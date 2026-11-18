#!/usr/bin/env python3
"""Read-only visual validation of ZAC gallery in production."""
import asyncio
from playwright.async_api import async_playwright

BASE = "https://zacseguros.com.br/"
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(BASE+"?gallery_qa=1", wait_until="networkidle", timeout=60000)
        await page.locator("#zac-photo-track").scroll_into_view_if_needed()
        await page.wait_for_timeout(2000)
        imgs = page.locator("#zac-photo-track .carousel-frame img")
        count = await imgs.count()
        print("Gallery images:",count)
        assert count == 11, f"Expected 11 photos, found {count}"
        for i in range(count):
            img=imgs.nth(i)
            await img.scroll_into_view_if_needed()
            await img.evaluate("(e)=>e.loading='eager'")
            await img.evaluate("(e)=>e.decode().catch(()=>{})")
            vals=await img.evaluate("""(e)=>{
                const css=getComputedStyle(e),f=getComputedStyle(e.closest('.carousel-frame'));
                const r=e.getBoundingClientRect(),b=e.closest('.carousel-frame').getBoundingClientRect();
                return {src:e.getAttribute('src'),naturalWidth:e.naturalWidth,naturalHeight:e.naturalHeight,
                    objectFit:css.objectFit,imgWidth:r.width,imgHeight:r.height,
                    frameWidth:b.width,frameHeight:b.height,frameAspect:f.aspectRatio};
            }""")
            print("Photo",i+1,vals)
            assert vals["naturalWidth"]>0, "Image did not load"
            assert f"zac-evento-{i+1:02}.jpg" in vals["src"]
            assert vals["objectFit"]=="cover", "Image CSS does not preserve proportion"
            assert abs(vals["imgWidth"]-vals["frameWidth"])<2
            assert abs(vals["imgHeight"]-vals["frameHeight"])<2
            assert 0.75 < vals["frameWidth"]/vals["frameHeight"] < 0.86
        await page.locator("#zac-photo-track").scroll_into_view_if_needed()
        await page.screenshot(path="/tmp/zac-gallery-qa.png",full_page=False)
        print("PASS: 11 gallery images proportionate on desktop")
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.reload(wait_until="networkidle")
        await page.locator("#zac-photo-track").scroll_into_view_if_needed()
        mobile=await page.locator("#zac-photo-track .carousel-frame img").first.evaluate(
            "(e)=>({fit:getComputedStyle(e).objectFit,ratio:e.closest('.carousel-frame').getBoundingClientRect().width/e.closest('.carousel-frame').getBoundingClientRect().height})"
        )
        print("Mobile:",mobile)
        assert mobile["fit"]=="cover" and 0.75<mobile["ratio"]<0.86
        print("PASS: mobile gallery proportions")
        await browser.close()
asyncio.run(main())

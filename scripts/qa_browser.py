#!/usr/bin/env python3
"""Browser-based smoke test of the independent Cloudflare preview."""
import asyncio
from playwright.async_api import async_playwright
BASE = "https://staging-static-site-preview-zacassessoria.carolschimitez491.workers.dev"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        problems=[]
        page.on("pageerror",lambda e: problems.append("JS ERROR: "+str(e)))
        await page.goto(BASE + "/?qa_browser=1",wait_until="networkidle",timeout=60000)
        await page.wait_for_timeout(3500)
        title=await page.title()
        headline=await page.locator("h1").first.inner_text()
        # Lazy-loaded carousel images need scrolling before naturalWidth is reliable.
        gallery = page.locator("#zac-photo-track figure.carousel-frame img")
        for i in range(await gallery.count()):
            await gallery.nth(i).scroll_into_view_if_needed(timeout=10000)
            await gallery.nth(i).evaluate("(img) => { img.loading = 'eager'; }")
        await page.wait_for_timeout(2500)
        photos=await page.locator("#zac-photo-track figure.carousel-frame img").evaluate_all("(imgs)=>imgs.map(i=>({src:i.getAttribute('src'),complete:i.complete,width:i.naturalWidth}))")
        gallery_count=len(photos)
        print("TITLE:",title)
        print("HERO:",headline)
        print("GALLERY COUNT:",gallery_count)
        print("GALLERY:",photos)
        print("PAGE ERRORS:",problems)
        await page.screenshot(path="/tmp/zac-independent-preview.png",full_page=True)
        if "O corretor no centro" not in headline:
            raise AssertionError("Original hero title missing")
        if gallery_count != 11:
            raise AssertionError(f"Expected exactly 11 gallery images, found {gallery_count}")
        for index,photo in enumerate(photos,1):
            expected=f"zac-evento-{index:02}.jpg"
            if expected not in photo["src"] or photo["width"]==0:
                raise AssertionError(f"Gallery photo {index} missing or broken: {photo}")
        unexpected=[p for p in problems if "Minified React error #418" not in p]
        if unexpected:
            raise AssertionError("JS runtime errors: "+repr(unexpected))
        print("HYDRATION WARNINGS:", len(problems)-len(unexpected))
        # Verify the React-powered contact form actually submits into the preview D1.
        form = page.locator("form.form").first
        await form.locator('input[name="name"]').fill("Teste Homologacao ZAC")
        await form.locator('input[name="phone"]').fill("51999990000")
        await form.locator('input[name="email"]').fill("zac-qa-browser@example.invalid")
        await form.locator('input[name="consent"]').check()
        await form.locator('button[type="submit"],button:has-text("Enviar solicitação")').first.click()
        await page.wait_for_timeout(2000)
        if "/obrigado" not in page.url:
            print("CONTACT FORM PAGE:",await page.locator("body").inner_text()[-600:])
            raise AssertionError("Contact form did not navigate to /obrigado after submission")
        print("CONTACT FORM SUCCESS:",page.url)
        await page.goto(BASE+"/privacidade",wait_until="networkidle",timeout=60000)
        if "Privacidade" not in await page.locator("body").inner_text():
            raise AssertionError("Privacy page missing")
        await browser.close()
        print("PASS: visual/runtime smoke test passed")

asyncio.run(main())

#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=await browser.new_page(viewport={"width":1440,"height":900})
        await page.goto("https://zacseguros.com.br/?zurich_qa=20261118",wait_until="networkidle",timeout=60000)
        await page.locator(".partner-zurich").scroll_into_view_if_needed()
        await page.wait_for_timeout(2200)
        data=await page.locator(".partner-zurich img").evaluate("""async e=>{
          await e.decode().catch(()=>{});
          const rect=e.getBoundingClientRect(),container=e.parentElement.getBoundingClientRect();
          return {src:e.currentSrc,attr:e.getAttribute('src'),width:e.naturalWidth,height:e.naturalHeight,
            rectWidth:rect.width,rectHeight:rect.height,containerWidth:container.width,
            objectFit:getComputedStyle(e).objectFit};
        }""")
        print("LIVE ZURICH:",data)
        assert "zurich-sem-seguros.jpg" in data["src"],"Old logo is still being rendered"
        assert data["width"]==729 and data["height"]==174,"Wrong cropped image size"
        assert data["rectWidth"]<=data["containerWidth"]+1,"Logo exceeds original container width"
        await page.locator(".partner-zurich").screenshot(path="/tmp/zurich-logo-desktop.png")
        await page.set_viewport_size({"width":390,"height":844})
        await page.reload(wait_until="networkidle")
        await page.locator(".partner-zurich").scroll_into_view_if_needed()
        mobile=await page.locator(".partner-zurich img").evaluate("e=>({width:e.getBoundingClientRect().width,container:e.parentElement.getBoundingClientRect().width,src:e.currentSrc})")
        print("MOBILE ZURICH:",mobile)
        assert mobile["width"]<=mobile["container"]+1
        assert "zurich-sem-seguros.jpg" in mobile["src"]
        await browser.close()
        print("PASS: logo sem Seguros, no tamanho correto, desktop e mobile")
asyncio.run(main())

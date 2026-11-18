#!/usr/bin/env python3
import asyncio
from urllib.parse import unquote, urlparse, parse_qs
from playwright.async_api import async_playwright
BASE = "https://zacseguros.com.br"
async def main():
  async with async_playwright() as p:
    browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
    for width,height in [(1440,900),(390,844)]:
      page=await browser.new_page(viewport={"width":width,"height":height})
      await page.goto(BASE+"/?zac_whatsapp_qa="+str(width),wait_until="networkidle",timeout=60000)
      target=page.locator("#zac-whatsapp-site")
      assert await target.count()==1,"WhatsApp button missing"
      href=await target.get_attribute("href")
      url=urlparse(href)
      print(width,"WhatsApp",href)
      assert url.netloc=="wa.me" and url.path=="/555493424494"
      assert parse_qs(url.query).get("text")==["vim pelo site e gostaria de mais informações."]
      bounds=await target.bounding_box()
      print(width,"Button box",bounds)
      assert bounds is not None and bounds["x"]>=0 and bounds["x"]+bounds["width"]<=width+1
      assert bounds["y"]>=0 and bounds["y"]+bounds["height"]<=height+1
      await page.screenshot(path=f"/tmp/zac-whatsapp-{width}.png")
      # Sending is not tested on production; only invalid user data on the endpoint.
      resp=await page.request.post(BASE+"/api/leads",data={"name":"x"},headers={"Content-Type":"application/json"})
      assert resp.status==400
      await page.close()
    print("PASS: WhatsApp link and form validation available on desktop and mobile")
    await browser.close()
asyncio.run(main())

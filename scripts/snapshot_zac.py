#!/usr/bin/env python3
"""Archive the public, approved ZAC site into Cloudflare static assets.

Run only on staging. Never download private admin content or submit forms.
"""
import os
import re
import shutil
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import requests
from bs4 import BeautifulSoup

ORIGIN = "https://zac-assessoria.carolschimitez491.chatgpt.site"
HOST = urlsplit(ORIGIN).netloc
ROOT = Path("site")
PAGES = ["/", "/privacidade", "/termos", "/cookies", "/acessibilidade"]
PHOTOS = Path("galeria/eventos")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ZAC-migration/1.0)"})
ROOT.mkdir(exist_ok=True)
asset_queue = deque()
seen_assets = set()
failures = []

def local_path(value):
    u = urlsplit(urljoin(ORIGIN + "/", value))
    if u.netloc != HOST or u.scheme != "https":
        return None
    path = unquote(u.path)
    if ".." in Path(path).parts or "\x00" in path:
        return None
    return path

def queue_asset(value):
    if not value or value.startswith(("data:", "blob:", "javascript:", "#")):
        return
    path = local_path(value)
    if not path or path == "/" or path.startswith(("/admin", "/api/")):
        return
    if re.match(r"^/images/galeria/zac-registro-", path):
        return
    if path not in seen_assets:
        seen_assets.add(path)
        asset_queue.append(path)

def get(path):
    resp = SESSION.get(ORIGIN + path, timeout=45)
    resp.raise_for_status()
    return resp

def extract_urls(css):
    return re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css, flags=re.I)

def fix_gallery(soup):
    track = soup.select_one("#zac-photo-track")
    if track is None:
        raise RuntimeError("Approved site's #zac-photo-track is missing")
    first = track.select_one("figure.carousel-frame")
    if first is None:
        raise RuntimeError("Approved carousel figure template is missing")
    template = BeautifulSoup(str(first), "html.parser").select_one("figure")
    track.clear()
    for i in range(1, 12):
        name = f"zac-evento-{i:02}.jpg"
        fig = BeautifulSoup(str(template), "html.parser").select_one("figure")
        img = fig.select_one("img")
        if img is None:
            raise RuntimeError("Approved carousel figure has no image")
        img["src"] = "/images/galeria/eventos/" + name
        img["alt"] = f"Registro da ZAC em eventos e encontros — foto {i}"
        img.pop("srcset", None)
        img.pop("data-src", None)
        track.append(fig)
    assert len(track.select("figure.carousel-frame")) == 11

for page in PAGES:
    try:
        response = get(page)
    except Exception as ex:
        raise RuntimeError(f"Failed to archive essential page {page}: {ex}")
    soup = BeautifulSoup(response.text, "html.parser")
    if page == "/":
        fix_gallery(soup)
    for tag in soup.find_all(True):
        for key in ("src", "href", "poster", "data-src", "data-background"):
            value = tag.get(key)
            if not value:
                continue
            if isinstance(value, str) and value.startswith(ORIGIN):
                tag[key] = value.replace(ORIGIN, "", 1) or "/"
                value = tag[key]
            if key in ("src", "poster", "data-src", "data-background") or (
                key == "href" and tag.name == "link"
            ):
                queue_asset(value)
        for key in ("srcset", "data-srcset"):
            for chunk in (tag.get(key) or "").split(","):
                queue_asset(chunk.strip().split(" ")[0])
        if tag.name == "style":
            for u in extract_urls(tag.get_text()):
                queue_asset(u)
    for path in re.findall(r"(?<!\w)/(?:images|assets|static|fonts)/[\w.%/+@-]+", str(soup)):
        queue_asset(path)
    # Replace any remaining absolute references to the old ChatGPT hostname.
    text = str(soup).replace(ORIGIN, "")
    output = ROOT / ("index.html" if page == "/" else page.lstrip("/") + "/index.html")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"PAGE {page} -> {output} ({len(text)} chars)")

for name in ("favicon.svg", "robots.txt", "sitemap.xml"):
    queue_asset("/" + name)

while asset_queue:
    path = asset_queue.popleft()
    dest = ROOT / path.lstrip("/")
    if dest.is_file():
        continue
    try:
        resp = get(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        if path.endswith(".css"):
            for u in extract_urls(resp.text):
                queue_asset(urljoin(ORIGIN + path, u))
        print(f"ASSET {path} ({len(resp.content)} bytes)")
    except Exception as ex:
        failures.append((path, str(ex)))
        print(f"WARN {path}: {ex}")

for i in range(1, 12):
    name = f"zac-evento-{i:02}.jpg"
    source = PHOTOS / name
    if not source.exists():
        raise RuntimeError(f"Missing user-provided photo: {source}")
    target = ROOT / "images/galeria/eventos" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)

if failures:
    print("Some optional URLs were unavailable:", failures)
    essential = [p for p,_ in failures if not p.startswith("/images/galeria/zac-registro-")]
    if essential:
        raise RuntimeError("Required static resources not archived: " + repr(essential))

html = (ROOT / "index.html").read_text()
assert "zac-evento-11.jpg" in html
assert "zac-assessoria.carolschimitez491.chatgpt.site" not in html
print("SUCCESS: independent static snapshot ready.")

#!/usr/bin/env python3
"""Remove only lower 'Seguros' subline from existing approved Zurich logo.

Preserves the original trademark, icon and lettering, crops away the subline,
and updates references on the independent Cloudflare-hosted site.
"""
from pathlib import Path
from PIL import Image
import re

old=Path("site/images/parceiras/zurich.jpeg")
new=Path("site/images/parceiras/zurich-sem-seguros.jpg")
image=Image.open(old).convert("RGB")
w,h=image.size
if (w,h)!=(780,381):
    raise RuntimeError(f"Unexpected original Zurich logo dimensions: {w}x{h}")
# Original icon and ZURICH lettering occupy image rows 91-245.
# The 'Seguros' subtitle starts at row 254; exclude it entirely.
upper_limit=249
points=[]
for y in range(upper_limit):
    for x in range(w):
        r,g,b=image.getpixel((x,y))
        if b>r*1.2 and b>g*1.12 and r<165 and g<180:
            points.append((x,y))
if not points:
    raise RuntimeError("Could not detect original navy logo pixels")
minx=min(x for x,y in points);maxx=max(x for x,y in points)
miny=min(y for x,y in points);maxy=max(y for x,y in points)
if not (80<=miny<=120 and 220<=maxy<=249):
    raise RuntimeError(f"Unexpected logo bounding box: {minx,miny,maxx,maxy}")
bbox=(max(0,minx-24),max(0,miny-16),min(w,maxx+25),min(upper_limit,maxy+9))
cropped=image.crop(bbox)
cropped.save(new,format="JPEG",quality=97,subsampling=0,optimize=True)
print("Zurich logo original:",(w,h),"top glyph bbox:",(minx,miny,maxx,maxy))
print("New Zurich logo asset:",new,"dimensions:",cropped.size)

# Update the server HTML and hydrated React script to point at the exact same new asset.
needle="/images/parceiras/zurich.jpeg"
replacement="/images/parceiras/zurich-sem-seguros.jpg"
count=0
for path in [Path("site/index.html"), *Path("site/_next/static/chunks").glob("*.js")]:
    text=path.read_text(encoding="utf-8")
    if needle not in text:
        continue
    occurrences=text.count(needle)
    text=text.replace(needle,replacement)
    if path.name=="index.html":
        # Keep intrinsic image dimensions in HTML consistent with the new crop.
        html_old='height="381" loading="lazy" src="'+replacement+'" width="780"'
        html_new='height="'+str(cropped.height)+'" loading="lazy" src="'+replacement+'" width="'+str(cropped.width)+'"'
        new_n=text.count(html_old)
        text=text.replace(html_old,html_new)
        print("Updated intrinsic image dimensions:",new_n)
    path.write_text(text,encoding="utf-8")
    count+=occurrences
    print("Updated",path,occurrences)
if count<2:
    raise RuntimeError(f"Expected both HTML and React bundle image refs; updated {count} occurrences")
assert needle not in Path("site/index.html").read_text()
print("SUCCESS: Zurich logo no longer includes Seguros subtitle")

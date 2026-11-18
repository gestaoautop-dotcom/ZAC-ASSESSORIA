from PIL import Image
from pathlib import Path

path=Path("site/images/parceiras/zurich.jpeg")
img=Image.open(path).convert("RGB")
print("ZURICH_IMAGE_SIZE", img.size)
w,h=img.size
for y in range(h):
    pixels=[img.getpixel((x,y)) for x in range(w)]
    hits=sum(1 for r,g,b in pixels if b>r*1.2 and b>g*1.12 and r<165 and g<180)
    if hits>2:
        print("ROW",y,"BLUE_PIXELS",hits)

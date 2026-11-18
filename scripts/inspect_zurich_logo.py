from PIL import Image
im = Image.open("site/images/parceiras/zurich.jpeg").convert("RGB")
print("ORIGINAL_IMAGE", im.size)
w,h=im.size
for y in range(0,h,4):
    count=0
    xs=[]
    for x in range(int(w*.37),int(w*.91)):
        r,g,b=im.getpixel((x,y))
        if r<140 and g<155 and b<190 and b>r*.8:
            count+=1
            xs.append(x)
    if count>=2:
        print("ROW",y,"COUNT",count,"XSPAN",min(xs),max(xs))

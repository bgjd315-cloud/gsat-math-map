import sys
from PIL import Image
names = sys.argv[2:]; out = sys.argv[1]
ims = [Image.open("img/" + n).convert("L") for n in names]
W = 600
ims = [im.resize((W, int(im.height * W / im.width))) for im in ims]
H = sum(im.height + 12 for im in ims)
sheet = Image.new("L", (W, H), 120)
y = 0
for im in ims:
    sheet.paste(im, (0, y)); y += im.height + 12
sheet.save(out)

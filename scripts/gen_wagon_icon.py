#!/usr/bin/env python3
"""Wagon bot icon v7 — final: simplified for 50x50 readability."""
from PIL import Image, ImageDraw, ImageFilter
import math as m, os

SIZE = 512
OUTPUT = "/Users/boris_ai/.hermes/profiles/boris/data/wagon_bot_icon.png"

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

NAVY   = (10, 27, 61)
STEEL  = (42, 90, 150)     # lighter for contrast against dark TG bg
DARK_INNER = (22, 58, 108)
CYAN   = (0, 205, 255)
WHITE  = (235, 247, 255)
SILVER = (145, 178, 185)
GLOW   = (0, 150, 210)

def a(c, alpha=255):
    return c + (alpha,)

# BG
draw.rectangle([0, 0, SIZE, SIZE], fill=a(NAVY))
for y in range(SIZE):
    for x in range(SIZE):
        d = m.sqrt((x-256)**2+(y-256)**2)/256
        if d > 0.95: continue
        r = int(NAVY[0]+(1-d)*8)
        g = int(NAVY[1]+(1-d)*6)
        b = int(NAVY[2]+(1-d)*8)
        if r!=NAVY[0]: draw.point((x,y), fill=(r,g,b,255))

# Glow
gl = Image.new("RGBA",(SIZE,SIZE),(0,0,0,0))
gd = ImageDraw.Draw(gl)
for r in range(150,20,-4):
    gd.ellipse([256-r,266-r,256+r,266+r], fill=(0,190,250,max(0,22-(150-r)//5)))
gl = gl.filter(ImageFilter.GaussianBlur(18))
img = Image.alpha_composite(img, gl)
draw = ImageDraw.Draw(img)

# Wagon
cx, cy = 256, 266
w, h = 300, 150
bt, bb = cy-h//2, cy+h//2
bl, br = cx-w//2, cx+w//2

draw.polygon([(bl+6,bt+6),(br-6,bt+6),(br,bb+6),(bl,bb+6)], fill=a((16,36,72)))
draw.polygon([(bl+10,bt),(br-10,bt),(br,bb),(bl,bb)], fill=a(STEEL))

im = 30
draw.polygon([(bl+10+im,bt+15),(br-10-im,bt+15),
              (br-im+4,bb-12),(bl+im-4,bb-12)], fill=a(DARK_INNER))

# ── 4 THICK bars (not 5) ──
ct, cb = bt+30, bb-30
cl, cr = bl+65, br-65
ch = cb - ct
n = 4
gap = 22
bw = (cr-cl-(n-1)*gap)//n
tw = n*bw+(n-1)*gap
bx0 = cl+(cr-cl-tw)//2

heights = [0.45, 0.80, 0.95, 0.65]
for i in range(n):
    bx = bx0 + i*(bw+gap)
    bh = int(ch*heights[i])
    by = cb - bh
    for dy in range(bh):
        t = dy/max(bh,1)
        draw.rectangle([bx,by+dy,bx+bw,by+dy+1],
                       fill=(int(25*t),int(185+35*t),int(245+10*t),min(255,180+int(75*t))))
    draw.rectangle([bx,by,bx+bw,cb], outline=a(CYAN,130), width=2)
    for dh in range(8):
        draw.rectangle([bx,by+dh,bx+bw,by+dh+1], fill=(170,248,255,230-dh*22))

# ── Wheels — larger, connected (no separate track) ──
wr = 30
wy = bb + wr - 2
pcts = [0.15, 0.38, 0.62, 0.85]
bw_body = br-bl
wheels = [(bl+int(p*bw_body), wy) for p in pcts]
for wx, wy_ in wheels:
    draw.ellipse([wx-wr,wy_-wr,wx+wr,wy_+wr], fill=a((28,38,58)))
    draw.ellipse([wx-wr,wy_-wr,wx+wr,wy_+wr], outline=a(SILVER), width=3)
    draw.ellipse([wx-8,wy_-8,wx+8,wy_+8], fill=a(WHITE))
    draw.line([wx,wy_-wr+4,wx,bb], fill=a((70,122,175)), width=3)

# ── Simple rail (no sleepers) ──
ry = wy + wr + 6
draw.line([bl-45, ry, br+45, ry], fill=a(SILVER, 180), width=4)

# ── Circuit nodes (just 2, cleaner) ──
ty = bb - 6
draw.line([bl+40, ty, br-40, ty], fill=a(SILVER, 90), width=2)
for nx in [cx-45, cx+45]:
    draw.ellipse([nx-8,ty-8,nx+8,ty+8], fill=a(GLOW,170))
    draw.ellipse([nx-4,ty-4,nx+4,ty+4], fill=a(CYAN))

# Save
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
img.save(OUTPUT,"PNG")
small = img.resize((50,50), Image.LANCZOS)
small.save(OUTPUT.replace(".png","_50x50.png"))
print(f"✓ Done: {OUTPUT}")

#!/usr/bin/env python3
"""Glampling map — Arial font, accurate labels, clean design."""
from PIL import Image, ImageDraw, ImageFont
import math, os

W, H = 1400, 934
OUT = "/Users/boris_ai/.hermes/profiles/boris/data/glamping_map.png"

img = Image.new("RGBA", (W, H), (0,0,0,0))
draw = ImageDraw.Draw(img)
BG = (22, 22, 46)
draw.rectangle([0, 0, W, H], fill=BG)

# Fonts
FONT_BIG = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 46)
FONT_MD  = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
FONT_SM  = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)

GOLD = (240, 165, 0)
WHITE = (230, 235, 245)
DIM_WHITE = (150, 155, 175)

# Russia outline (detailed polygon)
outline = [
    (0.03,0.22),(0.04,0.17),(0.05,0.13),(0.07,0.10),(0.09,0.07),
    (0.12,0.05),(0.16,0.03),(0.20,0.05),(0.24,0.08),(0.28,0.11),
    (0.32,0.14),(0.36,0.17),(0.40,0.20),(0.44,0.18),(0.48,0.15),
    (0.52,0.13),(0.56,0.12),(0.60,0.13),(0.64,0.16),(0.68,0.20),
    (0.72,0.24),(0.76,0.28),(0.80,0.33),(0.84,0.38),(0.87,0.42),
    (0.89,0.46),(0.88,0.50),(0.86,0.54),(0.82,0.56),(0.78,0.54),
    (0.74,0.52),(0.70,0.54),(0.66,0.58),(0.62,0.62),(0.58,0.66),
    (0.54,0.70),(0.50,0.74),(0.46,0.76),(0.42,0.74),(0.38,0.70),
    (0.34,0.66),(0.30,0.62),(0.26,0.58),(0.22,0.56),(0.18,0.54),
    (0.14,0.50),(0.11,0.46),(0.09,0.42),(0.07,0.37),(0.05,0.32),(0.03,0.26)
]
pts = [(int(x*W), int(y*H)) for x,y in outline]
draw.polygon(pts, fill=(32, 32, 60), outline=(55, 55, 90))

# Subtle grid
for gx in range(0, W, 60):
    for gy in range(0, H, 60):
        draw.point((gx, gy), fill=(38, 38, 60))

# Locations
locs = [
    ("Калининград",      0.05, 0.33,  True),
    ("Санкт-Петербург",  0.13, 0.22,  True),
    ("Карелия",          0.19, 0.14,  True),
    ("Москва",           0.14, 0.37,  True),
    ("Казань",           0.24, 0.41,  True),
    ("Сочи",             0.10, 0.59,  True),
    ("Крым",             0.07, 0.63,  True),
    ("Алтай",            0.52, 0.66,  True),
    ("Байкал",           0.64, 0.60,  True),
    ("Камчатка",         0.86, 0.37,  True),
]

markers = []
for name, px, py, _ in locs:
    x, y = int(px*W), int(py*H)
    markers.append((x, y))
    # Glow rings
    for r in [10, 6, 3]:
        alpha = 50 if r==10 else 90 if r==6 else 220
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(240,165,0,alpha))
    # Dot
    draw.ellipse([x-3, y-3, x+3, y+3], fill=GOLD)
    # Label
    offset = 16 if px < 0.5 else -16
    anchor = "lt" if px < 0.5 else "rt"
    draw.text((x+offset, y-10), name, fill=WHITE, font=FONT_SM)

# Routes
def dash_line(p1, p2):
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    length = math.sqrt(dx*dx+dy*dy)
    segs = max(2, int(length/8))
    for s in range(0, segs, 2):
        t1, t2 = s/segs, min((s+1)/segs, 1.0)
        draw.line([(p1[0]+dx*t1, p1[1]+dy*t1), (p1[0]+dx*t2, p1[1]+dy*t2)],
                  fill=(255,255,255,80), width=1)

routes = [(0,1),(1,3),(3,4),(4,7),(7,8),(8,9),(5,6)]
for a, b in routes:
    dash_line(markers[a], markers[b])

# Title
title = "ГЛЭМПИНГИ РОССИИ"
bbox = draw.textbbox((0,0), title, font=FONT_BIG)
tw = bbox[2]-bbox[0]
draw.text(((W-tw)//2, 30), title, fill=GOLD, font=FONT_BIG)

sub = "примерная схема размещения"
bbox2 = draw.textbbox((0,0), sub, font=FONT_SM)
sw = bbox2[2]-bbox2[0]
draw.text(((W-sw)//2, 82), sub, fill=DIM_WHITE, font=FONT_SM)

# Footer
draw.text((W-200, H-30), "@ boris_ai / 2026", fill=(80,80,100), font=FONT_SM)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG")
print(f"Done: {OUT} ({os.path.getsize(OUT)} bytes)")

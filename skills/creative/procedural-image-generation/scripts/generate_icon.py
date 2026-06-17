#!/usr/bin/env python3
"""Procedural icon generation template — Pillow + iterative vision refinement.

Copy this file, replace the drawing logic, and run.

Key constraints (from the telegram-avatar-guidelines reference):
  - Outputs BOTH 512x512 and 50x50 versions
  - Dark background, light foreground, high contrast
  - At most 2-3 large visual elements
  - Lines ≥ 3px wide (prefer 5-6px for structural lines)
  - No text — unreadable at 50x50
  - Center 80% = safe zone (Telegram crops to circle)

Usage:
  python3 generate_icon.py

Then validate:
  vision_analyze(image_url="output_50x50.png", question="...")
"""

from PIL import Image, ImageDraw
import math
import os

# ── Configuration ─────────────────────────────────────
SIZE = 512
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_512 = os.path.join(OUTPUT_DIR, "icon_512.png")
OUTPUT_50 = os.path.join(OUTPUT_DIR, "icon_50.png")

# Colors (edit to match your design)
BG_COLOR = (14, 22, 52, 255)        # Deep navy
FG_PRIMARY = (228, 236, 248, 255)   # Light blue-white
FG_SECONDARY = (70, 175, 240, 255)  # Medium blue (bars, accents)
FG_ACCENT = (255, 145, 0, 255)      # Orange/gold (sparingly)

# ── Canvas ────────────────────────────────────────────
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.rectangle([0, 0, SIZE, SIZE], fill=BG_COLOR)

# ── Safe zone reference (center 80% of radius) ────────
# For a 512x512 square, the inscribed circle radius = 256.
# 80% safe zone radius = 205px from center.
# Elements within (cx±205, cy±205) are guaranteed visible.
CX, CY = SIZE // 2, SIZE // 2
SAFE_R = int(SIZE * 0.4)  # 205

# ── DRAWING LOGIC — REPLACE THIS ──────────────────────
# Example: a simple centered rectangle + circle
# Replace with your actual icon design below.

rect_w, rect_h = 200, 100
draw.rectangle(
    [CX - rect_w // 2, CY - rect_h // 2, CX + rect_w // 2, CY + rect_h // 2],
    fill=FG_PRIMARY,
    outline=(190, 205, 230, 255),
)

circle_r = 30
draw.ellipse(
    [CX - circle_r, CY - 80, CX + circle_r, CY - 20],
    fill=FG_SECONDARY,
)

# ── END DRAWING LOGIC ─────────────────────────────────

# ── Output ────────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)
img.save(OUTPUT_512, "PNG")
print(f"✓ 512×512: {OUTPUT_512} ({os.path.getsize(OUTPUT_512)} bytes)")

small = img.resize((50, 50), Image.LANCZOS)
small.save(OUTPUT_50, "PNG")
print(f"✓ 50×50:   {OUTPUT_50} ({os.path.getsize(OUTPUT_50)} bytes)")
print()
print("Next: vision_analyze(image_url=OUTPUT_50, question='At 50x50px, is this clean and recognizable?')")

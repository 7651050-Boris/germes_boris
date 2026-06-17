#!/usr/bin/env python3
"""Convert markdown screenplay synopsis to PDF with Courier New 14pt.
Usage: python3 gen_pdf_courier.py <input.md> [output.pdf]

Requires: pip install fpdf2
Font: Courier New (must be installed on system)
"""
from fpdf import FPDF
import re, sys, os

INPUT = sys.argv[1] if len(sys.argv) > 1 else None
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else INPUT.replace('.md', '.pdf') if INPUT else None

if not INPUT or not os.path.exists(INPUT):
    print("Usage: python3 gen_pdf_courier.py <input.md> [output.pdf]")
    sys.exit(1)

FONT = "/System/Library/Fonts/Supplemental/Courier New.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
FONT_ITALIC = "/System/Library/Fonts/Supplemental/Courier New Italic.ttf"

with open(INPUT) as f:
    text = f.read()

lines = text.split('\n')

pdf = FPDF()
# Use "CN" (not "Courier") to avoid conflict with built-in Latin-1 Courier
pdf.add_font("CN", "", FONT)
pdf.add_font("CN", "B", FONT_BOLD)
pdf.add_font("CN", "I", FONT_ITALIC)
pdf.set_auto_page_break(auto=True, margin=25)
pdf.add_page()

MARGIN = 25
WIDTH = 210 - 2 * MARGIN
pdf.set_left_margin(MARGIN)
pdf.set_right_margin(MARGIN)

FS = 14
LH = FS * 0.45

for line in lines:
    line = line.strip()
    if not line:
        pdf.ln(LH * 1.2)
        continue

    if line.startswith("# ") and not line.startswith("## "):
        pdf.set_font("CN", "B", FS + 4)
        pdf.ln(LH)
        pdf.cell(WIDTH, LH * 1.4, line[2:].strip(), new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(LH)
        continue

    if line == "---":
        pdf.ln(LH * 0.8)
        y = pdf.get_y()
        pdf.set_draw_color(80)
        pdf.line(MARGIN, y, MARGIN + WIDTH, y)
        pdf.ln(LH * 0.8)
        continue

    pdf.set_font("CN", "", FS)
    parts = re.split(r'(\*\*.*?\*\*)', line)
    if len(parts) == 1:
        pdf.multi_cell(WIDTH, LH, line)
    else:
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                pdf.set_font("CN", "B", FS)
                pdf.write(LH, part[2:-2])
                pdf.set_font("CN", "", FS)
            else:
                pdf.write(LH, part)
        pdf.ln(LH)

pdf.output(OUTPUT)
print(f"Done: {OUTPUT} ({os.path.getsize(OUTPUT)} bytes)")

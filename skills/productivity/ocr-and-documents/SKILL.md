---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Image OCR with EasyOCR (screenshots, photos)

For **standalone images** (screenshots, photos, scanned JPG/PNG — not PDFs), use `easyocr`.

```bash
pip install easyocr
```

Supports 80+ languages including Russian and English. Works on CPU (slower) or GPU. No brew/tesseract needed — pure Python.

```python
import easyocr

reader = easyocr.Reader(['ru', 'en'], gpu=False)  # gpu=True if CUDA/Apple MPS available
result = reader.readtext('/path/to/image.jpg', detail=0)           # text only
result = reader.readtext('/path/to/image.jpg', paragraph=True)     # grouped paragraphs
for bbox, text, confidence in reader.readtext('/path/to/image.jpg'):
    print(f"{confidence:.2f}: {text}")
```

**Pitfalls:**
- **First run downloads models** (~100MB detection model + ~100MB recognition model) — takes a few minutes
- **CPU only is slow** — ~10-30s per image on Apple M-series. The `Using CPU` warning is harmless
- **Small text** (e.g., Telegram UI elements) may be missed. Resize image or crop before passing
- **Torch pin_memory warning on MPS** — harmless, can be ignored: `UserWarning: 'pin_memory' argument is set as true but not supported on MPS now`
- **Output can be enormous** from progress bars + torch warnings — pipe output through `grep -v -E '^(Progress|Using CPU|UserWarning|WARNING)'` or use `paragraph=True + detail=0` to reduce noise. Better yet: crop the image to just the text region first with Pillow, then OCR just that crop — smaller input = faster processing + less noise.
- **Use `detail=0`** when you only need text strings (faster, less output)
- **Combine with `paragraph=True`** for coherent multi-line reading — groups related text lines together instead of returning isolated fragments
- **Handwriting not well supported** — use for typed/printed text only
- **Cyrillic/Latin homoglyphs are the #1 credential trap** — EasyOCR (and any OCR engine) can confuse visually identical Cyrillic and Latin characters: `а` vs `a`, `е` vs `e`, `о` vs `o`, `с` vs `c`, `р` vs `p`, `к` vs `k`, `х` vs `x`, `і` vs `i`. This is CRITICAL when reading credentials, API keys, or secrets from screenshots. A common failure: OCR reads `fdd686383а29fe8c` (Cyrillic `а` at position 10) but the real value is `fdd686383a29fe8c` (Latin `a`). The strings look identical at a glance but the API silently rejects them with `invalid_client`. **Rule: never trust OCR output for credentials.** Always ask the user to copy-paste critical strings from the source directly. If OCR is the only option (e.g., user on phone sending screenshots), ask them to re-type each character group-by-group or read it out loud over voice.

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)

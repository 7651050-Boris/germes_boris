---
name: pdf-knowledge-synthesis
title: PDF Knowledge Base → Skill Synthesis
description: Batch-extract text from multiple PDF documents, analyze/classify the content, and synthesize a structured skill (SKILL.md) with organized knowledge sections. For ingesting domain-specific materials (nutrition protocols, training plans, research collections) into reusable agent skills.
category: productivity
version: 1.0.0
icon: 📚
author: Hermes Agent
created: 2026-06-15
---

# Skill: PDF Knowledge Base → Skill Synthesis

Transform a batch of PDF documents (scanned slides, text PDFs, mixed) into a structured, reusable SKILL.md agent skill.

## Workflow

### Step 1: Locate source PDFs
All incoming user documents land in the profile's cache directory:
```
~/.hermes/profiles/<profile>/cache/documents/
```

List them with:
```bash
ls -la ~/.hermes/profiles/<profile>/cache/documents/ | grep -i pdf
```

Sort by filename to get a clean ordering — the filenames encode the topic.

### Step 2: Install extraction tool (if missing)

First check:
```bash
python3 -c "import pymupdf; print('ok')" 2>/dev/null && echo "ready"
```

If not installed:
```bash
# Try uv first (Hermes default venv)
uv pip install pymupdf --quiet

# Or system pip3 (macOS, may need --break-system-packages on PEP 668 systems)
pip3 install pymupdf --break-system-packages 2>/dev/null || pip3 install pymupdf
```

**Important:** The import is `pymupdf` (not `fitz` as in older versions). On some systems, `import fitz` still works as an alias.

### Step 3: Bulk-extract metadata & text
Use `terminal` with a Python script to scan every PDF:

```python
import pymupdf, os, json

base = '/path/to/cache/documents'
files = sorted([f for f in os.listdir(base) if f.endswith('.pdf')])

results = {}
for f in files:
    path = os.path.join(base, f)
    doc = pymupdf.open(path)
    name = f.split('_', 2)[-1].replace('.pdf','') if '_' in f else f.replace('.pdf','')
    total_text = ''
    total_imgs = 0
    for page in doc:
        total_text += page.get_text()
        total_imgs += len(page.get_images())
    results[name] = {
        'pages': len(doc),
        'images': total_imgs,
        'text_len': len(total_text),
        'text': total_text[:2000] if total_text.strip() else ''
    }
    print(f'{name}: {len(doc)}p, {total_imgs}img, {len(total_text)}txt')
```

This tells you which PDFs have real text vs image-only. Most presentation PDFs (slides) will have usable text even with many images.

### Step 4: Deep-read key content
For the most text-rich files, dump the full content with a 3000-char preview:

```python
for fname in key_files:
    path = os.path.join(base, fname)
    doc = pymupdf.open(path)
    all_text = ''
    for page in doc:
        all_text += page.get_text()
    print(all_text[:3000])
    if len(all_text) > 3000:
        print(f'... [{len(all_text)-3000} more chars]')
```

### Step 5: Analyze and structure

Identify the domain logic from the text. For a nutrition protocol, look for:
- **Core principles**: rules, constraints, timing
- **Meal structure**: what to eat when, portion sizes
- **Macronutrient breakdowns**: protein types, carb classifications, fat types
- **Food lists**: allowed/restricted (by category: protein, veggies, fruit, grains)
- **Scientific explanations**: why certain foods work a certain way, hormonal mechanisms
- **Activity recommendations**: exercise, steps, sauna, sleep
- **Quantitative formulas**: water = 30ml/kg, protein = 0.83g/kg, etc.

Build a structured SKILL.md around these sections.

### Step 6: Create the skill

```bash
# Use skill_manage(action='create') with category and full SKILL.md content
```

**SKILL.md structure template:**

```markdown
---
name: <kebab-case>
title: <Human-readable title>
description: <One-paragraph summary of knowledge domain>
category: <category>
version: 1.0.0
icon: <emoji>
---

# Skill: <Title>

<1-2 sentence context about the source/system>

## 1. Core Principles
## 2. Main Protocol / Schemas
## 3. Nutrients / Components
## 4. Food Lists (by category)
## 5. Activity / Lifestyle
## 6. FAQ / Edge Cases
```

### Step 7: Add reference files (optional)
For very large reference documents (like recipe collections with 80+ pages), use:
```bash
skill_manage(action='write_file', name='<skill>', file_path='references/<name>.md', file_content='...')
```

Then add a one-line pointer in SKILL.md:
```markdown
> Full recipe collection: `references/recipes.md`
```

## Pitfalls
- **Image-only PDFs**: Some files may be scanned images with 0 text. Check `total_text.strip()` — if empty, use OCR tool (marker-pdf) separately. For most presentation/slide PDFs text is embedded in images metadata — `page.get_text()` still extracts it.
- **venv vs system Python**: `uv pip install pymupdf` installs into the Hermes virtualenv, which is used by `execute_code()`. `pip3 install pymupdf` installs system-wide, which is used by bare `terminal('python3 ...')` calls. If one doesn't see the module, try the other.
- **Truncation**: Keep previews under 3000 chars per file in analysis phase; `terminal()` output cap is ~50KB.
- **File naming**: Documents arrive with hashed prefixes (`doc_<hash>_<name>.pdf`). Extract the readable name via `f.split('_', 2)[-1]`.
- **Large PDFs**: For 80+ page PDFs, read only the intro/first 5-10 pages in detail; the rest is usually recipe applications of the same principles.
- **Language**: If documents are in Russian, keep all section headers and explanations in Russian in the final skill.

## Verification
- Load the created skill: `skill_view(name='<skill>')`
- Test with a domain question: the skill content should let you answer accurately without re-reading PDFs

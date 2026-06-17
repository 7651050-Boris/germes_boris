---
name: procedural-image-generation
description: "Generate icons, logos, and simple graphics programmatically with Pillow — the lightweight fallback when ComfyUI is unavailable or overkill. Iterative refinement with vision analysis."
version: 1.0.0
author: agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    category: creative
    tags: [icon, logo, pillow, png, telegram, avatar, design, iterative]
    related_skills: [comfyui]
---

# Procedural Image Generation

Generate icons, logos, avatars, and simple graphics programmatically with
Pillow when ComfyUI is not set up, overkill for the task, or the hardware
verdict is `marginal`/`cloud`.

## When to Use

- User asks for a Telegram bot icon/avatar, app icon, or simple logo
- ComfyUI hardware check returns `marginal` or `cloud`
- The image is geometric/symbolic (icons, charts, shapes) — NOT photorealistic
- You need precise control over layout, spacing, and alignment

When ComfyUI IS available and the task is photorealistic → use the `comfyui` skill instead.

## Quick Start

```bash
# Check Pillow availability
python3 -c "from PIL import Image; print('OK')"

# Copy the template and edit the drawing section
cp scripts/generate_icon.py my_icon.py
# ... edit "DRAWING LOGIC — REPLACE THIS" section ...
python3 my_icon.py
```

The template at `scripts/generate_icon.py` outputs both 512×512 and 50×50
versions, prints file paths, and reminds you to run `vision_analyze` next.

## Core Workflow

### Step 1: Understand the visual concept

Read the bot/app description. Identify 1-2 core visual metaphors (e.g.
"wagon + data bars"). Target: at most 2-3 large, high-contrast elements
visible at 50×50px.

### Step 2: Write a Pillow script

**CRITICAL: Do NOT use `execute_code`** — the sandbox lacks Pillow.
Instead: `write_file` → `terminal(command="python3 script.py")`.

Template approach:
- 512×512 RGBA canvas
- Solid background (no gradients needed for small icons)
- Draw shapes with `ImageDraw.Draw.polygon`, `.ellipse`, `.rectangle`, `.line`
- Use a limited color palette (2-3 main colors + background)
- Keep line widths ≥ 3px for visibility at small sizes

### Step 3: Generate + validate with vision

```python
# Always output BOTH sizes
img.save("icon_512.png")
img.resize((50, 50), Image.LANCZOS).save("icon_50.png")
```

Then:
```
vision_analyze(image_url="icon_50.png", question="At 50x50px, is this clean and recognizable?")
vision_analyze(image_url="icon_512.png", question="Rate this icon 1-10. Any issues?")
```

### Step 4: Iterate

Apply feedback from vision analysis. Common issues and fixes:

| Issue | Fix |
|-------|-----|
| "Too busy for 50×50" | Remove decorative elements, keep only 2-3 large shapes |
| "Elements look crowded" | Spread wider, use percentage-based positioning |
| "Track/line too thin" | Increase stroke width to ≥ 5px |
| "Not communicating theme X" | Add one clear symbol for that theme |
| "Rating below 7" | Address the specific issues, regenerate, re-evaluate |

**Stop condition:** vision model rates ≥ 7/10 and confirms readability at 50×50.

## Telegram Avatar Guidelines

See `references/telegram-avatar-guidelines.md` for platform-specific constraints.

Quick rules:
- Telegram crops to a **circle** — fill the full square, keep key elements in
  the center 80% radius
- Avatar displays at **50×50px** in chat list — test at this size
- Only 2-3 large, high-contrast elements survive at 50×50
- Dark backgrounds (navy, charcoal) perform well in Telegram's dark UI
- Light/bright foreground elements for contrast
- No text — unreadable at 50×50

## Pitfalls

1. **`execute_code` sandbox has no Pillow** — the sandbox strips user
   site-packages. Always use `write_file` + `terminal(command="python3 script.py")`.

2. **Designing for 512×512, forgetting 50×50** — every iteration MUST generate
   and vision-validate the 50×50 thumbnail. What looks good at 512 may be
   an unreadable blur at 50.

3. **Too many elements** — if the vision model says "busy" or "cluttered,"
   remove the smallest elements first. Five elements → three → two.

4. **Thin lines disappear** — any line thinner than 3px at 512×512 becomes
   invisible at 50×50. Minimum stroke width: 3px (prefer 5-6px for key
   structural lines).

5. **`pip install --user` needed on fresh macOS** — system Python 3.9 on
   macOS doesn't have Pillow by default. Install once:
   `python3 -m pip install --user Pillow`

## Verification Checklist

- [ ] Script produces both 512×512 and 50×50 outputs
- [ ] `vision_analyze` on 50×50 confirms readability
- [ ] `vision_analyze` on 512×512 rates ≥ 7/10
- [ ] No text in the icon (unreadable at small sizes)
- [ ] At most 3 major visual elements
- [ ] Key content fits within the center 80% (circular crop zone)

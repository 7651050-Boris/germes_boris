# Telegram Avatar Design Guidelines

Constraints discovered and validated during the wagon analytics bot icon
session, confirmed via iterative vision analysis.

## Platform Constraints

### Crop & Display

- Telegram **crops all profile pictures to a circle** (regardless of group
  vs. bot — same behavior everywhere).
- The circle touches the **midpoints of all four edges** of the square.
  Everything outside the inscribed circle is clipped.
- **Safe zone**: center ~80% of the radius. Keep all key content here.
- **Danger zone**: corners and edges — visible only if the element is
  large enough to extend into the safe zone.

### Sizes

| Context | Display size | Source |
|---------|-------------|--------|
| Chat list (main) | 50×50 px | 512×512 → downscaled |
| Chat header | ~36×36 px | Same source |
| Profile view | ~120×120 px | Same source |
| BotFather preview | ~100×100 px | Same source |

**The 50×50 chat-list view is the critical one.** If it fails at 50×50,
redesign. The 512×512 source is uploaded once to @BotFather; Telegram
handles all downscaling.

### Upload

1. Open @BotFather → `/mybots` → select bot
2. → `Edit Bot` → `Edit Botpic`
3. Upload the 512×512 PNG
4. Changes apply immediately (no restart needed)

## Design Principles for 50×50

### The Rule of Three

At 50×50px, the human eye can resolve:
- **2-3 large shapes** — clearly
- **4-5 shapes** — barely, if very distinct
- **6+ shapes** — impossible, becomes visual noise

Every element you add beyond three trades clarity for clutter.

### What Survives at 50×50

| Element | Survives? | Note |
|---------|-----------|------|
| Large filled polygon (wagon body) | ✅ Yes | Most legible element |
| Thick lines (≥5px at 512) | ✅ Yes | Tracks, borders, rails |
| 4-5 wide bars in a chart | ✅ Yes | If well-contrasted |
| Small dots (≤6px at 512) | ❌ No | Disappear or become noise |
| Thin lines (≤2px at 512) | ❌ No | Vanish completely |
| Text of any size | ❌ No | Unreadable, looks like artifacts |
| Magnifying glass icon | ❌ No | Too small to recognize |
| Gradient fills | ⚠️ Maybe | If contrast is high; often looks muddy |
| Eyes/faces on small objects | ❌ No | Creepy blobs, not expressive |

### Color Rules

- **Dark background, light foreground** — optimal for Telegram's dark UI
- **High contrast** — navy (#0E1634) + white (#E4ECF8) works excellently
- **Limited palette** — 2-3 main colors max
- **Avoid pastels** — they wash out against Telegram's dark theme
- **Orange/gold accents** — pop well but use sparingly (thin lines)

### Bad Ideas (learned the hard way)

| What was tried | Why it failed |
|---------------|---------------|
| Eyes on the wagon | "Childish" — undermines professional analytics feel |
| Chat bubble frame | Too busy, doesn't read at small sizes |
| 5+ decorative dots | "Unclear purpose" at 50×50 |
| Magnifying glass + bar chart + sparkle | Three competing "analytics" symbols |
| Thin track line (2px) | "Too thin compared to bold wagon" |
| Wheels crowded under center | "Not proportional to wagon width" |

### Good Ideas (that worked)

| What worked | Why |
|------------|-----|
| Bar chart AS wagon cargo | One unified visual, not two competing elements |
| 5 thick bars in cargo area | Readable at 50×50, clear analytics signal |
| Wheels at 15/35/65/85% of body width | Naturally proportional |
| Rail line at 6px width | Visible, grounds the icon |
| No text, no sparkles, no extras | Maximum clarity per pixel |
| 50×50 test thumbnail every iteration | Caught issues before final |

## Design Feedback Loop

The vision model (`vision_analyze`) is an effective icon critic when
prompted with specific questions:

```
Q: "At 50x50px, can you clearly see a railway wagon and data bars?"
Q: "Rate this icon 1-10 for professional quality."
Q: "What 2 changes would most improve this icon?"
```

Iterate until the model rates ≥ 7/10 AND confirms readability at 50×50.
This took 5 iterations for the wagon bot icon (v1→v5).

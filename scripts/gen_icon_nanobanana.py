#!/usr/bin/env python3
"""Generate wagon bot icon via Nano Banana (OpenRouter)."""
import os, sys, json, base64, urllib.request

# Load OpenRouter key — prefer env, fallback to .env file
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_KEY:
    env_path = "/Users/boris_ai/.hermes/profiles/boris/.env"
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k == "OPENROUTER_API_KEY":
                OPENROUTER_KEY = v.strip().strip('"').strip("'")
                break

if not OPENROUTER_KEY:
    print("ERROR: OPENROUTER_API_KEY not found in env or .env")
    sys.exit(1)

print(f"Key loaded: {OPENROUTER_KEY[:10]}...")
OUTPUT = "/Users/boris_ai/.hermes/profiles/boris/data/wagon_bot_icon_nb.png"

PROMPT = """A professional Telegram bot icon, 512x512px, flat vector style with subtle depth.
Central subject: a side-view minimalist freight gondola railway wagon, bold simplified silhouette, steel-blue metallic surfaces.
Inside the wagon body: glowing electric-blue bar chart with 4-5 bars of varying heights.
Background: deep navy circle, clean rounded-square crop.
Thin circuit traces and two glowing node dots at the bottom of the wagon, suggesting AI pipeline.
Color palette: navy background, steel blue wagon body, electric cyan chart bars, white highlights, silver details.
No text, no letters. High contrast for 50x50px readability.
Style: tech startup app icon, dark-mode aesthetic, flat illustration with sharp outlines.
The wagon fills 65% of the frame. No line graph. Keep it simple."""

req_data = json.dumps({
    "model": "google/gemini-2.5-flash-image",
    "messages": [{"role": "user", "content": PROMPT}],
    "modalities": ["image", "text"],
    "image_config": {"aspect_ratio": "1:1"}
}).encode()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=req_data,
    headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
)

print("Generating via Nano Banana (OpenRouter)...")
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
except Exception as e:
    print(f"API ERROR: {e}")
    sys.exit(1)

if "error" in result:
    print(f"OpenRouter error: {result['error']}")
    sys.exit(1)

images = result.get("choices", [{}])[0].get("message", {}).get("images", [])
if not images:
    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"No images. Text response: {text[:500]}")
    sys.exit(1)

img_url = images[0].get("image_url", {}).get("url", "")
if not img_url:
    print("No image URL in response")
    sys.exit(1)

if img_url.startswith("data:"):
    img_bytes = base64.b64decode(img_url.split(",", 1)[1])
elif img_url.startswith("http"):
    with urllib.request.urlopen(img_url) as r:
        img_bytes = r.read()
else:
    img_bytes = base64.b64decode(img_url)

with open(OUTPUT, "wb") as f:
    f.write(img_bytes)
print(f"Raw saved: {OUTPUT} ({len(img_bytes)} bytes)")

# Convert to 512x512 PNG
from PIL import Image
img = Image.open(OUTPUT)
img = img.convert("RGBA")
img = img.resize((512, 512), Image.LANCZOS)
img.save(OUTPUT, "PNG")

small = img.resize((50, 50), Image.LANCZOS)
small_path = OUTPUT.replace(".png", "_50x50.png")
small.save(small_path)
print(f"512x512: {OUTPUT}")
print(f"50x50:   {small_path}")
print("Done!")

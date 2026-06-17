#!/usr/bin/env python3
"""Generate images via OpenRouter (Nano Banana or GPT/SORA).
Usage: python3 gen_image_openrouter.py "<prompt>" [--model MODEL] [--output PATH]

Models (priority):
  1. google/gemini-2.5-flash-image (Nano Banana, default)
  2. openai/gpt-5-image (GPT/SORA, fallback)
"""
import os, sys, json, base64, urllib.request

# ── Config ──
def load_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    env_paths = [
        os.path.expanduser("~/.hermes/profiles/boris/.env"),
        os.path.expanduser("~/.hermes/.env"),
    ]
    for ep in env_paths:
        if os.path.exists(ep):
            for line in open(ep):
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

DEFAULT_MODEL = "google/gemini-2.5-flash-image"
FALLBACK_MODEL = "openai/gpt-5-image"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Args ──
import argparse
parser = argparse.ArgumentParser(description="Generate image via OpenRouter")
parser.add_argument("prompt", help="Image generation prompt")
parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
parser.add_argument("--output", default="", help="Output path (default: ~/gen_image_<ts>.png)")
parser.add_argument("--aspect-ratio", default="1:1", help="Aspect ratio (default: 1:1)")
parser.add_argument("--fallback", action="store_true", help="Use fallback model (GPT/SORA)")
args = parser.parse_args()

key = load_key()
if not key:
    print("ERROR: OPENROUTER_API_KEY not found")
    sys.exit(1)

model = FALLBACK_MODEL if args.fallback else args.model
output = args.output or os.path.expanduser(f"~/gen_image_{int(__import__('time').time())}.png")

# ── Generate ──
print(f"Model: {model}")
print(f"Aspect: {args.aspect_ratio}")
print(f"Prompt: {args.prompt[:100]}...")

data = json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": args.prompt}],
    "modalities": ["image", "text"],
    "image_config": {"aspect_ratio": args.aspect_ratio}
}).encode()

req = urllib.request.Request(
    API_URL, data=data,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
except Exception as e:
    print(f"API ERROR: {e}")
    sys.exit(1)

if "error" in result:
    print(f"OpenRouter error: {result['error']}")
    # Auto-fallback
    if not args.fallback and model != FALLBACK_MODEL:
        print(f"Falling back to {FALLBACK_MODEL}...")
        # Re-run with fallback
        os.execv(sys.executable, [sys.executable, __file__, args.prompt,
                                   "--model", FALLBACK_MODEL,
                                   "--output", output,
                                   "--aspect-ratio", args.aspect_ratio])
    sys.exit(1)

images = result.get("choices", [{}])[0].get("message", {}).get("images", [])
if not images:
    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"No images. Text: {text[:300]}")
    sys.exit(1)

img_url = images[0].get("image_url", {}).get("url", "")
if img_url.startswith("data:"):
    b64 = img_url.split(",", 1)[1]
    img_bytes = base64.b64decode(b64)
elif img_url.startswith("http"):
    with urllib.request.urlopen(img_url) as r:
        img_bytes = r.read()
else:
    img_bytes = base64.b64decode(img_url)

with open(output, "wb") as f:
    f.write(img_bytes)

# Resize to 512x512 via Pillow if available
try:
    from PIL import Image
    img = Image.open(output)
    img = img.convert("RGBA")
    img = img.resize((512, 512), Image.LANCZOS)
    img.save(output, "PNG")
except ImportError:
    pass

print(f"✓ {output} ({os.path.getsize(output)} bytes)")

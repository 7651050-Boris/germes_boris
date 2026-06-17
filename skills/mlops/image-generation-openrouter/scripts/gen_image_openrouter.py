#!/usr/bin/env python3
"""Image generation via OpenRouter. Usage: python3 gen_image_openrouter.py --prompt "..." --output out.png"""
import os, sys, json, base64, urllib.request, argparse

def load_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    for env_path in [
        os.path.expanduser("~/.hermes/profiles/boris/.env"),
        os.path.expanduser("~/.hermes/.env"),
    ]:
        if os.path.exists(env_path):
            for line in open(env_path):
                line = line.strip()
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k == "OPENROUTER_API_KEY":
                    return v.strip().strip('"').strip("'")
    return ""

def generate(prompt: str, model: str = "google/gemini-2.5-flash-image",
             aspect_ratio: str = "1:1", output: str = "output.png") -> str:
    key = load_key()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not found")

    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
        "image_config": {"aspect_ratio": aspect_ratio}
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )

    print(f"Generating via {model}...")
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read())

    if "error" in result:
        raise RuntimeError(f"OpenRouter error: {result['error']}")

    images = result.get("choices", [{}])[0].get("message", {}).get("images", [])
    if not images:
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        raise RuntimeError(f"No images. Text: {text[:300]}")

    img_url = images[0].get("image_url", {}).get("url", "")
    if not img_url:
        raise RuntimeError("No image URL")

    if img_url.startswith("data:"):
        img_bytes = base64.b64decode(img_url.split(",", 1)[1])
    elif img_url.startswith("http"):
        with urllib.request.urlopen(img_url) as r:
            img_bytes = r.read()
    else:
        img_bytes = base64.b64decode(img_url)

    with open(output, "wb") as f:
        f.write(img_bytes)

    # Resize if needed
    from PIL import Image
    img = Image.open(output)
    img = img.convert("RGBA")
    img.save(output, "PNG")

    # 50x50 test
    small = img.resize((50, 50), Image.LANCZOS)
    small_path = output.rsplit(".", 1)[0] + "_50x50.png"
    small.save(small_path)

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", default="output.png")
    parser.add_argument("--model", default="google/gemini-2.5-flash-image")
    parser.add_argument("--aspect-ratio", default="1:1")
    args = parser.parse_args()

    try:
        path = generate(args.prompt, args.model, args.aspect_ratio, args.output)
        print(f"Done: {path}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

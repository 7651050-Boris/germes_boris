# OpenRouter Image Generation API

Quick reference for generating images via OpenRouter Chat Completions API.

## Endpoint
`POST https://openrouter.ai/api/v1/chat/completions`

## Required headers
```
Authorization: Bearer <OPENROUTER_API_KEY>
Content-Type: application/json
```

## Request body (Nano Banana)
```json
{
  "model": "google/gemini-2.5-flash-image",
  "messages": [{"role": "user", "content": "<prompt>"}],
  "modalities": ["image", "text"],
  "image_config": {"aspect_ratio": "1:1"}
}
```

## Model priority (для Бориса)
1. `google/gemini-2.5-flash-image` — Nano Banana ($0.30/$2.50 per 1M)
2. `openai/gpt-5-image` — GPT/SORA (fallback)

## Supported aspect ratios
`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

## Image size options
`0.5K`, `1K` (default), `2K`, `4K`
Set via `image_config.image_size`.

## Response parsing
```python
images = result["choices"][0]["message"]["images"]
img_url = images[0]["image_url"]["url"]
# url is either data:image/png;base64,... or https://...
```

## Pricing (June 2026)
| Model | Input | Output |
|---|---|---|
| Nano Banana (gemini-2.5-flash-image) | $0.30/M | $2.50/M |
| GPT-5 Image | ~$5.00/M | ~$15.00/M |

## Pitfalls
- Image models return images in `message.images[]`, NOT in `message.content`
- Some models return base64 data URLs, others return HTTP URLs
- Aspect ratio `1:1` = 1024×1024 (default)
- Context window for Nano Banana: 33K tokens — keep prompts concise
- Single image generation typically costs <$0.01

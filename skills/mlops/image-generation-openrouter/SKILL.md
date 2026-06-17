---
name: image-generation-openrouter
description: "Генерация изображений через OpenRouter: Nano Banana (основной) → GPT/SORA (запасной). Все модели — через единый провайдер OpenRouter."
version: 1.0.0
category: mlops
---

# Генерация изображений через OpenRouter

ВСЕ запросы на генерацию изображений — через OpenRouter. Никаких прямых вызовов Google/OpenAI API.

## Приоритет моделей

| Приоритет | Модель OpenRouter | Название | Цена (вход/выход за 1M) |
|---|---|---|---|
| 🥇 Основная | `google/gemini-2.5-flash-image` | Nano Banana | $0.30 / $2.50 |
| 🥈 Запасная | `openai/gpt-5-image` | GPT/SORA | ~$0.50 / $5.00 |

## Полный пайплайн

### Шаг 1: Дизайн промпта (креатив)

Спавнить `claude-sonnet-4.6` для составления качественного промпта:

```bash
hermes chat --model anthropic/claude-sonnet-4.6 --provider openrouter -q "Разработай концепт и напиши подробный промпт для генерации изображения: [описание задачи]. Выдай: 1) концепт, 2) промпт на английском для AI-генерации, 3) цветовую палитру."
```

### Шаг 2: Генерация через Nano Banana

Использовать Python-скрипт `scripts/gen_image_openrouter.py`:

```bash
python3 scripts/gen_image_openrouter.py --prompt "..." --output /path/to/output.png
```

Скрипт вызывает OpenRouter Chat Completions API с моделью `google/gemini-2.5-flash-image`, параметрами `modalities: ["image", "text"]`, `image_config: { aspect_ratio: "1:1" }`.

### Шаг 3: Если Nano Banana не справился

Повторить с `openai/gpt-5-image` (запасная модель).

## API формат (OpenRouter)

```python
{
    "model": "google/gemini-2.5-flash-image",
    "messages": [{"role": "user", "content": "PROMPT"}],
    "modalities": ["image", "text"],
    "image_config": {"aspect_ratio": "1:1"}
}
```

Ответ содержит `choices[0].message.images[0].image_url.url` — base64 или URL изображения.

## Ключ

`OPENROUTER_API_KEY` из `.env`. Единый ключ для ВСЕХ моделей.

## Pitfalls

- ❌ **НИКОГДА не использовать Pillow/programmatic rendering для задачи, где нужна AI-генерация.** Пользователь явно хочет AI-изображения. Pillow — только для утилитарной обработки (resize, convert), а не для создания контента.
- ❌ **НИКОГДА не использовать прямые API Google/OpenAI — только OpenRouter.** Все модели доступны через единый ключ `OPENROUTER_API_KEY`.
- ❌ **НЕ пропускать шаг 1 (дизайн промпта через claude-sonnet-4.6).** Промпт от claude даёт качественный результат; пропуск = экономия 30 секунд ценой плохой картинки.
- ✅ Промпт для Nano Banana — на английском, детальный, с цветами и стилем
- ✅ Для иконок: `aspect_ratio: "1:1"`, просить "no text, no letters"
- ✅ При ошибке/таймауте Nano Banana — автоматически пробовать `openai/gpt-5-image`

### 🔤 Текст и география: когда НЕ использовать AI-генерацию

**Провал 17.06:** Nano Banana трижды сгенерировал карту России с глэмпингами: дважды с промптами от Sonnet 4.6, один раз — с детальным промптом от Opus 4.8. Все три раза: орфография исковеркана, география искажена. Даже экспертный промпт от Opus 4.8 не исправил фундаментальную неспособность Nano Banana рендерить читаемую кириллицу. Четвёртая попытка — Pillow с точными подписями — решила задачу.

**Правило:** если изображение ДОЛЖНО содержать читаемый текст (карты, инфографика, диаграммы, схемы с подписями) — используй Pillow/programmatic rendering. AI-генерация НЕ гарантирует корректную орфографию и точное позиционирование. **Это ограничение модели, а не качество промпта.**

**Когда AI (Nano Banana):** художественные изображения, иллюстрации, иконки без текста, фоны, эстетика.
**Когда Pillow:** карты, графики, точные схемы, любой контент с читаемым текстом.

См. `references/text-geography-failure.md` — детальный разбор трёх попыток генерации карты.

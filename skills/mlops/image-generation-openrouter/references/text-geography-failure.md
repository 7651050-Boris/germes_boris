# Text & Geography Failure — 17.06.2026

## Task
Generate a map of Russia with 10 glampling location markers and labels.

## Attempt 1 — Nano Banana (google/gemini-2.5-flash-image)

**Prompt:** "Map illustration of Russia showing glampling camping locations... 10 small glowing amber/orange markers... Title in Russian: ГЛЭМПИНГИ РОССИИ..."

**Result:**
- Map outline: recognizable Russia shape ✓
- Markers: 10 golden dots placed roughly ✓  
- **Text: GARBLED.** Examples:
  - «Кальннудь» instead of «Калининград»
  - «Кудииь» instead of «Курилы»
  - «Сощи» instead of «Сочи»
  - «Краснадар» instead of «Краснодар»
  - «Моска» instead of «Москва»
- Geography: Москва placed in Caucasus/Volga region, Камчатка in ocean

**Result: UNUSABLE** — spelling errors everywhere, misleading geography.

## Attempt 2 — Nano Banana with corrected prompt

**Prompt changes:** Added «EXACT spelling below: Карелия, Санкт-Петербург, Москва, Казань... Labels must be correctly spelled.»

**Result:**
- Map outline: good ✓
- **Text: STILL GARBLED.** Examples:
  - «Каэва» instead of «Казань»
  - «Байбкал» instead of «Байкал»
  - «Камнила» instead of «Камчатка»
  - «Калинсннар» instead of «Калининград»
  - Москва appeared twice in wrong locations
- Geography: still inaccurate placement

**Result: STILL UNUSABLE.** Explicit spelling instruction did not help.

## Attempt 3 — Pillow (programmatic)

**Method:** Python + PIL, polygon outline of Russia, hardcoded coordinates, Arial font.

**Result:**
- All 10 labels: PERFECT ✓
- Map outline: simplified but recognizable ✓
- Markers: correctly positioned ✓
- Routes: dashed connecting lines ✓
- Dark elegant style maintained ✓

## Attempt 4 — Opus 4.8 prompt → Nano Banana (17.06.2026)

**User request:** «Пусть опус пишет промт. Опус 4.8.» — пользователь затребовал более сильную модель для составления промпта.

**Opus 4.8 prompt quality:** Отличный. Детальный промпт на английском с явным акцентом: географически точные контуры России, точные позиции всех 10 локаций, требования к читаемой кириллице, перечисление всех названий в точном написании.

**Nano Banana result: STILL GARBLED.**
- «Калинннад» вместо «Калининград»
- «Санкт-Петбург» вместо «Санкт-Петербург»
- «Кареля» вместо «Карелия»
- «Байбал» вместо «Байкал»
- «раземения» вместо «размещения»
- «Казан» вместо «Казань»
- «Москва» подписана дважды
- «ателия» — нераспознаваемый мусор
- География искажена

**Вывод:** Даже эксперт-промпт от Opus 4.8 не решает проблему кириллицы в Nano Banana. Это фундаментальное ограничение модели рендеринга текста, а не проблема качества промпта.

## Lesson

**AI image models CANNOT reliably produce readable text or accurate geography.** The text rendering in Nano Banana/Gemini image models introduces character-level errors (hallucinations in pixel space). No amount of prompting or explicit spelling instructions fixes this.

**Decision rule:**
- If image MUST contain readable text → Pillow (programmatic)
- If image is artistic/illustrative (no text) → Nano Banana (AI generation)
- For maps with labels → Pillow with exact coordinates and Arial font

# Nano Banana Cyrillic Failure — 17.06.2026

## Summary

Nano Banana (`google/gemini-2.5-flash-image`) cannot render readable Cyrillic text. This is a **fundamental model limitation**, not a prompt quality issue. Three attempts with increasing prompt quality — including an expert-level prompt from Opus 4.8 — all failed.

## Attempts

| # | Prompt by | Model | Result |
|---|---|---|---|
| 1 | Sonnet 4.6 | Nano Banana | Garbled: «Кальннудь», «Кудииь», «Сощи», «Краснадар», «Моска» |
| 2 | Sonnet 4.6 (corrected) | Nano Banana | Still garbled: «Каэва», «Байбкал», «Камнила», «Калинсннар» |
| 3 | **Opus 4.8** (expert) | Nano Banana | **Still garbled:** «Калинннад», «Кареля», «Байбал», «ателия», «раземения» |

## Opus 4.8 Prompt (Attempt 3)

Opus produced a detailed English prompt with explicit instructions:
- "exactly 10 glowing golden circular dot markers at the GEOGRAPHICALLY CORRECT real positions"
- "ALL TEXT LABELS MUST BE IN RUSSIAN CYRILLIC, perfectly legible, sharp, and correctly spelled"
- Listed all 10 names in exact spelling: «Калининград», «Санкт-Петербург», «Карелия», «Москва», «Казань», «Сочи», «Крым», «Алтай», «Байкал», «Камчатка»
- "absolutely NO garbled characters, no fake letters, no Latin substitutions"

Even with this level of detail, Nano Banana produced:
- «Калинннад» instead of «Калининград»
- «Санкт-Петбург» instead of «Санкт-Петербург»
- «Байбал» instead of «Байкал»
- «раземения» instead of «размещения»
- «ателия» — unrecognizable garbage

## Conclusion

**No amount of prompt engineering can fix Nano Banana's Cyrillic rendering.** The model fundamentally cannot produce accurate non-Latin text. For any image requiring readable text:

- ❌ Nano Banana / AI generation
- ✅ Pillow (Python) with system fonts

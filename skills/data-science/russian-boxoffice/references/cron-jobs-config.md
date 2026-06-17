# Cron Jobs for @kassakino Box Office Channel

Created 2026-06-15. User: @Борис Мягков. Bot: @gera_boris_1_bot.
Last updated: 2026-06-16.

## Current Channel Status ⚠️

**@kassakino** — бот @gera_boris_1_bot добавлен как администратор, но:
- Канал НЕ отображается в `send_message(action='list')`
- Бот не получает Telegram update из канала
- `channel_directory.json` содержит только DM с пользователем

**Попытки решить:**
1. ✅ Бот добавлен как администратор канала
2. ✅ Пользователь написал сообщение в канале (бот должен получить update)
3. ❌ Канал всё ещё не resolved

**Что не помогло:**
- Добавление бота как администратора в существующий публичный канал
- Удаление и повторное добавление
- Написание сообщения в канале

**Рекомендация:** Создать новый канал с нуля, добавить бота админом, написать в нём, проверить send_message list, и ОБНОВИТЬ deliver на всех задачах.

## Active Jobs

### Job 1: Ежедневные сборы (Daily Top-10)
- **ID:** `74fd174cbc25`
- **Schedule:** `0 9 * * *` (ежедневно в 09:00 MSK, конвертируется в 13:00 UTC)
- **Deliver:** `origin` ⚠️ — возвращается в этот чат (DM с пользователем)
- **Toolsets:** `browser`
- **Created:** 2026-06-15
- **Last run:** никогда

### Job 2: Премьеры недели (Monday)
- **ID:** `edb12d88d206`
- **Schedule:** `0 8 * * 1` (пн в 08:00 MSK)
- **Deliver:** `origin` ⚠️
- **Toolsets:** `browser`

### Job 3: Итоги уикенда (Monday)
- **ID:** `8960fde2ce46`
- **Schedule:** `0 10 * * 1` (пн в 10:00 MSK)
- **Deliver:** `origin` ⚠️
- **Toolsets:** `browser`

### Job 4: Премьеры сегодня (Thursday)
- **ID:** `938ac0e37528`
- **Schedule:** `0 7 * * 4` (чт в 07:00 MSK)
- **Deliver:** `origin` ⚠️
- **Toolsets:** `browser`

### Job 5: Все премьеры месяца (1st)
- **ID:** `908fb7feceb0`
- **Schedule:** `0 8 1 * *` (1-го числа в 08:00 MSK)
- **Deliver:** `origin` ⚠️
- **Toolsets:** `browser`

## Deliver Target Fix Plan

All 5 jobs currently deliver to `origin` (the chat where they were created — this Telegram DM).
To redirect to @kassakino channel:

1. **Fix channel first** — create new channel or get bot properly wired
2. **Update each job:**
   ```
   cronjob(action='update', job_id='74fd174cbc25', deliver='telegram:-100<channel_id>')
   cronjob(action='update', job_id='edb12d88d206', deliver='telegram:-100<channel_id>')
   cronjob(action='update', job_id='8960fde2ce46', deliver='telegram:-100<channel_id>')
   cronjob(action='update', job_id='938ac0e37528', deliver='telegram:-100<channel_id>')
   cronjob(action='update', job_id='908fb7feceb0', deliver='telegram:-100<channel_id>')
   ```

## Scripts

Location: `~/.hermes/scripts/` and skill scripts under `skills/data-science/russian-boxoffice/scripts/`
- `eais_top10.py` — parser for ЕАИС JSON endpoint `/ekb/top-films/` (historical data, dsum often 0)

Both scripts are supplementary — for daily data, use browser-based parsing (browser_navigate).

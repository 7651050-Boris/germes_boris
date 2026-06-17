---
name: telegram-bot-development
description: "Build Telegram bots with python-telegram-bot: NL→SQL→NL pipelines, LLM integration, database backends, background deployment, and user-style formatting preferences."
version: 1.0.0
author: agent
tags: [telegram, bot, python-telegram-bot, sqlite, llm, deepseek, nlp]
platforms: [macos, linux]
metadata:
  hermes:
    tags: [telegram, bot, python-telegram-bot, sqlite, llm]
---

# Telegram Bot Development

Build production Telegram bots that query databases via natural language using python-telegram-bot and LLM-powered SQL generation.

## User Style Preferences

**CRITICAL — these preferences apply to ALL bot output formatting:**

1. **No system messages in responses** — no SQL queries, no debug, no "here is the answer", no markdown blocks with raw data. The user sees ONLY the meaningful answer.
2. **Natural language summaries** — bots MUST summarize raw data into human-readable Russian text, not dump tables or raw numbers. Use a second LLM pass for summarization.
3. **Concise, meeting-style responses** — as if answering at a briefing. No greetings, no "вот ответ", no filler.

## Architecture: Two-Pass NL→SQL→NL Pipeline

```
User question → LLM (SQL generation) → Execute SQL → LLM (summarization) → Final response
```

### Pass 1: SQL Generation

- Send user question + full DB schema to LLM
- System prompt: "Ты — SQL-генератор. Отвечай ТОЛЬКО SQL-запросом, без пояснений и без markdown."
- Temperature: 0.1, max_tokens: 500
- Strip markdown code fences from response
- Use `deepseek-chat` endpoint: `https://api.deepseek.com/v1/chat/completions`

### Pass 2: Summarization

- Send question + raw query results back to LLM
- System prompt: "Напиши краткую, осмысленную сводку на русском. Без приветствий, без вступления. Только суть: цифры, проценты, ключевые выводы."
- Temperature: 0.3, max_tokens: 600
- Include base statistics (total row count) so LLM can compute percentages

### Error Handling

- SQL errors: return `❌ Ошибка: {error_message}` (no SQL echo)
- Empty results: "🔍 Ничего не найдено."
- LLM API failure: fall back to raw table format with error preamble

## Hermes Home Isolation Pitfall

When a standalone script runs under Hermes, `$HOME` is overridden to the isolated profile home (`~/.hermes/profiles/<name>/home`). This means:

- `Path.home()` → isolated dir, NOT real user home
- `os.path.expanduser("~")` → isolated dir, NOT real user home

**Fix:** Use absolute paths to the real user home for all file access:
```python
# WRONG under Hermes:
DB_PATH = Path.home() / ".hermes/profiles/boris/data/wagons.db"

# RIGHT:
DB_PATH = Path("/Users/boris_ai/.hermes/profiles/boris/data/wagons.db")
```

This applies to: database files, config files, .env files, and any path the script needs from the real filesystem.

## API Key Resolution

Bots running as standalone scripts need to resolve API keys from Hermes config:

```python
import yaml
real_config = "/Users/boris_ai/.hermes/profiles/boris/config.yaml"
with open(real_config) as f:
    config = yaml.safe_load(f)
api_key = config.get("model", {}).get("api_key", "")
```

Prefer this over reading from `.env` which may not have the key. The Hermes config.yaml always has `model.api_key`.

## Background Deployment

Start the bot as a background process managed by Hermes:

```python
terminal(
    command="python3 /absolute/path/to/bot.py 2>&1",
    background=True,
    notify_on_complete=True
)
```

- Always use absolute paths for the script
- `notify_on_complete=True` ensures you get notified if the bot crashes
- To restart: `process(action="kill", session_id="...")` → then re-launch

### Background Script Reliability

**Prefer `execute_code` over `terminal(background=True)`** for long-running Python scripts that need real-time progress feedback. Background terminal processes often buffer stdout silently — `python3 -u` (unbuffered) helps but `execute_code` is more reliable for scripts with progress output.

When using `terminal(background=True)`:
- Add `-u` flag: `python3 -u script.py 2>&1` for unbuffered stdout
- Even with `-u`, output may arrive in chunks or be delayed — don't assume real-time visibility
- For data-collection scripts that produce rich progress output, run inline via `execute_code` or invoke directly with `terminal(background=False, timeout=300)`

### Process Restart Cycle

When updating a running bot:
1. `process(action="kill", session_id="...")` — kill old process
2. Wait for the kill confirmation (old process may emit a delayed completion notice)
3. Launch new process with updated code
4. Ignore late-arriving completion notices from the killed process — they're stale

## Token Management

1. Create bot via @BotFather: `/newbot` → get token
2. Store token in `WAGONS_BOT_TOKEN=...` in profile `.env`
3. Bot script reads it from `os.environ.get("WAGONS_BOT_TOKEN")`

## Reference Table Pattern

When enriching a database with external reference data (e.g., technical specifications), use the pattern described in `references/web-scraping-to-sqlite.md`.

## Voice Message Handling

Bots accept voice messages via `filters.VOICE` handler. Voice files are downloaded as `.ogg`, converted to WAV via ffmpeg, and transcribed using Google Speech Recognition (free, Russian-capable). Full pattern in `references/voice-message-handling.md`.

Key points:
- `speech_recognition` is blocking — wrap in `asyncio.get_event_loop().run_in_executor(None, fn)`
- ffmpeg static binary from evermeet.cx (macOS)
- Transcribed text echoed to user before query processing (verification step)

## Computed Classification Columns

When multiple columns encode overlapping business logic (ownership + lease + lessee), derive a single clean `category` column via `CASE WHEN`. See `references/computed-classification-columns.md` for the complete pattern with examples.

## Bot Template

Start new bots from `templates/bot_template.py` — a complete NL→SQL→NL bot with proper Hermes path handling, two-pass LLM summarization, and voice message support via `filters.VOICE`. Copy, edit the config section, customize the DB_SCHEMA, and run.

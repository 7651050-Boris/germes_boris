#!/usr/bin/env python3
"""NL→SQL→NL Telegram bot template — start from this for new bots."""

import os, sys, sqlite3, json
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── Config (EDIT THESE) ─────────────────────────────────
REAL_HOME = "/Users/boris_ai"  # Real user home (Hermes overrides $HOME)
PROFILE = "boris"              # Hermes profile name
DB_PATH = Path(f"{REAL_HOME}/.hermes/profiles/{PROFILE}/data/example.db")
BOT_TOKEN = os.environ.get("EXAMPLE_BOT_TOKEN", "")

# Resolve API key from Hermes config
def _load_api_key():
    import yaml
    config_path = f"{REAL_HOME}/.hermes/profiles/{PROFILE}/config.yaml"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config.get("model", {}).get("api_key", "")
    return ""

API_KEY = _load_api_key()

# ── DB Schema (EDIT: describe YOUR tables) ──────────────
DB_SCHEMA = """
Таблица my_table (описание данных):
- col1 — описание колонки 1
- col2 — описание колонки 2

ПРАВИЛА ГЕНЕРАЦИИ SQL:
1. Возвращай ТОЛЬКО SQL запрос, ничего больше. Без markdown-блоков ```, без объяснений.
2. Все значения — строки (TEXT). Числа в кавычках: WHERE year > '2000'
3. LIKE для частичного совпадения: WHERE name LIKE '%поиск%'
4. Всегда LIMIT 20 если не указано иное. Максимум LIMIT 100.
5. Для подсчёта: SELECT COUNT(*) FROM my_table WHERE ...
6. Для списка: SELECT col1, col2, col3 FROM my_table WHERE ...
7. Для группировки: SELECT col, COUNT(*) FROM my_table GROUP BY col ORDER BY 2 DESC
"""

SYSTEM_PROMPT_SQL = f"""Ты — SQL-генератор.
Отвечай ТОЛЬКО SQL-запросом, без пояснений и без markdown.

{DB_SCHEMA}"""


# ── SQL generation (Pass 1) ─────────────────────────────
def generate_sql(question: str) -> str:
    import urllib.request
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_SQL},
            {"role": "user", "content": question}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }).encode()

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            sql = result["choices"][0]["message"]["content"].strip()
            sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
            return sql
    except Exception as e:
        return f"ERROR: {e}"


def execute_sql(sql: str) -> tuple:
    """Execute SQL and return (headers, rows, error)."""
    try:
        db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cur = db.execute(sql)
        headers = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(25)
        db.close()
        return headers, rows, None
    except Exception as e:
        return [], [], str(e)


def summarize_result(question: str, headers: list, rows: list) -> str:
    """Send raw data back to LLM for natural language summary (Pass 2)."""
    import urllib.request

    if not rows:
        return "🔍 Ничего не найдено."

    # Build raw data text
    data_text = "КОЛОНКИ: " + ", ".join(headers) + "\n"
    for i, row in enumerate(rows[:20]):
        vals = [f"{headers[j]}={row[j]}" for j in range(min(len(headers), len(row))) if row[j]]
        data_text += f"{i+1}. " + "; ".join(vals) + "\n"

    sys_prompt = """Ты — аналитик данных. На вопрос пользователя получил сырые данные.
Напиши краткую, осмысленную сводку на русском языке. Без приветствий, без "вот ответ", без вступления.
Только суть: цифры, проценты, ключевые выводы. Строго по делу, как будто отвечаешь на совещании."""

    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Вопрос: {question}\n\nДанные:\n{data_text}"}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }).encode()

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Fallback: raw table
        return f"(Ошибка: {e})"


def format_result(question: str, sql: str, headers: list, rows: list, error: str) -> str:
    if error:
        return f"❌ Ошибка: {error}"
    if not rows:
        return "🔍 Ничего не найдено."
    return summarize_result(question, headers, rows)


# ── Bot handlers ────────────────────────────────────────
FFMPEG_PATH = "/tmp/ffmpeg"

async def transcribe_voice(file_path: str) -> str:
    """Convert ogg to wav and transcribe using Google Speech Recognition."""
    import subprocess, asyncio
    import speech_recognition as sr

    wav_path = file_path + ".wav"
    try:
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", file_path, "-ac", "1", "-ar", "16000", wav_path],
            capture_output=True, timeout=15
        )
        loop = asyncio.get_event_loop()
        
        def _recognize():
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = r.record(source)
            return r.recognize_google(audio, language="ru-RU")
        
        return await loop.run_in_executor(None, _recognize)
    except Exception as e:
        print(f"Voice error: {e}")
        return ""
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Бот запущен**\n\n"
        "Задай вопрос текстом или голосовым — я найду ответ в базе данных."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return
    await process_query(update, question)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    if not voice:
        return

    await update.message.chat.send_action("typing")
    
    file = await voice.get_file()
    ogg_path = f"/tmp/voice_{update.message.message_id}.ogg"
    await file.download_to_drive(ogg_path)
    
    text = await transcribe_voice(ogg_path)
    if os.path.exists(ogg_path):
        os.remove(ogg_path)
    
    if not text:
        await update.message.reply_text("🎤 Не удалось распознать речь.")
        return
    
    await update.message.reply_text(f"🎤 *{text}*", parse_mode="Markdown")
    await process_query(update, text)

async def process_query(update: Update, question: str):
    """Full NL→SQL→Summarize pipeline."""
    await update.message.chat.send_action("typing")
    
    sql = generate_sql(question)
    if sql.startswith("ERROR:"):
        await update.message.reply_text(f"❌ Ошибка: {sql}")
        return
    
    headers, rows, error = execute_sql(sql)
    result = format_result(question, sql, headers, rows, error)
    await update.message.reply_text(result)


def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set")
        sys.exit(1)
    if not API_KEY:
        print("ERROR: API key not found")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("🤖 Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

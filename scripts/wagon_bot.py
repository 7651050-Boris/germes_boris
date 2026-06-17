#!/usr/bin/env python3
"""Telegram bot for querying wagon database (wagons.db)."""

import os, sys, sqlite3, json, textwrap
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── Config ──────────────────────────────────────────────
ENV_PATH = Path.home() / ".hermes/profiles/boris/.env"
DB_PATH = Path("/Users/boris_ai/.hermes/profiles/boris/data/wagons.db")

def load_env():
    """Load env vars from .env file."""
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if k not in os.environ:
                    os.environ[k] = v.strip('"').strip("'")

load_env()

DEEPSEEK_KEY = ""
BOT_TOKEN = os.environ.get("WAGONS_BOT_TOKEN", "")

# Load DeepSeek key from Hermes config
def _load_deepseek_key():
    import yaml
    # Use REAL home (Hermes overrides $HOME to isolated dir)
    real_home = os.path.expanduser("~")
    # If HOME is overridden, try to detect real home
    real_config = "/Users/boris_ai/.hermes/profiles/boris/config.yaml"
    if os.path.exists(real_config):
        with open(real_config) as f:
            config = yaml.safe_load(f)
        return config.get("model", {}).get("api_key", "")
    # Fallback
    config_path = Path(real_home) / ".hermes/profiles/boris/config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config.get("model", {}).get("api_key", "")
    return ""

DEEPSEEK_KEY = _load_deepseek_key()

DB_SCHEMA = """Таблица wagons (вагоны РЖД, май 2026). Колонки (все TEXT):
wagon_num — номер вагона (уникальный, 8 цифр)
wagon_type — род: Полувагоны, Цистерны, Крытые, Платформы, Зерновозы, Рефрижераторы, Прочие
wagon_subtype — подрод
specialization — специализация (код + описание)
build_date — дата постройки
model — модель вагона (например: 12-132, 15-1547-03, 11-280, 19-9549, ВПМ-770). Первые 2 цифры: 12=полувагоны, 15=цистерны, 11=крытые, 13=платформы/прочие, 19=зерновозы/прочие, 23=прочие
ownership — принадл: ИП (инвентарный парк), ПС (собственный)
fleet — парк: Рабочий парк, Нерабочий парк, Отс ВМ, За балансом
fleet_type — тип парка: Порожние, Груженые, Неисправные, Отсутств в ВМ, Тех. надобности
fleet_state — сост: Порожние, Груж. транзитные, Груж. местные, В деп. ремонт, В кап. ремонт, В тек. рем (ТР2), Исключение и др.
in_vm — наличие в ВМ: нал. в ВМ, отс. в ВМ
malfunction_flag — неисправность ДВ
lease_flag — аренда
accounting — вид учёта
owner — собственник (например: ОАО Вторая грузовая компания, Первая грузовая компания, \"Казтемиртранс\" АО, Инвентарный парк, ЦДИ - филиал ОАО \"РЖД\", \"ТрансФин-М\" ПАО, \"ГТЛК\" АО, \"РУСАГРОТРАНС\" ООО и 400+ других)
state_owner — гос собственник (код страны: РЖД, КЗХ, УЗБ, АЗ, ГР, ТДЖ и др.)
lessee — арендатор
egrpo_owner — собственник по ЕГРПО
operator — оператор (АО \"ФГК\", АО \"ПГК\", ООО \"МОДУМ-ТРАНС\", АО \"НТК\", ООО \"ТРАНСОЙЛ\" и др.)
station — станция приписки (КОЛПИН, МЕРЕТЬ, БЕЛОВО, НВЛИПЦ и др.)
railway — дорога приписки: ЗСБ, МСК, ОКТ, КЗХ, ЮВС, ЮУР, КРС, СВР, ПРВ, СЕВ, КБШ, СКВ, ЗБК, ВСБ, ДВС
service_interval — интервал сроков службы (0-9 лет, 10-19 лет, 20-29 лет, 30-39 лет, 40-49 лет, >=50 лет)
last_depot_repair — дата последнего деповского ремонта
next_repair — дата следующего ремонта
last_overhaul — дата последнего капремонта
last_current1/2 — даты текущих ремонтов
empty_mileage — порожний пробег (км)
total_mileage — общий пробег (км)
build_year — год постройки (1938-2026)
service_life — срок службы
factory — завод-изготовитель (АО \"НПК\"Уралвагонзавод\", АО Алтайвагон, АО \"ТВСЗ\", АО \"Pузхиммаш\", ЧАО \"Азовобщемаш\", ПАО \"КВСЗ\", ОАО \"Завод металлоконструкций\" и др.)
depot — депо приписки
service_expired — истек срок сл / не истек срок сл
standard_term — признак нормсрока: просрочен норм ср сл / не просрочен норм ср сл
extended_term — признак просрочки полуторного срока
ownership_category — категория владения: Собственник, Собственник-арендодатель, Инвентарный парк, Лизинг

ДОПОЛНИТЕЛЬНАЯ ТАБЛИЦА wagon_specs (технические характеристики моделей):
Можно JOIN по model. Колонки:
- axles — осность (4, 6, 8)
- capacity — грузоподъёмность, тонны
- tare_min / tare_max — тара (мин / макс), тонны
- axle_load_kn — статическая нагрузка на ось, кН
- axle_load_ton — нагрузка на ось, тонн-сил
- bogie — модель тележки (18-100, 18-9855 и др.)
- speed_kmh — конструкционная скорость, км/ч
- service_life_years — нормативный срок службы, лет
- factory — завод-изготовитель
- gauge_mm — ширина колеи, мм
- volume — объём кузова/котла, м³
- wheelbase_mm — база вагона, мм
- production_start — год начала производства
- gabarit — габарит по ГОСТ 9238
- body_material — материал кузова

Пример JOIN:
SELECT w.wagon_num, w.model, s.capacity, s.axle_load_ton, s.axles
FROM wagons w
LEFT JOIN wagon_specs s ON w.model = s.model
WHERE w.wagon_num = '63596241'

Для вопросов про нагрузку на ось — используй axle_load_ton.
Для вопросов про грузоподъёмность — capacity.
Для фильтрации по осности — s.axles = 4 / 6 / 8.

СТАТИСТИКА БАЗЫ:
- Всего вагонов: 1,772,596
- Полувагонов: 796,601 | Цистерн: 353,838 | Прочих: 335,629 | Зерновозов: 110,826 | Крытых: 91,787 | Платформ: 79,858 | Рефрижераторов: 4,057
- Рабочий парк: 1,538,243 | Нерабочий: 175,198 | Отс ВМ: 34,023
- Порожних: 999,095 | Гружёных: 539,148 | Неисправных: 133,880
- С истекшим сроком службы: 97,740 | Не истек: 1,674,856
- Дороги (топ-5): ЗСБ (287K), МСК (228K), ОКТ (211K), КЗХ (150K), ЮВС (137K)
- Собственники (топ-5): ВГК (106K), Инвентарный парк (104K), ПГК (59K), ГТЛК (56K), НефтеТрансСервис (55K)
- Заводы (топ-3): Уралвагонзавод (361K), Алтайвагон (177K), ТВСЗ (173K)
- Годы постройки: 1938-2026

ПРАВИЛА ГЕНЕРАЦИИ SQL:
1. Возвращай ТОЛЬКО SQL запрос, ничего больше. Без markdown-блоков ```, без объяснений.
2. Все значения — строки (TEXT). Числа в кавычках: WHERE build_year > '2000'
3. LIKE для частичного совпадения: WHERE owner LIKE '%Вторая грузовая%'
4. Всегда LIMIT 20 если не указано иное. Максимум LIMIT 100.
5. Для подсчёта: SELECT COUNT(*) FROM wagons WHERE ...
6. Для списка: SELECT wagon_num, wagon_type, model, ownership_category, owner, fleet, fleet_state, build_year FROM wagons WHERE ...
7. Для группировки: SELECT column, COUNT(*) FROM wagons GROUP BY column ORDER BY 2 DESC
8. Сложные условия: WHERE fleet = 'Рабочий парк' AND (wagon_type = 'Полувагоны' OR wagon_type = 'Цистерны')
9. Пустые значения: WHERE railway IS NOT NULL AND railway != ''
10. Имена собственные точно как в схеме: 'ОАО Вторая грузовая компания', 'ЦДИ - филиал ОАО \"РЖД\"', 'АО \"НПК\"Уралвагонзавод\"\"'
"""

SYSTEM_PROMPT = f"""Ты — SQL-генератор для базы вагонов РЖД. 
Отвечай ТОЛЬКО SQL-запросом, без пояснений и без markdown.

{DB_SCHEMA}"""


# ── SQL generation via LLM ──────────────────────────────
def generate_sql(question: str) -> str:
    """Send question to LLM, get SQL back."""
    import urllib.request

    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }).encode()

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            sql = result["choices"][0]["message"]["content"].strip()
            # Clean markdown if present
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
    """Send raw data + question back to LLM for a human-readable summary."""
    import urllib.request

    if not rows:
        return "🔍 Ничего не найдено."

    # Build raw data text
    data_text = "КОЛОНКИ: " + ", ".join(headers) + "\n"
    for i, row in enumerate(rows[:20]):
        vals = [f"{headers[j]}={row[j]}" for j in range(min(len(headers), len(row))) if row[j]]
        data_text += f"{i+1}. " + "; ".join(vals) + "\n"

    sys_prompt = """Ты — аналитик парка вагонов РЖД. На вопрос пользователя ты получил сырые данные из базы.
Твоя задача — написать краткую, осмысленную сводку на русском языке. Без приветствий, без "вот ответ", без вступления.
Только суть: цифры, проценты, ключевые выводы. Строго по делу, как будто отвечаешь на совещании.
Формат: сжатый текст, числа с разделителями тысяч, проценты от базы где уместно.
БАЗА: 1 772 596 вагонов всего."""

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
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Fallback: return raw table
        return f"(Ошибка сводки: {e})\n\nСырые данные:\n" + _raw_table(headers, rows)


def _raw_table(headers: list, rows: list) -> str:
    """Fallback table format."""
    lines = []
    if len(headers) > 1 and len(rows) > 1:
        lines.append(" | ".join(h[:15] for h in headers))
        lines.append("-" * len(lines[0]))
    for row in rows:
        vals = [str(v)[:25] if v else "-" for v in row]
        lines.append(" | ".join(vals))
    result = "\n".join(lines)
    if len(result) > 3800:
        result = result[:3800] + "\n... (обрезано)"
    return result


def format_result(question: str, sql: str, headers: list, rows: list, error: str) -> str:
    """Format query result for Telegram."""
    if error:
        return f"❌ Ошибка: {error}"

    if not rows:
        return "🔍 Ничего не найдено."

    return summarize_result(question, headers, rows)


# ── Bot handlers ────────────────────────────────────────
FFMPEG_PATH = "/tmp/ffmpeg"

async def transcribe_voice(file_path: str) -> str:
    """Convert ogg to wav and transcribe using Google Speech Recognition."""
    import subprocess, tempfile, asyncio
    import speech_recognition as sr

    wav_path = file_path + ".wav"
    try:
        # ffmpeg conversion (sync but fast)
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", file_path, "-ac", "1", "-ar", "16000", wav_path],
            capture_output=True, timeout=15
        )
        # Run blocking speech recognition in thread
        loop = asyncio.get_event_loop()
        
        def _recognize():
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_google(audio, language="ru-RU")
        
        text = await loop.run_in_executor(None, _recognize)
        return text
    except Exception as e:
        print(f"Voice error: {e}")
        return ""
    finally:
        for p in [wav_path]:
            if os.path.exists(p):
                os.remove(p)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚂 **Вагонный парк БОТ**\n\n"
        "Спроси меня текстом или голосовым сообщением:\n"
        "• Сколько полувагонов в рабочем парке?\n"
        "• Вагон 63596241\n"
        "• Топ-10 собственников\n"
        "• Порожние цистерны УВЗ старше 20 лет\n"
        "• Неисправные вагоны на дороге ЗСБ"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return
    await process_query(update, question)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages — download, transcribe, query."""
    voice = update.message.voice
    if not voice:
        return

    await update.message.chat.send_action("typing")
    
    # Download voice file
    file = await voice.get_file()
    ogg_path = f"/tmp/wagon_voice_{update.message.message_id}.ogg"
    await file.download_to_drive(ogg_path)
    
    # Transcribe
    text = await transcribe_voice(ogg_path)
    if os.path.exists(ogg_path):
        os.remove(ogg_path)
    
    if not text:
        await update.message.reply_text("🎤 Не удалось распознать речь. Попробуйте текстом.")
        return
    
    # Echo what was understood
    await update.message.reply_text(f"🎤 *{text}*", parse_mode="Markdown")
    
    # Process the query
    await process_query(update, text)


async def process_query(update: Update, question: str):
    """Run the full SQL→Execute→Summarize pipeline."""
    await update.message.chat.send_action("typing")
    
    sql = generate_sql(question)
    if sql.startswith("ERROR:"):
        await update.message.reply_text(f"❌ Ошибка генерации SQL: {sql}")
        return
    
    headers, rows, error = execute_sql(sql)
    result = format_result(question, sql, headers, rows, error)
    await update.message.reply_text(result)


# ── Main ────────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        print("ERROR: WAGONS_BOT_TOKEN not set in .env")
        print("Create a bot via @BotFather and add:")
        print('  WAGONS_BOT_TOKEN=your_token_here')
        print(f"  to {ENV_PATH}")
        sys.exit(1)
    if not DEEPSEEK_KEY:
        print("ERROR: DeepSeek API key not found in Hermes config")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("🚂 WagonBot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

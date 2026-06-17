# Watchdog-паттерн для процессов через cron

Когда нужно, чтобы процесс (бот, сервер, скрипт) не падал бесследно.

## Инструменты

| Инструмент | Применение |
|---|---|
| `cronjob(no_agent=True)` | Без LLM — чистый запуск скрипта по расписанию |
| `deliver="local"` | Результат watchdog'а не нужен пользователю |
| `nohup` + `&` | Отвязать процесс от cron-сессии |
| PID-файл | Отслеживать живой процесс между тиками |

## Шаблон watchdog-скрипта

```bash
#!/bin/bash
BOT_SCRIPT="/path/to/bot.py"
PID_FILE="/path/to/bot.pid"
LOG_FILE="/path/to/bot.log"

# Если --force — убить и перезапустить
if [ "$1" = "--force" ]; then
    [ -f "$PID_FILE" ] && kill $(cat "$PID_FILE") 2>/dev/null
    pkill -f "bot.py" 2>/dev/null
    sleep 1
fi

# Проверить, жив ли
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    exit 0  # жив
fi

# Запустить
nohup python3 "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
```

## Два cron-джоба

| Джоб | Расписание | Скрипт |
|---|---|---|
| Watchdog | `*/5 * * * *` | `watchdog.sh` |
| Принуд. рестарт | `0 20 * * *` (3:00 МСК) | `watchdog.sh --force` |

## Важно

- Скрипт должен лежать в `~/.hermes/scripts/` (cron требует относительный путь)
- `deliver="local"` — результат не уходит пользователю
- При пустом stdout бот жив и молчит — это норма
- При не-нулевом exit code cron присылает алерт

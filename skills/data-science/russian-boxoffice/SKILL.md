---
name: russian-boxoffice
title: Russian Box Office Data (ЕАИС / Кинопоиск)
description: Parse, format, and schedule daily/weekly/monthly box office reports from ЕАИС (Фонд кино) and Кинопоиск. Fetch top-10 daily gross, weekend summaries, premieres, and monthly schedules. Publish to Telegram channels.
category: data-science
version: 1.0.0
icon: 🎬
author: Hermes Agent
created: 2026-06-15
---

# Skill: Russian Box Office Data (ЕАИС / Фонд кино)

Parse Russian box office data from ЕАИС (Фонд кино) and Кинопоиск, format reports, and schedule recurring publications.

## Data Sources

### 1. ЕАИС (Фонд кино) — Топ-20 сборов

**Страница статистики (требует браузер для полных дневных данных):**
`https://ekinobilet.fond-kino.ru/statistics/`

Таблица «ТОП — 20 по России» содержит за день: позиция, название, сборы (₽), зрители, сеансы, средние сборы, залы, доля.

**JSON-эндпоинт (все фильмы, исторические данные):**
`https://ekinobilet.fond-kino.ru/ekb/top-films/`

Возвращает полный массив фильмов с полями:
- `title`, `title_en` — название
- `dsum` — дневные сборы (часто 0 — обновляются с задержкой)
- `sum` — сумма за выбранный период (тоже 0 на общей странице)
- `money` — общие сборы за всё время
- `tickets` — общее число зрителей
- `quantity` — зрители за день
- `sessions` — сеансы за день
- `launch_date` — дата премьеры
- `genre`, `country`, `distributor`, `ageRestr`
- `firstWeekendSales` — сборы первого уикенда

**Headers для запроса:**
```
X-Requested-With: XMLHttpRequest
Referer: https://ekinobilet.fond-kino.ru/statistics/
User-Agent: Mozilla/5.0 (...)
Cookie: _language=ru
```

**Ограничение:** `/statistics/api/top20` эндпоинт требует авторизации (возвращает пустоту без сессии). Используй `/ekb/top-films/` вместо него для bulk-данных, а для дневных цифр — браузерный парсинг страницы статистики.

### 2. Кинопоиск — премьеры
`https://www.kinopoisk.ru/premiere/`

Страница с предстоящими премьерами. Названия фильмов, даты, жанры. Рендерится через JS — нужен браузер.

## Workflow: Daily Top-10 via Browser

When browser tools are available, the most reliable approach:

1. `browser_navigate` to `https://ekinobilet.fond-kino.ru/statistics/`
2. Wait for page load
3. `browser_snapshot` — find the "ТОП — 20 по России" table
4. Extract from snapshot: position (1-10), film title (from link text), gross (₽), viewer count
5. Format and deliver

## Workflow: Daily Top-10 via curl/JSON

When browser isn't available or speed matters for bulk processing:

1. Fetch `/ekb/top-films/` via curl
2. Filter films where `dsum > 0` (has daily data)
3. Sort by `dsum` descending
4. Take top 10

```python
import urllib.request, json

url = 'https://ekinobilet.fond-kino.ru/ekb/top-films/'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://ekinobilet.fond-kino.ru/statistics/'
})
films = json.loads(urllib.request.urlopen(req).read())
daily = sorted([f for f in films if f.get('dsum', 0) > 0], key=lambda f: f['dsum'], reverse=True)
```

**Pitfall:** `dsum` is often 0 for all films. The daily figures are server-rendered on the statistics page and not exposed via a public JSON API. When `dsum` is all zeros, **must use browser** to get daily data.

## Report Formats

### Daily Top-10
```
🎬 Кассовые сборы РФ за 14.06.2026

🥇 Холоп 3
   💰 74 301 133 ₽ | 👥 144 440 зрителей
...

💰 Сумма топ-10: 219 000 000 ₽
👥 Всего зрителей топ-10: ...
📊 ЕАИС (Фонд кино)
```

### Weekend Summary
```
📊 Итоги уикенда

🥇 Холоп 3 — 74 301 133 ₽
🥈 МАЙКЛ — 64 589 856 ₽
...
📈 Анализ: ...
```

### Today's Premieres
```
🎬 Премьеры сегодня (17.06.2026)

• Название — жанр (страна) [возраст+]
```

### Week Premieres
```
📅 Премьеры недели

• Название — жанр (страна)
   📅 19.06.2026
```

### Monthly Premieres
```
📋 Все премьеры июня

• Название — жанр (страна)
   📅 19.06.2026
```

## Cron Scheduling

Use `cronjob(action='create')` with these parameters:

| Purpose | Schedule (МСК) | Cron schedule (ET) | Toolsets |
|---------|---------------|-------------------|----------|
| Daily top-10 | 09:00 | `0 2 * * *` | browser |
| Week premieres (Mon) | 08:00 | `0 1 * * 1` | browser |
| Weekend summary (Mon) | 10:00 | `0 3 * * 1` | browser |
| Today premieres (Thu) | 07:00 | `0 0 * * 4` | browser |
| Month premieres (1st) | 08:00 | `0 1 1 * *` | browser |

**Critical:** Cron scheduler runs in America/New_York (UTC-4 summer). Schedule MUST be in ET, NOT MSK. MSK = ET + 7 hours (summer). Система НЕ авто-конвертирует из МСК в ET — вычитай 7 часов вручную.

**Important:** Cron jobs run in their own session with no conversation context. The prompt must be fully self-contained — include the exact URL, the parsing approach, and the format template.

## Правило публикации

**Все посты в канал — только чистый контент.** Никаких служебных пометок, «вот сводка», «готово», технических заголовков. Только цифры и текст, как будто автор написал сам.

## Pitfalls

1. **ЕАИС блокирует curl** — страница статистики `/statistics/` проверяет cookie/сессию. При curl-запросе возвращает пустой HTML или страницу с робот-проверкой. Используй браузер (browser_navigate).
2. **JSON-эндпоинт `/ekb/top-films/`** — содержит полный каталог фильмов с историческими сборами (`money` = всё время, `tickets` = общие зрители). Дневные данные (`dsum`, `quantity`) часто = 0 (обновляются с задержкой или доступны только на SSR-странице). Браузерный парсинг дневных сборов — единственный надёжный способ.
3. **ЕАИС SSR-страница** — таблица «ТОП — 20 по России» рендерится сервером (Yii2 framework). Данные встроены в HTML. Парсить через browser_snapshot (accessibility tree), который выдаёт читаемые строки: позиция, название (link), сборы, зрители, сеансы, средние, залы, доля. Пример разбора строки из snapshot: `"1" → link "Холоп 3" → "35 034 743" → "79 168" → "6 881" → "5 092" → "12" → "30.37" → "%" → "34.52" → "%"` — поля: позиция, название, сборы (₽), зрители, сеансы, средние сборы, залы, доля сборов %, доля зрителей %.
4. **DuckDuckGo Lite** — блокирует частые запросы с одного IP. Для поиска премьер используй браузер → Кинопоиск напрямую.
5. **Кинопоиск может быть недоступен** — `net::ERR_SOCKET_NOT_CONNECTED`. Используй альтернативные источники или пропускай премьеры при недоступности.
6. **macOS grep** — без флага `-P`. Используй `-E` для расширенных regex.
7. **Telegram deliver target resolution** — при создании cron-задачи target типа `telegram:НазваниеКанала` резолвится по username канала. Если канал НЕ отображается в `send_message(action='list')`, значит бот не получал update из канала. Решения (в порядке предпочтения):
   - (a) **Создать новый канал** в Telegram, добавить бота админом → написать в канале любое сообщение → канал появится в send_message list
   - (b) **Добавить бота как участника, не только админа:** открыть канал → ... (три точки) → Add Member / Добавить участника → @gera_boris_1_bot. Простое добавление админом НЕ даёт update — бот должен быть участником канала. Если кнопка Add Member недоступна в публичном канале, создать приватный.
   - (c) **Проверить через скриншот:** если бот не видит канал после всех действий, попросить пользователя прислать скриншот канала → использовать easyocr для извлечения названия/@username для проверки. EasyOCR хорошо распознаёт @username в шапке канала.
   - (d) **Использовать HTTP Bot API напрямую** с токеном для определения chat_id
   - (e) Последний резерв: отправить в `origin` (текущий чат пользователя), потом обновить deliver
   - Приватные пригласительные ссылки (t.me/+...) не дают chat_id напрямую — их нужно активировать через бота
   - **Если канал упорно не подключается:** удалить все созданные cron-задачи и канал, создать новый чистовой канал, добавить бота админом, написать в канале, проверить send_message list, создать задачи заново с правильным deliver
   - **Для существующего канала @kassakino:** chat_id = `-1004313130186`, токен бота в `~/.hermes/profiles/boris/.env` как `TELEGRAM_BOT_TOKEN`. Отправка через `send_message(target="telegram:-1004313130186", ...)`. Удаление сообщений — итерацией message_id через Bot API `deleteMessage`. См. `references/telegram-channel-management.md`.
8. **Cron time zones** — scheduler работает в America/New_York (UTC-4 летом). Schedule задаётся в ET, не в MSK. MSK = ET + 7 часов летом. Пример: чтобы задача сработала в 09:00 МСК, пиши `0 2 * * *` (2 AM ET = 9 AM MSK). Система НЕ авто-конвертирует.
9. **cron-задачи без контекста** — промпт должен быть самодостаточным: URL, инструкция по парсингу, формат вывода. Никаких «как я в прошлый раз делал» — задача не видит историю чата.
10. **Чистый контент в канал** — при публикации любых сводок в @kassakino (и любые другие сторонние каналы) — только содержательная часть. Никаких «вот пост», «результат», «держи», служебных заголовков, маркеров сессий.

## Related Skills

- `model-orchestration` — правила выбора модели и чистого контента для сторонних каналов
- `nutriciolog-eliseeva` — nutrition protocol (related: the user is an actor/producer who also runs a box office channel)
- `osint-person` — public person profile collection

## References

- `references/telegram-channel-management.md` — управление каналом @kassakino: chat_id, удаление/отправка сообщений, права бота
- `references/cron-jobs-config.md` — конфигурация cron-задач

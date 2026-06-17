# Пример досье: Мягков Борис Анатольевич

Данные собраны 15 июня 2026 года. Этот файл — рабочий пример того, как выглядит полное досье после выполнения workflow osint-person.

## Исходный запрос
Пользователь: «собери про меня подробную информацию в интернете, все мои интервью, подкасты, статьи на всех сайтах, про спорт, кино, работу»

## Ключевые источники, которые сработали
1. **DuckDuckGo Lite** (без JS) — основной поисковик
   - Использовать: `https://lite.duckduckgo.com/lite?q=ФИО`
2. **Peoples.ru** — хорошая биография, раскрыта полностью через browser_navigate
   - Пример: `https://www.peoples.ru/art/cinema/actor/boris_myagkov/`
3. **24SMI.org** — отличная детальная биография с фильмографией
   - Пример: `https://24smi.org/celebrity/405549-boris-miagkov.html`
4. **YouTube** — поиск через browser работал, accessibility tree показывал все названия видео
   - URL: `https://www.youtube.com/results?search_query=ИМЯ+ФАМИЛИЯ+интервью`
5. **ilovesupersport.ru** — специализированное спортивное интервью
   - Работало через browser_navigate
6. **Рамблер/женский, Совспорт** — найдены через DuckDuckGo

## Блокировки
- **kino-teatr.ru** — CAPTCHA, не прошёл
- **kinopoisk.ru** — ERR_SOCKET_NOT_CONNECTED (региональная блокировка?)
- **afisha.ru** — пустая страница (bot detection)

## Структура итогового отчёта (Telegram-friendly)
- Без таблиц (Telegram не поддерживает pipe-синтаксис)
- Markdown: **жирный**, *курсив*, `код`
- Использовать MEDIA: только для доставки файлов
- Секции с эмодзи-заголовками для наглядности

## Технические заметки
- macOS grep: нет `-P`, только `-E`
- DuckDuckGo Lite парсинг: ссылки в формате `//duckduckgo.com/l/?uddg=URL`
- Для распарсивания: `grep -oE 'uddg=[^&"]+'` + `python3 -c "import sys,urllib.parse; print(urllib.parse.unquote(...))"`

КРИТИЧНО: send_message(target="telegram") → Home-канал, НЕ DM. Для диалога — без target. Никогда не слать личное в Home-канал.
§
ОРКЕСТРАЦИЯ (НЕ НАРУШАТЬ): всё через OpenRouter. Креатив/дизайн → spawn claude-sonnet-4.6. Кодинг → devstral-2512. Поиск/vision → gemini-3.1-flash-lite. Сложный анализ → claude-opus-4.8. Изображения: 🥇 Nano Banana (google/gemini-2.5-flash-image), 🥈 GPT/SORA (openai/gpt-5-image). Спавн: `hermes chat --model X --provider openrouter -q "..."`. delegate_task НЕ подчиняется оркестрации.
§
ВАЖНО: при отправке контента в ЛЮБЫЕ сторонние каналы (не только @kassakino) — только содержательная часть, без рабочих/машинных пометок. Никаких «вот пост», «результат», «держи», «готово», служебных заголовков, маркеров сессий. Чистый человеческий контент — как будто автор написал сам.
§
Календарь: ВСЕ операции в МСК (UTC+3). Mac в America/New_York (ET, UTC-4). При создании событий через osascript вычитать 7ч из МСК (12:30 МСК → 05:30 ET). AppleScript date string "MM/DD/YYYY HH:MM:SS" работает. Календарь по умолчанию «Рабочий», спорт — «Тренировки». iCloud Calendar не настроен — все календари локальные, на iPhone не синхронизируются. При [local] создавать .ics-файл и отправлять пользователю.
§
Нутрициолог: навыки nutriciolog-coach + nutriciolog-eliseeva. Трекер: $HERMES_HOME/data/daily_tracker.py. Cron: еда */15 4-18 (99ff), чекин 22:00 МСК = 0 19 ET (7430). Фото еды → meal + status обязательно. Вода 2л, шаги 15к.
§
Бот @Wagon_Analit_Bot: wagon_bot.py + wagons.db (1.77M вагонов). NL→SQL→NL через DeepSeek. Watchdog: cron каждые 5 мин (77d0e5bcde71) + принудительный рестарт раз в сутки в 20:00 ET (63f47ca2f8dd). Всё в $HERMES_HOME/scripts/ и data/.
§
Vercel: токен VERCEL_TOKEN в .env. Деплой: python3 scripts/deploy_vercel.py (статический index.html). Проект "oshibana" (prj_e0jFdfnNUu5pIHQr3K21RnEm3XLj) на oshibana-7651050-boris-projects.vercel.app. Контекст7: mcp установлен в Hermes-venv, ждёт рестарта.
§
ЗАПРЕТ: text_to_speech НИКОГДА. Борис ненавидит голосовые ответы агента — только текст.
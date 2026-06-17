---
name: vercel-deploy
description: "Деплой статических сайтов на Vercel через REST API. Однофайловые лендинги, HTML/CSS/JS — создание проекта, загрузка, отключение SSO, получение URL."
version: 1.0.0
category: software-development
---

# Vercel Deploy

Деплой статических сайтов (HTML/CSS/JS) на Vercel через REST API. Не требует Vercel CLI, работает через `urllib` + Bearer-токен.

## Когда использовать

- После вёрстки лендинга/сайта — быстрый деплой на Vercel
- Однофайловые проекты (index.html со встроенными стилями и скриптами)
- Когда Vercel CLI не установлен или недоступен

## Предварительные требования

- `VERCEL_TOKEN` в `.env` (создать: https://vercel.com/account/tokens)
- Python 3.9+ (только stdlib: `urllib`, `json`, `base64`)

## Быстрый деплой

```bash
export VERCEL_TOKEN=***
python3 scripts/deploy_vercel.py
```

Скрипт автоматически:
1. Находит или создаёт проект на Vercel
2. Отключает SSO-защиту (чтобы сайт был публичным)
3. Загружает index.html и создаёт production-деплой
4. Выводит URL

## Питфоллы

- **SSO-защита** включена по умолчанию на новых проектах Vercel. Без её отключения сайт требует логин. Скрипт отключает автоматически через `PATCH /v9/projects/{id}` с `{"ssoProtection": null}`.
- **Токен в коде**: НИКОГДА не хардкодить токен в Python-файлах. Инструменты Hermes маскируют токены как `***`, что ломает синтаксис. Всегда читать из env или .env.
- **Фреймворк**: для статических сайтов передавать `"framework": null` в настройках проекта, иначе Vercel пытается определить фреймворк и может ошибиться.
- **Первый деплой**: создать проект (`POST /v9/projects`), затем деплой (`POST /v13/deployments`). Не пытаться деплоить без проекта.

## API reference

| Endpoint | Method | Назначение |
|---|---|---|
| `/v9/projects` | GET | Список проектов |
| `/v9/projects` | POST | Создать проект |
| `/v9/projects/{id}` | PATCH | Обновить настройки (SSO) |
| `/v13/deployments` | POST | Создать деплой с файлами |

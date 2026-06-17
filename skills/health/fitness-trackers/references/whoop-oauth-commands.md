# Whoop OAuth — выученные уроки

## Сценарий: пользователь на телефоне, агент на Mac

Когда пользователь не может сидеть за машиной с агентом, OAuth-флоу выглядит так:

1. **Агент** генерирует `state` + auth URL на своей машине
2. **Агент** отправляет URL пользователю в Telegram
3. **Пользователь** открывает на телефоне, авторизуется
4. Браузер редиректит на `localhost:3002` → на телефоне это не работает
5. **Пользователь** копирует URL из адресной строки и вставляет в чат
6. **Агент** извлекает код из URL и обменивает

## Проблема с сервером на port 3002

```
lsof -ti:3002 | xargs kill -9     # освободить порт
# или
pkill -f callback_server
```

Запускать сервер надо **только** если пользователь на той же машине. Если пользователь на телефоне — сервер не нужен.

## Ошибка 403 error code 1010

Whoop отклоняет обмен кода на токен с этой ошибкой. Причины (по убыванию вероятности):

1. **Код истёк** (~2 минуты TTL). Если прошло больше минуты между генерацией и обменом — код мёртв.
2. **Rate limit**. Whoop не документирует лимиты, но после 2-3 неудач подряд нужно подождать 30-60 секунд.
3. **Scopes не подтверждены в dashboard**. Мало передать scopes в URL — они должны быть отмечены в настройках приложения.

## Проблема с redirect URI на телефоне

Когда Whoop редиректит на `http://localhost:3002/callback`:
- **На телефоне**: браузер показывает ошибку "Страница недоступна"
- **Пользователь**: копирует URL из адресной строки
- **Внимание**: на iPhone адресную строку Safari нужно раскрыть (свайп вниз), чтобы увидеть полный URL. На Android — просто нажать на URL.

## Скрипт обмена кода на токены

Писать скрипт в файл, а не в inline-команду:

```bash
python3 /tmp/whoop_exchange.py
```

Inline с кавычками, словарями и f-строками ломает bash. Пример рабочего файла:

```python
import urllib.request, urllib.parse, json

CLIENT_ID = '...'
CLIENT_SECRET = '...'
CODE = '...'  # из URL
REDIRECT_URI = 'http://localhost:3002/callback'

token_data = {
    'grant_type': 'authorization_code',
    'code': CODE,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI
}

data = urllib.parse.urlencode(token_data).encode()
req = urllib.request.Request(
    'https://api.prod.whoop.com/oauth/oauth2/token',
    data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
try:
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())
        print(json.dumps(tokens, indent=2, ensure_ascii=False))
        with open('/tmp/whoop_tokens.json', 'w') as f:
            json.dump(tokens, f, indent=2)
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()}")
```

## EasyOCR и homoglyphs

При OCR-распознавании credentials возможны подмены:

- `а` (кир.) вместо `a` (лат.) — в Client ID
- `е` (кир.) вместо `e` (лат.) — в Client Secret
- `о` (кир.) вместо `o` (лат.)
- `с` (кир.) вместо `c` (лат.)
- `g` вместо `9`, `b` вместо `6`

Скриншот → OCR → копирование → вставка → 401 invalid_client.

**Решение**: просить пользователя скопировать credentials через Cmd+C / кнопку Copy на сайте, а не через скриншот.

## Пароли приложений Apple iCloud

Для CalDAV через iCloud нужен пароль приложения, созданный именно для **iCloud** (не для Mail!). Если создать для Mail — будет 403 на `caldav.icloud.com/`.

Проверить тип пароля: зайти на https://appleid.apple.com → Sign-In & Security → App-Specific Passwords → посмотреть описание.

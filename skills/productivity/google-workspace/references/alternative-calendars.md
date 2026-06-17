# Альтернативные календари (не Google)

## Apple iCloud CalDAV

### Требуется
1. Apple ID
2. **Пароль приложения для iCloud** (не Mail!)
   - Создать: https://appleid.apple.com → Sign-In & Security → App-Specific Passwords
   - Выбрать тип: **iCloud** (только для iCloud, не Mail)
3. CalDAV URL: `https://caldav.icloud.com/`

### Пароль приложения
Если пароль создан не для того сервиса:
- Пароль для **Mail** → работает для IMAP/SMTP почты
- Пароль для **iCloud** → работает для CalDAV + CardDAV
- Если создать для Mail и пытаться подключить CalDAV → **HTTP 403**

### Проверка
```bash
# Проверить аутентификацию
curl -v -u "email@icloud.com:app-specific-password" \
  "https://caldav.icloud.com/" 2>&1 | grep "HTTP/"
# Должен быть 200 или 4xx (если 403 — пароль не того типа)
```

### Библиотека caldav (Python)
```bash
pip3 install caldav
```

```python
import caldav
client = caldav.DAVClient(
    url="https://caldav.icloud.com/",
    username="email@icloud.com",
    password="app-specific-password"
)
principal = client.principal()
calendars = principal.calendars()
for cal in calendars:
    print(cal.name, cal.url)
```

### Ограничения
- EventKit/macOS Calendar на этой машине недоступен через Hermes, так как:
  - Нет активной GUI-сессии пользователя
  - `osascript tell application "Calendar"` зависает
  - База SQLite календарей защищена macOS-песочницей (Operation not permitted)
- Через CalDAV (сетевой протокол) всё работает без GUI

## Яндекс.Календарь (CalDAV)

### Требуется
1. Яндекс-аккаунт
2. **Пароль приложения** (создать на https://id.yandex.ru/security → Пароли приложений)
3. CalDAV URL: `https://caldav.yandex.ru/`

### Проверка
```bash
curl -v -u "login@yandex.ru:app-password" \
  "https://caldav.yandex.ru/"
```

## macOS Calendar.app (локальный, системный)

**Не работает** через Hermes без активного GUI-сеанса. 
EventKit требует macOS sandbox entitlement, который есть только у нативных приложений.
osascript к Calendar.app зависает, если приложение не запущено или нет GUI.

## Рекомендация

Для автоматизации с Hermes использовать **сетевой CalDAV** (iCloud, Яндекс) или **Google Calendar API** (через google-workspace skill + OAuth).

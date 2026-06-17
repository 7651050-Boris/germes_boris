# Управление Telegram-каналом @kassakino

## Идентификаторы

- **Канал:** @kassakino = «Кассовые сборы»
- **Chat ID:** `-1004313130186`
- **Бот:** @gera_boris_1_bot (администратор канала, права: post + delete)
- **Токен бота:** `TELEGRAM_BOT_TOKEN` в `~/.hermes/profiles/boris/.env`

## Отправка сообщений

Через Hermes `send_message`:
```
send_message(target="telegram:-1004313130186", message="...")
```

Цель вида `telegram:Кассовые сборы` НЕ резолвится. Всегда использовать chat_id.

Через Bot API напрямую:
```python
url = f"https://api.telegram.org/bot{token}/sendMessage"
data = {"chat_id": "-1004313130186", "text": "..."}
```

## Удаление сообщений

Бот имеет права `can_delete_messages: true`. Удаление — итерацией по message_id:

```python
for msg_id in range(1, 100):
    url = f"https://api.telegram.org/bot{token}/deleteMessage?chat_id={chat_id}&message_id={msg_id}"
    # Успех если ok=True, ошибка "not found" — сообщения с таким ID нет
```

**Важно:** бот НЕ получает updates из канала (getUpdates пуст для channel_post). Это известная проблема @kassakino. Единственный способ узнать message_id — угадывать итерацией либо знать ID из предыдущих send_message.

## Закрепление сообщений

```python
url = f"https://api.telegram.org/bot{token}/pinChatMessage?chat_id={chat_id}&message_id={msg_id}&disable_notification=true"
```

## Проверка прав бота

```python
url = f"https://api.telegram.org/bot{token}/getChatMember?chat_id={chat_id}&user_id={bot_user_id}"
```

## Правило чистого контента

При публикации в канал — **только содержательная часть**. Никаких служебных пометок, «вот пост», «результат», маркеров сессий. Чистый человеческий контент.

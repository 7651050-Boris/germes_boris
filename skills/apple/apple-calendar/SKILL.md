---
name: apple-calendar
description: "Manage Apple Calendar via osascript: list, create, edit, delete events across all calendars."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Calendar, Apple, macOS, events, scheduling, iCal]
    related_skills: [apple-reminders]
prerequisites:
  commands: [osascript]
---

# Apple Calendar

Use `osascript` (built-in on macOS) to manage Apple Calendar events. Changes sync via iCloud to iPhone/iPad.

Available calendars on this Mac: **Тренировки, Рабочий, Семья, mba.rzd@gmail.com** (plus system: Дни рождения, Праздники, Предложения Siri).

**Timezone: always use Europe/Moscow (UTC+3).** All event times are interpreted and created in Moscow time. Calendar.app is configured with `TimeZone = Europe/Moscow`.

## When to Use

- User asks to add, view, edit, or delete calendar events
- Scheduling meetings, workouts, family events
- Checking what's on the schedule for a day/week
- Events that should sync to iPhone/iPad

## When NOT to Use

- Simple personal to-dos without a time → use apple-reminders instead
- Agent-triggered alerts → use the cronjob tool instead
- Google Calendar via web → use browser_tool unless user wants Mac Calendar sync

## User Preference

**ВСЕ события, встречи и напоминания — только в Календарь (Calendar.app). Никогда не использовать Напоминания (Reminders) или Заметки (Notes), если пользователь явно не попросил другое приложение.** Если задача звучит как «напомни» — всё равно создавать событие в Календаре.

## FORBIDDEN

**Do not create .ics files when Calendar.app iCloud sync is available.** Events created via osascript sync to iPhone automatically. If all calendars are local, use the iCloud Sync Troubleshooting fallback below and send .ics only to the originating DM.

## Allowed write calendars

Доступные календари (полный список через `osascript -e 'tell application "Calendar" to get name of calendars'`): Тренировки, Рабочий, Семья, Дни рождения, Запланированные напоминания, Предложения Siri, mba.rzd@gmail.com.

**Все календари доступны для записи**, включая Дни рождения (проверено: событие успешно создано). Системные календари (Праздники, Предложения Siri) — только чтение.

Default writable calendar: **Рабочий** для рабочих встреч, **Дни рождения** для празднований и дней рождений.

## Calendar routing rules

Use **Тренировки** automatically when the event involves:
- Sport, physical activity, fitness: gym, run, swim, bike, yoga, workout, football, basketball, tennis, ski, boxing, CrossFit, тренировка, зал, бег, плавание, велосипед, йога, футбол, баскетбол, теннис, лыжи, бокс
- Nutrition and diet planning tied to a time slot: meal prep, диета, питание, приём пищи, завтрак/обед/ужин if scheduled as a planned event (not a social lunch — see Семья rule)

Use **Семья** for social meals/events with family members.
Use **Рабочий** for everything else (meetings, calls, tasks).

---

## Quick Reference

### List all calendars

```bash
osascript -e 'tell application "Calendar" to get name of every calendar'
```

### List today's events

```bash
osascript <<'EOF'
tell application "Calendar"
    set d to current date
    set s to d - (time of d)
    set e to s + (23 * hours + 59 * minutes + 59)
    set out to {}
    repeat with c in (every calendar)
        repeat with ev in (every event of c whose start date ≥ s and start date ≤ e)
            set end of out to (summary of ev) & " | " & (start date of ev as string) & " → " & (end date of ev as string) & " [" & (name of c) & "] uid:" & (uid of ev)
        end repeat
    end repeat
    return out
end tell
EOF
```

### List events for a specific date (e.g. 2026-06-20)

```bash
osascript <<'EOF'
tell application "Calendar"
    -- Build target date
    set td to current date
    set year of td to 2026
    set month of td to 6
    set day of td to 20
    set time of td to 0
    set te to td + (23 * hours + 59 * minutes + 59)
    set out to {}
    repeat with c in (every calendar)
        repeat with ev in (every event of c whose start date ≥ td and start date ≤ te)
            set end of out to (summary of ev) & " | " & (start date of ev as string) & " → " & (end date of ev as string) & " [" & (name of c) & "] uid:" & (uid of ev)
        end repeat
    end repeat
    return out
end tell
EOF
```

### List events for a date range (e.g. this week)

```bash
osascript <<'EOF'
tell application "Calendar"
    set s to current date
    set time of s to 0
    set e to s + (7 * days)
    set out to {}
    repeat with c in (every calendar)
        repeat with ev in (every event of c whose start date ≥ s and start date ≤ e)
            set end of out to (summary of ev) & " | " & (start date of ev as string) & " [" & (name of c) & "] uid:" & (uid of ev)
        end repeat
    end repeat
    return out
end tell
EOF
```

### Search events by keyword

```bash
osascript <<'EOF'
tell application "Calendar"
    set kw to "встреча"   -- replace with search term
    set s to current date
    set time of s to 0
    set e to s + (30 * days)
    set out to {}
    repeat with c in (every calendar)
        repeat with ev in (every event of c whose start date ≥ s and start date ≤ e and summary contains kw)
            set end of out to (summary of ev) & " | " & (start date of ev as string) & " [" & (name of c) & "] uid:" & (uid of ev)
        end repeat
    end repeat
    return out
end tell
EOF
```

---

### Create an event

```bash
osascript <<'EOF'
tell application "Calendar"
    tell calendar "Рабочий"
        -- Set start date: 2026-06-20 14:30
        set sd to current date
        set year of sd to 2026
        set month of sd to 6
        set day of sd to 20
        set time of sd to (14 * hours + 30 * minutes)
        -- Set end date: 2026-06-20 15:30
        set ed to sd + 1 * hours
        set newEv to make new event with properties {¬
            summary:"Встреча с командой", ¬
            start date:sd, ¬
            end date:ed, ¬
            location:"Офис, переговорная 2", ¬
            description:"Обсуждение Q3 плана"}
        -- Optional: add 15-minute alert
        make new display alarm at newEv with properties {trigger interval:-15}
        return "Created: " & (uid of newEv)
    end tell
end tell
EOF
```

**Fields:**
- `summary` — название (обязательно)
- `start date` / `end date` — начало и конец
- `location` — место (необязательно)
- `description` — заметки (необязательно)
- `trigger interval:-15` — уведомление за N минут до начала

### Create an all-day event

```bash
osascript <<'EOF'
tell application "Calendar"
    tell calendar "Семья"
        set sd to current date
        set year of sd to 2026
        set month of sd to 7
        set day of sd to 4
        set time of sd to 0
        set ed to sd + (23 * hours + 59 * minutes)
        make new event with properties {¬
            summary:"День независимости", ¬
            start date:sd, ¬
            end date:ed, ¬
            allday event:true}
    end tell
end tell
EOF
```

---

### Edit an event (by uid)

First find the uid with a list command, then:

```bash
osascript <<'EOF'
tell application "Calendar"
    set targetUID to "D663AF50-7EB1-4247-B24F-F652658094B4"  -- replace
    repeat with c in (every calendar)
        repeat with ev in (every event of c)
            if uid of ev is targetUID then
                -- Change what you need:
                set summary of ev to "Новое название"
                set start date of ev to (start date of ev) + 30 * minutes
                set end date of ev to (end date of ev) + 30 * minutes
                return "Updated"
            end if
        end repeat
    end repeat
    return "Not found"
end tell
EOF
```

### Delete an event (by uid)

Do NOT delete inside a nested `repeat` — AppleScript raises -1728 when the collection shifts mid-iteration.
Use a filter (`whose uid is`) to locate the event first, then delete outside the loop:

```bash
osascript <<'EOF'
tell application "Calendar"
    set targetUID to "D663AF50-7EB1-4247-B24F-F652658094B4"  -- replace
    set foundCal to missing value
    set foundEv to missing value
    repeat with c in (every calendar)
        set evts to (every event of c whose uid is targetUID)
        if (count of evts) > 0 then
            set foundCal to c
            set foundEv to item 1 of evts
            exit repeat
        end if
    end repeat
    if foundEv is missing value then return "Not found"
    tell foundCal to delete foundEv
    return "Deleted"
end tell
EOF
```

---

## Date Construction Reference

**CRITICAL: NEVER use `date "MM/DD/YYYY"` string format — it breaks on non-US locales (Russian locale interprets as DD/MM/YYYY, causing wrong dates).**

AppleScript dates MUST be built field by field:

```applescript
set d to current date
set year of d to 2026
set month of d to 6          -- integer 1-12, not month constant
set day of d to 18
set time of d to 0           -- reset first, REQUIRED
set time of d to (14 * hours + 0 * minutes)   -- 14:00
```

Time constants: `hours` = 3600, `minutes` = 60, `days` = 86400.

---

## Rules

1. Always confirm event details (title, date, time, calendar) before creating
2. Always use **Europe/Moscow (UTC+3)** for all event times
3. When listing events, include uid in output so edits/deletes can reference it
4. Default calendar is **Рабочий** unless user specifies otherwise; use **Дни рождения** for birthdays/celebrations
5. For recurring events or complex recurrence, open Calendar.app via `open -a Calendar` — AppleScript recurrence support is limited
6. When deleting, always confirm with user first
7. After creating/editing, optionally run a list command to confirm the change took effect

## iCloud Sync Troubleshooting

**Calendar.app синхронизация с iPhone НЕ работает «из коробки».**

Проверка — есть ли iCloud-календари:

```bash
osascript -e 'tell application "Calendar"
repeat with c in (every calendar)
  try
    set acctName to name of (account of c)
  on error
    set acctName to "local"
  end try
  log (name of c) & " [" & acctName & "]"
end repeat
end tell' 2>&1
```

Если **все** календари показывают `[local]` — iCloud-синхронизация НЕ настроена. События создаются локально на Mac и не попадают на iPhone.

**Причина:** Calendar.app не подключён к iCloud-аккаунту, даже если Mac залогинен в iCloud. Системный CalDAV (MobileMeAccounts.plist) есть, но Calendar.app его не видит.

**Диагностика:**
```bash
# Проверить системный iCloud CalDAV
defaults read MobileMeAccounts 2>&1 | grep -A5 "com.apple.Dataclass.Calendars"
# Наличие записи = iCloud залогинен, но Calendar может не видеть
```

**Что делать агенту при `[local]`:**
1. Создать событие локально (для записи)
2. Сформировать `.ics`-файл и отправить пользователю — открывается на iPhone, добавляется в Календарь iOS одним тапом
3. Сообщить пользователю, что нужна однократная активация iCloud Calendar на Mac (Системные настройки → Apple ID → iCloud → Календари)

**Шаблон .ics-файла:**
```
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20260617T123000
DTEND:20260617T133000
SUMMARY:Название встречи
LOCATION:Адрес
END:VEVENT
END:VCALENDAR
```
DTSTART/DTEND всегда в местном времени пользователя (МСК), без конвертации в ET.

## Pitfalls

1. **Не использовать `tell (default calendar)`** — на русской macOS вызывает ошибку «Предполагаемый результат — конец строки; полученный — имя класса (-2741)». Всегда указывать календарь явно по имени: `tell calendar "Рабочий"`.
2. **Не использовать `tell application "Calendar" to make new event` без указания календаря** — ошибка «Не удается создать или переместить объект в контейнер (-10024)». Всегда: `tell calendar "ИМЯ" to make new event`.
3. **Формат даты в строке**: `date "MM/DD/YYYY HH:MM:SS"` — американский формат. Русские названия месяцев не работают.
4. **Не использовать `date "Wednesday, June 17, 2026 at 6:30:00 PM"`** — ошибка «Недействительная дата и время (-30720)» на русской macOS.
5. **Не использовать строковые даты даже для простых событий.** Всегда строить `current date` через `set year`, `set month`, `set day`, `set time`.
6. **Не делать двойную конвертацию времени.** Основное правило — Europe/Moscow (UTC+3); если Calendar.app уже настроен на MSK, задавать время как MSK напрямую.
7. **КРИТИЧНО: отправка .ics только в DM**: после создания .ics-файла НИКОГДА не использовать `send_message(target="telegram")` — это уходит в Home-канал (публичный). Отправлять без target (доставка `origin` — в тот же диалог). Провал 17.06: .ics с ФИО и адресом ушёл в Home-канал.
8. **После создания события проверить iCloud**: запустить проверку календарей на `[local]`. Если все локальные — сразу формировать .ics и отправлять пользователю, не ждать синхронизации.

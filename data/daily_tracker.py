#!/usr/bin/env python3
"""
Daily nutrition & activity tracker for Boris Myagkov.
Protocol: nutriciolog-eliseeva (Gina Nutrition by Marina Eliseeva).

Usage:
  python3 daily_tracker.py init                 # create today's tracker
  python3 daily_tracker.py meal <time> <desc>   # log a meal
  python3 daily_tracker.py water <ml>           # add water intake
  python3 daily_tracker.py steps <count>        # log step count
  python3 daily_tracker.py status               # show today's status
  python3 daily_tracker.py check-evening        # check if steps reported (for cron)
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

MSK = timezone(timedelta(hours=3))
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

WATER_TARGET_ML = 2000  # 1.8-2L
STEP_TARGET = 15000
MEAL_INTERVAL_HOURS = 3.5  # 3-4 hours

MEAL_ORDER = ["breakfast", "lunch", "snack", "dinner"]


def today_str():
    return datetime.now(MSK).strftime("%Y-%m-%d")


def tracker_path(date_str=None):
    if date_str is None:
        date_str = today_str()
    return os.path.join(DATA_DIR, f"tracker-{date_str}.json")


def load(date_str=None):
    path = tracker_path(date_str)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {
        "date": date_str or today_str(),
        "meals": [],
        "water_ml": 0,
        "water_log": [],
        "steps": None,
        "steps_reported": False,
        "evening_check_sent": False,
        "reminders_sent": [],  # meal names that already got a reminder
    }


def save(data):
    with open(tracker_path(data["date"]), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_init():
    data = load()
    save(data)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_meal(time_str, desc):
    data = load()
    meal_num = len(data["meals"]) + 1
    meal_name = MEAL_ORDER[meal_num - 1] if meal_num <= 4 else f"extra_{meal_num}"
    data["meals"].append({
        "num": meal_num,
        "name": meal_name,
        "time": time_str,
        "description": desc,
    })
    save(data)

    # Calculate next meal time
    next_num = meal_num + 1
    next_name = MEAL_ORDER[next_num - 1] if next_num <= 4 else None

    # Try to parse time
    try:
        hour, minute = map(int, time_str.replace(":", " ").split()[:2])
        next_hour = hour + MEAL_INTERVAL_HOURS
        next_h = int(next_hour)
        next_m = int((next_hour - next_h) * 60)
        next_time = f"{next_h:02d}:{next_m:02d}"
    except:
        next_time = "?"

    result = {
        "meal_logged": meal_name,
        "meal_number": meal_num,
        "total_meals_today": meal_num,
        "next_meal": next_name,
        "next_meal_time": next_time,
        "water_ml": data["water_ml"],
        "water_target_ml": WATER_TARGET_ML,
        "water_pct": round(data["water_ml"] / WATER_TARGET_ML * 100),
    }

    # Add meal-specific guidance
    if next_name == "breakfast":
        result["guidance"] = "Сложные углеводы с кулак (каша на воде) + фрукт/ягоды + 1 яйцо или 10 орехов"
    elif next_name == "lunch":
        result["guidance"] = "Правило тарелки: белок с ладонь + 5 ст.л. сложных углеводов + полтарелки салата (3+ овоща) + фрукт"
    elif next_name == "snack":
        result["guidance"] = "Белок с ладонь + припущенные овощи al dente полтарелки + вкусняшка (углеводистая)"
    elif next_name == "dinner":
        result["guidance"] = "Только белок с ладонь (не красное мясо). Овощи — только при сильном голоде. За 2-3 ч до сна."
    else:
        result["guidance"] = "Все 4 приёма уже должны быть сделаны. Если голоден — только вода."

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_water(ml):
    data = load()
    ml = int(ml)
    data["water_ml"] += ml
    data["water_log"].append({
        "time": datetime.now(MSK).strftime("%H:%M"),
        "ml": ml,
        "cumulative": data["water_ml"],
    })
    save(data)

    remaining = max(0, WATER_TARGET_ML - data["water_ml"])
    pct = round(data["water_ml"] / WATER_TARGET_ML * 100)

    result = {
        "added_ml": ml,
        "total_ml": data["water_ml"],
        "target_ml": WATER_TARGET_ML,
        "remaining_ml": remaining,
        "percent": pct,
        "status": "✅ Норма!" if pct >= 100 else f"Осталось {remaining} мл",
    }

    if pct >= 100:
        result["message"] = "🔥 Водная норма выполнена! Так держать."
    elif pct >= 70:
        result["message"] = "Хорошо, ещё немного."
    elif pct >= 40:
        result["message"] = "Пей дальше, ты на середине пути."
    else:
        result["message"] = "Мало воды. Ускорься — обезвоживание снижает умственную работоспособность."

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_steps(count):
    data = load()
    count = int(count)
    data["steps"] = count
    data["steps_reported"] = True
    save(data)

    diff = count - STEP_TARGET
    if diff >= 0:
        msg = f"✅ {count} шагов — отлично! +{diff} к норме. Жир горит."
    elif diff >= -2000:
        msg = f"⚠️ {count} шагов. Недобор {abs(diff)}. Уже неплохо, но завтра дожми до {STEP_TARGET}."
    elif diff >= -5000:
        msg = f"😤 {count} шагов — СЛАБО! Недобор {abs(diff)}. Ходьба — единственный прямой сжигатель жира. Завтра без отмазок."
    else:
        msg = f"🤬 {count} шагов — ЭТО ЧТО ТАКОЕ?! Ты проспал весь день? Недобор {abs(diff)}. Жир не уходит сам. Завтра {STEP_TARGET}, иначе я за себя не отвечаю."

    result = {
        "steps": count,
        "target": STEP_TARGET,
        "diff": diff,
        "message": msg,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


MEAL_GUIDANCE = {
    "breakfast": "Сложные углеводы с кулак (каша на воде) + фрукт/ягоды + 1 яйцо или 10 орехов",
    "lunch": "Правило тарелки: белок с ладонь + 5 ст.л. сложных углеводов + полтарелки салата (3+ овоща) + фрукт",
    "snack": "Белок с ладонь + припущенные овощи al dente полтарелки + вкусняшка (углеводистая)",
    "dinner": "Только белок с ладонь (не красное мясо). Овощи — только при сильном голоде. За 2-3 ч до сна.",
}


def cmd_check_meal_reminder():
    """Called by cron every 30 min. Checks if it's time to remind about next meal."""
    now = datetime.now(MSK)
    current_hour = now.hour + now.minute / 60.0

    # Don't remind before 7:30 or after 21:00
    if current_hour < 7.5 or current_hour > 21.0:
        print(json.dumps({"action": "skip", "reason": "outside_reminder_hours"}))
        return

    data = load()
    meals = data.get("meals", [])
    reminders_sent = data.get("reminders_sent", [])

    # If 4 meals already logged, nothing to remind
    if len(meals) >= 4:
        print(json.dumps({"action": "skip", "reason": "all_meals_done"}))
        return

    # Determine which meal should come next
    next_meal_idx = len(meals)  # 0=breakfast, 1=lunch, 2=snack, 3=dinner
    next_meal_name = MEAL_ORDER[next_meal_idx] if next_meal_idx < 4 else None

    if next_meal_name is None:
        print(json.dumps({"action": "skip", "reason": "all_meals_done"}))
        return

    # Already sent reminder for this meal?
    if next_meal_name in reminders_sent:
        print(json.dumps({"action": "skip", "reason": f"reminder_already_sent_{next_meal_name}"}))
        return

    # Calculate when this meal is due
    if meals:
        # Get last meal time
        last_meal = meals[-1]
        try:
            h, m = map(int, last_meal["time"].replace(":", " ").split()[:2])
            last_meal_hour = h + m / 60.0
        except:
            last_meal_hour = 0
        # Meal is due 3 hours after the last one
        due_hour = last_meal_hour + 3.0
    else:
        # No meals yet today — breakfast reminder if it's past 8:00
        due_hour = 8.0

    # Is it time? (within 30 min window after due time)
    if current_hour < due_hour:
        print(json.dumps({"action": "skip", "reason": f"not_yet_time", "due_at": f"{int(due_hour):02d}:{int((due_hour%1)*60):02d}", "now": now.strftime("%H:%M")}))
        return

    # Final re-check: did user already eat this meal?
    # Re-load in case a meal was logged between initial load and now
    data_fresh = load()
    meals_fresh = data_fresh.get("meals", [])
    if len(meals_fresh) > len(meals):
        # New meal logged since we started — skip reminder
        print(json.dumps({"action": "skip", "reason": "meal_already_logged"}))
        return

    # Time to remind!
    data["reminders_sent"].append(next_meal_name)
    save(data)

    # Calculate the interval window
    start_h = int(due_hour)
    start_m = int((due_hour % 1) * 60)
    end_h = int(due_hour + 1.0)
    end_m = int(((due_hour + 1.0) % 1) * 60)
    window = f"{start_h:02d}:{start_m:02d} – {end_h:02d}:{end_m:02d}"

    # Russian meal names
    meal_names_ru = {
        "breakfast": "ЗАВТРАК",
        "lunch": "ОБЕД",
        "snack": "ПОЛДНИК",
        "dinner": "УЖИН",
    }

    guidance = MEAL_GUIDANCE.get(next_meal_name, "")

    # Add water status
    water_pct = round(data["water_ml"] / WATER_TARGET_ML * 100)

    lines = [
        f"⏰ **Пора есть! {meal_names_ru.get(next_meal_name, next_meal_name)}**",
        "",
        f"🕐 Интервал: **{window}**",
        f"📋 {guidance}",
        f"💧 Вода: **{data['water_ml']} мл** из {WATER_TARGET_ML} мл ({water_pct}%)",
    ]

    result = {
        "action": "send",
        "meal": next_meal_name,
        "meal_ru": meal_names_ru.get(next_meal_name, next_meal_name),
        "window": window,
        "guidance": guidance,
        "water_ml": data["water_ml"],
        "water_pct": water_pct,
        "message": "\n".join(lines),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_status():
    data = load()
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_check_evening():
    """Called by cron at 22:00 MSK. Returns what to tell the user."""
    data = load()
    if data.get("evening_check_sent"):
        # Already sent today, skip
        print(json.dumps({"action": "skip", "reason": "already_sent"}))
        return

    data["evening_check_sent"] = True
    save(data)

    # Build evening summary
    meals_count = len(data["meals"])
    water_pct = round(data["water_ml"] / WATER_TARGET_ML * 100)
    steps_reported = data.get("steps_reported", False)
    steps = data.get("steps")

    result = {
        "action": "send",
        "meals_count": meals_count,
        "water_ml": data["water_ml"],
        "water_target_ml": WATER_TARGET_ML,
        "water_pct": water_pct,
        "steps_reported": steps_reported,
        "steps": steps,
        "steps_target": STEP_TARGET,
    }

    # Build the message
    lines = ["🌙 **Вечерний чек-ин — 22:00**"]
    lines.append("")
    lines.append(f"🥗 Приёмов пищи: **{meals_count}/4**")
    lines.append(f"💧 Вода: **{data['water_ml']} мл** из {WATER_TARGET_ML} мл ({water_pct}%)")

    if steps_reported and steps is not None:
        diff = steps - STEP_TARGET
        if diff >= 0:
            lines.append(f"🚶 Шаги: **{steps}** ✅ (+{diff})")
        else:
            lines.append(f"🚶 Шаги: **{steps}** ❌ (недобор {abs(diff)})")
    else:
        lines.append("🚶 Шаги: **не скинул!**")
        lines.append("")
        lines.append("😤 Скидывай шаги СЕЙЧАС. Жду.")

    result["message"] = "\n".join(lines)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage: daily_tracker.py <init|meal|water|steps|status|check-evening> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "meal":
        if len(sys.argv) < 4:
            print("Usage: daily_tracker.py meal <HH:MM> <description>")
            sys.exit(1)
        cmd_meal(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "water":
        if len(sys.argv) < 3:
            print("Usage: daily_tracker.py water <ml>")
            sys.exit(1)
        cmd_water(sys.argv[2])
    elif cmd == "steps":
        if len(sys.argv) < 3:
            print("Usage: daily_tracker.py steps <count>")
            sys.exit(1)
        cmd_steps(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    elif cmd == "check-evening":
        cmd_check_evening()
    elif cmd == "check-meal-reminder":
        cmd_check_meal_reminder()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()

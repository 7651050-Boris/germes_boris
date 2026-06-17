#!/bin/bash
# Evening check-in for Boris's nutrition & activity tracker
# Runs at 22:00 MSK (19:00 UTC) via cron
# Outputs message text if check-in is needed, empty if already done

TRACKER="/Users/boris_ai/.hermes/profiles/boris/data/daily_tracker.py"
RESULT=$(python3 "$TRACKER" check-evening 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Ошибка трекера: $RESULT"
    exit 1
fi

ACTION=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('action',''))")

if [ "$ACTION" = "send" ]; then
    echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['message'])
"
elif [ "$ACTION" = "skip" ]; then
    # Silent - already sent today
    exit 0
else
    echo "⚠️ Неизвестное действие: $ACTION"
    exit 1
fi

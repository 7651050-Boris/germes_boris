#!/bin/bash
# Meal reminder check — runs every 30 min via cron
# Checks if it's time for the next meal and sends a reminder

TRACKER="/Users/boris_ai/.hermes/profiles/boris/data/daily_tracker.py"
RESULT=$(python3 "$TRACKER" check-meal-reminder 2>/dev/null)

if [ $? -ne 0 ]; then
    exit 0  # Silent on errors
fi

ACTION=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('action',''))")

if [ "$ACTION" = "send" ]; then
    echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['message'])
"
elif [ "$ACTION" = "skip" ]; then
    # Silent — not time yet, already sent, or all meals done
    exit 0
fi

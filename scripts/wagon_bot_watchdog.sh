#!/bin/bash
# Watchdog for Wagon Analytics Bot
# Checks if bot is running; if not, starts it with nohup
# If called with --force, kills existing and restarts

BOT_SCRIPT="/Users/boris_ai/.hermes/profiles/boris/scripts/wagon_bot.py"
LOG_FILE="/Users/boris_ai/.hermes/profiles/boris/data/wagon_bot.log"
PID_FILE="/Users/boris_ai/.hermes/profiles/boris/data/wagon_bot.pid"

# Kill existing if forced
if [ "$1" = "--force" ]; then
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        kill "$OLD_PID" 2>/dev/null
        sleep 1
        kill -9 "$OLD_PID" 2>/dev/null
        rm -f "$PID_FILE"
    fi
    # Also kill any strays
    pkill -f "wagon_bot.py" 2>/dev/null
    sleep 1
fi

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        # Running — nothing to do (unless forced, already handled above)
        [ "$1" != "--force" ] && exit 0
    fi
fi

# Also check by process name
if pgrep -f "wagon_bot.py" > /dev/null 2>&1; then
    # Already running via process check
    PG_PID=$(pgrep -f "wagon_bot.py" | head -1)
    echo "$PG_PID" > "$PID_FILE"
    exit 0
fi

# Start bot
cd "$(dirname "$BOT_SCRIPT")"
nohup python3 "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"
echo "[$(date)] Watchdog started bot (PID $NEW_PID)" >> "$LOG_FILE"

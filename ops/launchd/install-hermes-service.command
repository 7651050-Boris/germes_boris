#!/bin/bash
set -euo pipefail

on_error() {
    echo
    echo "Hermes Gateway installation failed."
    read -r -p "Press Enter to close this window..."
}
trap on_error ERR

ROOT="/Users/borismagkov/Documents/New project/Hermes1"
LABEL="ai.hermes.gateway"
DOMAIN="gui/$(id -u)"
SOURCE_PLIST="$ROOT/ops/launchd/$LABEL.plist"
TARGET_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$TARGET_DIR/$LABEL.plist"

mkdir -p "$TARGET_DIR"
plutil -lint "$SOURCE_PLIST"

# Unload an older definition before replacing it. Failure is expected on first install.
launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
cp "$SOURCE_PLIST" "$TARGET_PLIST"
chmod 600 "$TARGET_PLIST"
xattr -c "$TARGET_PLIST" 2>/dev/null || true

launchctl bootstrap "$DOMAIN" "$TARGET_PLIST"
launchctl enable "$DOMAIN/$LABEL"
launchctl kickstart -k "$DOMAIN/$LABEL"

sleep 5
echo
HERMES_HOME="$ROOT/hermes-home" \
XDG_STATE_HOME="$ROOT/hermes-home/xdg-state" \
"$ROOT/.venv/bin/hermes" gateway status --deep
echo
echo "Hermes Gateway is installed with macOS autostart and automatic restart."
read -r -p "Press Enter to close this window..."

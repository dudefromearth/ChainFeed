#!/bin/bash
# -------------------------------------------------------------------
# ChainFeed Node Installer — Fail-Safe Edition
# -------------------------------------------------------------------
# - No builds, no installs, no pip
# - Just unpacks a verified ChainFeed environment snapshot
# - Registers and starts launchd service
# -------------------------------------------------------------------

set -e
set -u

echo "🚀 Installing ChainFeed Node (Fail-Safe Edition)"
echo "--------------------------------------------------"

ARCHIVE="$HOME/chainfeed_env.tar.gz"
TARGET_DIR="$HOME/ChainFeed"
LOG_DIR="$HOME/Library/Logs"
PLIST="$HOME/Library/LaunchAgents/ai.fotw.chainfeed.plist"

# 1️⃣ Check archive
if [ ! -f "$ARCHIVE" ]; then
  echo "❌ Missing archive: $ARCHIVE"
  echo "Please copy your prebuilt chainfeed_env.tar.gz here first."
  exit 1
fi

# 2️⃣ Remove any old install
if [ -d "$TARGET_DIR" ]; then
  echo "⚠️ Removing old ChainFeed installation..."
  rm -rf "$TARGET_DIR"
fi

# 3️⃣ Extract prebuilt environment
echo "📦 Extracting ChainFeed environment..."
mkdir -p "$TARGET_DIR"
tar xzf "$ARCHIVE" -C "$HOME"

# 4️⃣ Verify layout
if [ ! -f "$TARGET_DIR/core/heartbeat_startup.py" ]; then
  echo "❌ Extracted structure looks wrong. Expected $TARGET_DIR/core/heartbeat_startup.py"
  exit 1
fi
if [ ! -x "$TARGET_DIR/.venv/bin/python3" ]; then
  echo "❌ Missing virtual environment in $TARGET_DIR/.venv"
  exit 1
fi

# 5️⃣ Write launchd plist
echo "🪄 Creating launchd plist..."
mkdir -p "$LOG_DIR"
cat <<EOF > "$PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.fotw.chainfeed</string>
  <key>ProgramArguments</key>
  <array>
    <string>$TARGET_DIR/.venv/bin/python3</string>
    <string>-m</string>
    <string>core.heartbeat_startup</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$TARGET_DIR</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/ai.fotw.chainfeed.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/ai.fotw.chainfeed.err</string>
</dict>
</plist>
EOF

# 6️⃣ Load launchd
echo "🚦 Activating service..."
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo
echo "✅ ChainFeed node installed and running!"
echo "------------------------------------------"
echo "Working directory:  $TARGET_DIR"
echo "Logs:               $LOG_DIR"
echo "Service label:      ai.fotw.chainfeed"
echo
echo "🩺 To verify:"
echo "   launchctl list | grep chainfeed"
echo "   tail -f $LOG_DIR/ai.fotw.chainfeed.log"
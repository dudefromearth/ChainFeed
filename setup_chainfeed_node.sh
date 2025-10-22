#!/usr/bin/env bash
set -e

echo "🚀 Installing ChainFeed Node (Fail-Safe Edition)"
echo "--------------------------------------------------"

# --- Detect or set ChainFeed path ---
if [ -n "$CHAINFEED_HOME" ]; then
  CHAINFEED_DIR="$CHAINFEED_HOME"
elif [ -d "$HOME/PyCharmProjects/ChainFeed" ]; then
  CHAINFEED_DIR="$HOME/PyCharmProjects/ChainFeed"
elif [ -d "$HOME/ChainFeed" ]; then
  CHAINFEED_DIR="$HOME/ChainFeed"
else
  CHAINFEED_DIR="$HOME/PyCharmProjects/ChainFeed"
  mkdir -p "$CHAINFEED_DIR"
fi

echo "📂 Using ChainFeed directory: $CHAINFEED_DIR"

# --- Cleanup any prior install ---
if [ -d "$CHAINFEED_DIR" ]; then
  echo "⚠️  Removing old ChainFeed installation..."
  rm -rf "$CHAINFEED_DIR"
fi

# --- Extract archive ---
echo "📦 Extracting ChainFeed environment..."
tar -xzf "$HOME/chainfeed_env.tar.gz" -C "$(dirname "$CHAINFEED_DIR")"

# --- Verify structure ---
if [ ! -f "$CHAINFEED_DIR/core/heartbeat_startup.py" ]; then
  echo "❌ Extracted structure looks wrong. Expected $CHAINFEED_DIR/core/heartbeat_startup.py"
  exit 1
fi

echo "✅ Verified ChainFeed layout OK."

# --- Ensure Python environment ---
if [ ! -d "$CHAINFEED_DIR/.venv" ]; then
  echo "🐍 Creating Python environment..."
  python3 -m venv "$CHAINFEED_DIR/.venv"
fi

source "$CHAINFEED_DIR/.venv/bin/activate"
pip install -q -r "$CHAINFEED_DIR/requirements.txt" || echo "⚠️ Pip install skipped or partial."

# --- Create launchd service ---
PLIST="$HOME/Library/LaunchAgents/ai.fotw.chainfeed.plist"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.fotw.chainfeed</string>

  <key>ProgramArguments</key>
  <array>
    <string>$CHAINFEED_DIR/.venv/bin/python3</string>
    <string>-m</string>
    <string>core.heartbeat_startup</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$CHAINFEED_DIR</string>

  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/ai.fotw.chainfeed.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/ai.fotw.chainfeed.err</string>
</dict>
</plist>
EOF

# --- Load or restart service ---
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo "✅ ChainFeed node installed and running from: $CHAINFEED_DIR"
#!/bin/bash
#
# setup_chainfeed_node.sh
# --------------------------------------------------------------
# Fully automated installer for a ChainFeed Development Node.
# Reinstalls cleanly on every run. Safe, idempotent, and self-healing.
# --------------------------------------------------------------

set -euo pipefail
LOG_FILE="$HOME/Library/Logs/chainfeed_installer.log"
CHAINFEED_DIR="$HOME/ChainFeed"
REPO_URL="https://github.com/dudefromearth/ChainFeed.git"
PYTHON_BIN="$(command -v python3 || true)"
BREW_BIN="$(command -v brew || true)"

echo "🧠 ChainFeed Node Installer (clean reinstall mode)"
echo "🗒️  Logging to: $LOG_FILE"
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "--------------------------------------------------------------"
echo "📦 STEP 1: Checking system dependencies..."
echo "--------------------------------------------------------------"

# Homebrew
if [ -z "$BREW_BIN" ]; then
  echo "🍺 Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "✅ Homebrew already installed."
fi

# Python
if [ -z "$PYTHON_BIN" ]; then
  echo "🐍 Installing Python 3..."
  brew install python@3.11
  PYTHON_BIN="$(brew --prefix)/bin/python3"
else
  echo "✅ Python already installed at $PYTHON_BIN"
fi

# Redis
if ! brew list redis &>/dev/null; then
  echo "🧱 Installing Redis..."
  brew install redis
else
  echo "✅ Redis already installed."
fi

echo "--------------------------------------------------------------"
echo "🧹 STEP 2: Cleaning previous installation..."
echo "--------------------------------------------------------------"
launchctl unload "$HOME/Library/LaunchAgents/ai.fotw.chainfeed.plist" >/dev/null 2>&1 || true
rm -rf "$CHAINFEED_DIR"
rm -f "$HOME/Library/LaunchAgents/ai.fotw.chainfeed.plist"
mkdir -p "$CHAINFEED_DIR"

echo "--------------------------------------------------------------"
echo "📥 STEP 3: Cloning latest dev branch..."
echo "--------------------------------------------------------------"
git clone --branch dev --single-branch "$REPO_URL" "$CHAINFEED_DIR"

cd "$CHAINFEED_DIR"

echo "--------------------------------------------------------------"
echo "🐍 STEP 4: Creating virtual environment..."
echo "--------------------------------------------------------------"
rm -rf .venv
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || echo "⚠️ No requirements.txt found, continuing."

echo "--------------------------------------------------------------"
echo "⚙️  STEP 5: Creating LaunchAgent..."
echo "--------------------------------------------------------------"
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

echo "--------------------------------------------------------------"
echo "🚀 STEP 6: Loading LaunchAgent..."
echo "--------------------------------------------------------------"
launchctl load -w "$PLIST"

sleep 3
if pgrep -f "core.heartbeat_startup" >/dev/null; then
  echo "✅ ChainFeed node started successfully!"
else
  echo "❌ ChainFeed node did not start properly. Check log file:"
  echo "   tail -f ~/Library/Logs/ai.fotw.chainfeed.err"
  exit 1
fi

echo "--------------------------------------------------------------"
echo "🧩 STEP 7: Verifying Redis mesh state..."
echo "--------------------------------------------------------------"
if redis-cli PING >/dev/null 2>&1; then
  echo "✅ Redis is running."
else
  echo "❌ Redis is not running! Starting Redis..."
  brew services start redis
fi

sleep 2
redis-cli HGETALL mesh:state || echo "⚠️ No mesh data yet — heartbeat may still be initializing."

echo "--------------------------------------------------------------"
echo "🎉 Installation complete!"
echo "--------------------------------------------------------------"
echo "✅ ChainFeed directory: $CHAINFEED_DIR"
echo "✅ Logs: ~/Library/Logs/ai.fotw.chainfeed.log"
echo "✅ LaunchAgent: ~/Library/LaunchAgents/ai.fotw.chainfeed.plist"
echo "--------------------------------------------------------------"
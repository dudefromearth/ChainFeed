#!/bin/bash
set -e

echo "🚀 Installing ChainFeed Node..."

# Ensure prerequisites
brew list redis >/dev/null 2>&1 || brew install redis
brew services start redis

# Clone or update ChainFeed repo
if [ ! -d ~/ChainFeed ]; then
  git clone https://github.com/dudefromearth/ChainFeed.git ~/ChainFeed
else
  cd ~/ChainFeed && git pull
fi

# Create virtual environment if missing
cd ~/ChainFeed
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Launchd service
cat << 'PLIST' > ~/Library/LaunchAgents/ai.fotw.chainfeed.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.fotw.chainfeed</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/$(whoami)/ChainFeed/.venv/bin/python3</string>
    <string>-m</string>
    <string>core.heartbeat_startup</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/$(whoami)/ChainFeed</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/Users/$(whoami)/Library/Logs/ai.fotw.chainfeed.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/$(whoami)/Library/Logs/ai.fotw.chainfeed.err</string>
</dict>
</plist>
PLIST

launchctl load ~/Library/LaunchAgents/ai.fotw.chainfeed.plist
launchctl start ai.fotw.chainfeed

echo "✅ ChainFeed Node installed and running."

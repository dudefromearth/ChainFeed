#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "🔍 Checking Python virtual environment..."

if [ ! -d ".venv" ]; then
  echo "🧱 Rebuilding .venv..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install redis pyyaml requests pandas
  echo "✅ Environment built successfully."
else
  source .venv/bin/activate
  echo "🔁 Updating environment..."
  pip install --upgrade pip
  pip install redis pyyaml requests pandas
  echo "✅ Environment refreshed."
fi

echo "🧪 Verifying imports..."
python3 -c "import redis, yaml, requests, pandas; print('✅ All core imports OK')"
echo "✨ ChainFeed environment verified and ready!"
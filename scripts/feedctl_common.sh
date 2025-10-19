#!/bin/bash
# =========================================================
# ⚙️  ChainFeed Common Feed Controller
# Shared between: live_feedctl.sh & historic_feedctl.sh
# =========================================================
# Provides:
#   - Unified menu and monitoring
#   - Preflight checks (Redis, config, environment)
#   - Smart exception detection in logs
#   - Safe startup validation and recovery prompts
# =========================================================

# ─────────────────────────────────────────────────────────────
# 🧩 Global Defaults
# ─────────────────────────────────────────────────────────────
APP_DIR="${APP_DIR:-$HOME/PyCharmProjects/ChainFeed}"
VENV="$APP_DIR/.venv/bin/activate"
GROUPS_FILE="$APP_DIR/groups.yaml"
COMMON_LOG_DIR="$APP_DIR/data/feed_logs"
mkdir -p "$COMMON_LOG_DIR"

if [ -f "$VENV" ]; then
  source "$VENV"
else
  echo "⚠️  Virtual environment not found at $VENV"
fi

# ─────────────────────────────────────────────────────────────
# 🚦 Preflight Checks
# ─────────────────────────────────────────────────────────────
preflight_check() {
  echo "🧠 Running preflight checks..."
  local errors=0

  if ! command -v redis-cli >/dev/null 2>&1; then
    echo "❌ redis-cli not found. Please install Redis CLI."
    ((errors++))
  else
    if ! redis-cli ping >/dev/null 2>&1; then
      echo "❌ Redis not responding. Start Redis with 'redis-server' first."
      ((errors++))
    else
      echo "✅ Redis connection OK."
    fi
  fi

  if [ ! -f "$GROUPS_FILE" ]; then
    echo "❌ Missing configuration: $GROUPS_FILE"
    ((errors++))
  else
    echo "✅ Group configuration found."
  fi

  if [ ! -d "$APP_DIR/data" ]; then
    echo "❌ Missing data directory: $APP_DIR/data"
    ((errors++))
  fi

  if [ "$errors" -gt 0 ]; then
    echo "⚠️  Preflight check failed — please resolve the above issues."
    return 1
  fi

  echo "🧩 Environment ready. Launching feed..."
  return 0
}

# ─────────────────────────────────────────────────────────────
# 🩺 Feed Monitoring
# ─────────────────────────────────────────────────────────────
monitor_feed() {
  local pid=$1
  local logfile=$2
  local group=$3
  local mode=$4

  echo "🩺 Monitoring feed process (PID: $pid) for [$group | $mode]..."
  while kill -0 "$pid" 2>/dev/null; do
    sleep 5
  done

  echo "⚠️  Feed process $pid for [$group | $mode] terminated unexpectedly."
  echo "🔍 Last 10 log lines:"
  tail -n 10 "$logfile" | sed 's/^/   /'

  # Smart exception scan
  if grep -q "Traceback (most recent call last):" "$logfile"; then
    echo "❌ Python exception detected in $logfile"
    grep -E "FileNotFoundError|KeyError|ConnectionRefusedError|RuntimeError" "$logfile" | tail -n 3 | sed 's/^/   /'
  fi

  read -rp "Would you like to restart [$group | $mode]? (y/n): " resp
  if [[ $resp =~ ^[Yy]$ ]]; then
    echo "🔁 Restarting [$group | $mode]..."
    start_feed "$mode"
  else
    echo "🛑 Feed remains stopped."
  fi
}

# ─────────────────────────────────────────────────────────────
# 🧭 Menu Display
# ─────────────────────────────────────────────────────────────
show_menu() {
  local mode="$1"
  clear
  echo "╔══════════════════════════════════════════════════════╗"
  printf "║        ChainFeed %-10s Feed Controller         ║\n" "$mode"
  echo "╚══════════════════════════════════════════════════════╝"
  echo "1) Start $mode Feed"
  echo "2) Stop $mode Feed"
  echo "3) Restart $mode Feed"
  echo "4) Monitor Logs"
  echo "5) View Active Jobs"
  echo "6) Configure Groups"
  echo "7) Exit"
  echo "--------------------------------------------------------"
  read -rp "Select an option: " opt
  case $opt in
    1) start_feed "$mode" ;;
    2) stop_feed "$mode" ;;
    3) restart_feed "$mode" ;;
    4) tail_logs "$mode" ;;
    5) list_jobs "$mode" ;;
    6) configure_groups ;;
    7) exit 0 ;;
    *) echo "Invalid option"; sleep 1; show_menu "$mode" ;;
  esac
}

# ─────────────────────────────────────────────────────────────
# 🚀 Feed Lifecycle Control
# ─────────────────────────────────────────────────────────────
start_feed() {
  local mode="$1"
  local manager log_dir logfile timestamp pid

  if ! preflight_check; then
    sleep 2
    show_menu "$mode"
    return
  fi

  if [[ "$mode" == "Live" ]]; then
    manager="python -m core.live_feed_manager"
    log_dir="$APP_DIR/data/live_logs"
  else
    manager="python -m core.historical_feed_manager"
    log_dir="$APP_DIR/data/historical_logs"
  fi
  mkdir -p "$log_dir"

  read -rp "Enter group (spx_complex / ndx_complex): " group
  timestamp=$(date +"%Y%m%d_%H%M%S")
  logfile="$log_dir/${mode,,}_${group}_${timestamp}.log"

  echo "--------------------------------------------"
  echo "📡 Starting $mode Feed for Group: $group"
  echo "📘 Log File: $logfile"
  echo "--------------------------------------------"

  if [[ "$mode" == "Historical" ]]; then
    read -rp "Enter historical date (YYYY-MM-DD): " date
    read -rp "Enter start time (HH:MM 24h): " start_time
    read -rp "Enter frequency in seconds (default 60): " freq
    read -rp "Enter stop time (HH:MM 24h, blank for manual stop): " stop_time
    freq=${freq:-60}

    nohup $manager \
      --group "$group" \
      --historical-date "$date" \
      --start-time "$start_time" \
      --frequency "$freq" \
      --stop-time "$stop_time" \
      > "$logfile" 2>&1 &
  else
    nohup $manager --group "$group" > "$logfile" 2>&1 &
  fi

  pid=$!
  sleep 2

  # Validate process actually started
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "❌ $mode Feed failed to start. Check $logfile for details."
    tail -n 10 "$logfile"
    sleep 2
    return
  fi

  echo "✅ $mode Feed started successfully (PID: $pid)"
  monitor_feed "$pid" "$logfile" "$group" "$mode" &
  sleep 2; show_menu "$mode"
}

stop_feed() {
  local mode="$1"
  echo "🛑 Stopping all $mode feed processes..."
  if [[ "$mode" == "Live" ]]; then
    pkill -f "core.live_feed_manager"
  else
    pkill -f "core.historical_feed_manager"
  fi
  echo "✅ $mode feeds stopped."
  sleep 1; show_menu "$mode"
}

restart_feed() {
  local mode="$1"
  stop_feed "$mode"; sleep 2; start_feed "$mode"
}

# ─────────────────────────────────────────────────────────────
# 📋 Utility Functions
# ─────────────────────────────────────────────────────────────
tail_logs() {
  local mode="$1"
  local log_dir
  [[ "$mode" == "Live" ]] && log_dir="$APP_DIR/data/live_logs" || log_dir="$APP_DIR/data/historical_logs"

  echo "Available logs:"
  ls -1t "$log_dir" | head -10
  read -rp "Enter log filename (or leave blank for latest): " fname
  [ -z "$fname" ] && fname=$(ls -1t "$log_dir" | head -1)
  tail -f "$log_dir/$fname"
}

list_jobs() {
  local mode="$1"
  local match
  [[ "$mode" == "Live" ]] && match="core.live_feed_manager" || match="core.historical_feed_manager"
  echo "📋 Active $mode Feed Jobs:"
  ps aux | grep "$match" | grep -v grep
  read -rp "Press Enter to return..."
  show_menu "$mode"
}

configure_groups() {
  echo "Opening group configuration..."
  nano "$GROUPS_FILE"
}

# End of feedctl_common.sh
#!/bin/bash
# =========================================================
# ChainFeed Historical Feed Controller
# =========================================================
APP_DIR="$HOME/PyCharmProjects/ChainFeed"
VENV="$APP_DIR/.venv/bin/activate"
MANAGER="python -m core.historical_feed_manager"
CONFIG="$APP_DIR/data/historical_config.json"
LOG_DIR="$APP_DIR/data/historical_logs"

mkdir -p "$LOG_DIR"
cd "$APP_DIR" || exit
source "$VENV"

# =========================================================
# 🩺 Monitor Feed Function
# =========================================================
monitor_feed() {
  pid=$1
  logfile=$2
  group=$3

  echo "🩺 Monitoring feed process (PID: $pid)..."
  while kill -0 "$pid" 2>/dev/null; do
    sleep 5
  done

  echo "⚠️ Feed process $pid terminated unexpectedly."
  echo "🔍 Last 10 log lines:"
  tail -n 10 "$logfile" | sed 's/^/   /'

  if grep -q "Traceback (most recent call last):" "$logfile"; then
    echo "❌ Python exception detected in $logfile"
  fi

  read -rp "Would you like to restart $group feed? (y/n): " resp
  if [[ $resp =~ ^[Yy]$ ]]; then
    echo "🔁 Restarting $group feed..."
    start_feed
  else
    echo "🛑 Feed remains stopped."
  fi
}

# =========================================================
# 🧩 Menu Functions
# =========================================================
save_config() {
  cat <<EOF > "$CONFIG"
{
  "group": "$group",
  "historical_date": "$date",
  "start_time": "$start_time",
  "frequency": "$freq",
  "stop_time": "$stop_time"
}
EOF
}

show_menu() {
  clear
  echo "╔══════════════════════════════════════════════════════╗"
  echo "║             ChainFeed Historical Manager             ║"
  echo "╚══════════════════════════════════════════════════════╝"
  echo "1) Start Historical Feed"
  echo "2) Stop Historical Feed"
  echo "3) Restart Historical Feed"
  echo "4) Monitor Logs"
  echo "5) View Active Jobs"
  echo "6) Configure Groups"
  echo "7) Exit"
  echo "--------------------------------------------------------"
  read -rp "Select an option: " opt
  case $opt in
    1) start_feed ;;
    2) stop_feed ;;
    3) restart_feed ;;
    4) tail_logs ;;
    5) list_jobs ;;
    6) configure_groups ;;
    7) exit 0 ;;
    *) echo "Invalid option"; sleep 1; show_menu ;;
  esac
}

start_feed() {
  read -rp "Enter group (spx_complex / ndx_complex): " group
  read -rp "Enter historical date (YYYY-MM-DD): " date
  read -rp "Enter start time (HH:MM 24h): " start_time
  read -rp "Enter frequency in seconds (default 60): " freq
  read -rp "Enter stop time (HH:MM 24h, blank for manual stop): " stop_time

  freq=${freq:-60}
  timestamp=$(date +"%Y%m%d_%H%M%S")
  logfile="$LOG_DIR/historical_${group}_${timestamp}.log"

  save_config
  echo "--------------------------------------------"
  echo "📅 Group:       $group"
  echo "🕐 Date:        $date"
  echo "⏰ Start Time:  $start_time"
  echo "🔁 Frequency:   ${freq}s"
  echo "🪩 Stop Time:   ${stop_time:-Manual}"
  echo "📘 Log File:    $logfile"
  echo "--------------------------------------------"

  nohup $MANAGER \
      --group "$group" \
      --historical-date "$date" \
      --start-time "$start_time" \
      --frequency "$freq" \
      --stop-time "$stop_time" \
      > "$logfile" 2>&1 &

  pid=$!
  echo "✅ Feed started (PID: $pid). Logs: $logfile"
  monitor_feed $pid "$logfile" "$group" &
  sleep 2; show_menu
}

stop_feed() {
  echo "🛑 Stopping all historical feed processes..."
  pkill -f "core.historical_feed_manager"
  echo "✅ Feeds stopped."
  sleep 1; show_menu
}

restart_feed() {
  stop_feed; sleep 2; start_feed
}

tail_logs() {
  echo "Available logs:"
  ls -1t "$LOG_DIR" | head -10
  read -rp "Enter log filename (or leave blank for latest): " fname
  [ -z "$fname" ] && fname=$(ls -1t "$LOG_DIR" | head -1)
  tail -f "$LOG_DIR/$fname"
}

list_jobs() {
  echo "📋 Active Historical Feed Jobs:"
  ps aux | grep "core.historical_feed_manager" | grep -v grep
  read -rp "Press Enter to return..."
  show_menu
}

configure_groups() {
  nano "$APP_DIR/groups.yaml"
}

show_menu
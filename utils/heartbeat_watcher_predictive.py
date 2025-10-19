"""
utils/heartbeat_watcher_predictive.py
──────────────────────────────────────────────
Predictive + uptime-aware + persistent heartbeat monitor for ChainFeed.

Features:
  • Predictive silence detection (active → overdue → silent)
  • Time Alive indicator (mm:ss → hh:mm:ss → days)
  • Continuous uptime tracking
  • Persistent rolling CSV log for historical analysis
──────────────────────────────────────────────
"""

import json
import time
import redis
import os
import csv
from datetime import datetime, timezone

CLEAR = "cls" if os.name == "nt" else "clear"
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "heartbeat_history.csv")


class FeedState:
    def __init__(self, expected_cycle=30):
        self.expected = expected_cycle
        self.last_seen = {}
        self.symbols = {}
        self.started = {}
        self.silent_since = {}
        self.last_state = {}  # track last state for CSV delta logging

    def update(self, group, symbols, timestamp):
        try:
            ts = datetime.fromisoformat(timestamp)
            self.last_seen[group] = ts
            self.symbols[group] = symbols
            if group not in self.started:
                self.started[group] = ts
            if group in self.silent_since:
                del self.silent_since[group]
        except Exception:
            pass

    def status(self, group):
        if group not in self.last_seen:
            return None, "❌ never seen"
        delta = (datetime.now(timezone.utc) - self.last_seen[group]).total_seconds()
        if delta <= self.expected * 1.2:
            return delta, "✅ active"
        elif delta <= self.expected * 2:
            return delta, "⚠️ overdue"
        else:
            if group not in self.silent_since:
                self.silent_since[group] = datetime.now(timezone.utc)
            return delta, "🚨 silent"

    def time_alive(self, group):
        if group not in self.started:
            return "N/A"
        now = datetime.now(timezone.utc)
        if group in self.silent_since:
            alive_until = self.silent_since[group]
        else:
            alive_until = now
        delta = alive_until - self.started[group]
        total_seconds = int(delta.total_seconds())

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if days > 0:
            return f"{days}d {hours:02}h:{minutes:02}m:{seconds:02}s"
        elif hours > 0:
            return f"{hours:02}h:{minutes:02}m:{seconds:02}s"
        else:
            return f"{minutes:02}m:{seconds:02}s"

    def log_state(self, group, state, delta, uptime):
        """Log transitions to CSV only when state changes."""
        last = self.last_state.get(group)
        if last != state:
            self.last_state[group] = state
            ts = datetime.now(timezone.utc).isoformat()
            with open(LOG_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([ts, group, state, f"{delta:.1f}", uptime])


def connect_redis():
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        print("✅ Connected to Redis (localhost:6379)\n")
        return r
    except redis.ConnectionError as e:
        raise RuntimeError(f"❌ Cannot connect to Redis: {e}")


def ensure_csv_header():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "group", "state", "delta_since_last_s", "uptime"])


def monitor(interval=1, expected_cycle=30):
    ensure_csv_header()
    r = connect_redis()
    feeds = FeedState(expected_cycle=expected_cycle)

    while True:
        os.system(CLEAR)
        print("💓  ChainFeed Predictive Heartbeat Monitor — Persistent Mode")
        print("──────────────────────────────────────────────")

        keys = sorted(r.keys("heartbeat:*"))
        active_groups = set()

        for key in keys:
            data = json.loads(r.get(key))
            group = data.get("group", "unknown")
            symbols = ", ".join(data.get("symbols", []))
            timestamp = data.get("timestamp", "")
            ttl = r.ttl(key)
            feeds.update(group, symbols, timestamp)

            delta, state = feeds.status(group)
            ago = f"{delta:.1f}s ago" if delta is not None else "N/A"
            uptime = feeds.time_alive(group)

            print(f"\n🫀 {group.upper()} ({key.decode()})")
            print(f"   • Symbols: {symbols}")
            print(f"   • Last seen: {ago}")
            print(f"   • TTL: {ttl if ttl >= 0 else '∞'}s")
            print(f"   • Time Alive: {uptime}")
            print(f"   • Status: {state}")

            feeds.log_state(group, state, delta or 0.0, uptime)
            active_groups.add(group)

        # Detect missing feeds (no active Redis key)
        for group in feeds.last_seen.keys():
            if group not in active_groups:
                delta, state = feeds.status(group)
                ago = f"{delta:.1f}s ago" if delta is not None else "N/A"
                uptime = feeds.time_alive(group)
                print(f"\n⚠️  {group.upper()} feed missing from Redis")
                print(f"   • Last seen: {ago}")
                print(f"   • Time Alive: {uptime}")
                print(f"   • Status: {state}")
                feeds.log_state(group, state, delta or 0.0, uptime)

        print("\n──────────────────────────────────────────────")
        print(f"UTC Time: {datetime.now(timezone.utc).isoformat()}")
        print(f"📈 Log file: {LOG_FILE}")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        monitor(interval=1, expected_cycle=30)
    except KeyboardInterrupt:
        print("\n🛑 Stopped predictive heartbeat watcher.")
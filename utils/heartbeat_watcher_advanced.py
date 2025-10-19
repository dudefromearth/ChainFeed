"""
utils/heartbeat_watcher_advanced.py
──────────────────────────────────────────────
Advanced Redis heartbeat monitor for ChainFeed.
Adds:
  • Latency delta (since last heartbeat)
  • Average publish interval per group
  • Drift warnings (deviation from expected cycle)
──────────────────────────────────────────────
"""

import json
import time
import redis
import os
from datetime import datetime, timezone
from statistics import mean

CLEAR = "cls" if os.name == "nt" else "clear"


class HeartbeatTracker:
    """Tracks heartbeat intervals, TTLs, and drift over time."""

    def __init__(self, expected_cycle=30):
        self.last_seen = {}
        self.intervals = {}
        self.expected_cycle = expected_cycle

    def update(self, group: str, timestamp: str):
        """Update latency and interval tracking for a group."""
        now = datetime.now(timezone.utc)
        try:
            t = datetime.fromisoformat(timestamp)
        except Exception:
            return None

        if group in self.last_seen:
            delta = (t - self.last_seen[group]).total_seconds()
            if delta > 0:
                self.intervals.setdefault(group, []).append(delta)

        self.last_seen[group] = t

    def get_stats(self, group: str):
        """Return latency and drift summary."""
        if group not in self.intervals or not self.intervals[group]:
            return "N/A", "N/A"

        avg = mean(self.intervals[group])
        drift = abs(avg - self.expected_cycle)
        return f"{avg:.1f}s", f"{drift:+.2f}s"


def connect_redis():
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        print("✅ Connected to Redis (localhost:6379)\n")
        return r
    except redis.ConnectionError as e:
        raise RuntimeError(f"❌ Cannot connect to Redis: {e}")


def fmt_delta(ts: str) -> str:
    """Format time since timestamp."""
    try:
        t = datetime.fromisoformat(ts)
        delta = datetime.now(timezone.utc) - t
        return f"{delta.total_seconds():.1f}s ago"
    except Exception:
        return "N/A"


def monitor(interval=1, expected_cycle=30):
    r = connect_redis()
    tracker = HeartbeatTracker(expected_cycle=expected_cycle)

    while True:
        os.system(CLEAR)
        print("💓  ChainFeed Heartbeat Monitor — Advanced Mode")
        print("──────────────────────────────────────────────")
        keys = sorted(r.keys("heartbeat:*"))

        if not keys:
            print("⚠️  No heartbeat keys found.")
        else:
            for key in keys:
                key_str = key.decode()
                ttl = r.ttl(key)
                data = json.loads(r.get(key))
                group = data.get("group", "unknown")
                symbols = ", ".join(data.get("symbols", []))
                timestamp = data.get("timestamp", "N/A")

                tracker.update(group, timestamp)
                avg, drift = tracker.get_stats(group)

                ago = fmt_delta(timestamp)
                status = "✅ ACTIVE" if ttl > 0 else "❌ EXPIRED"
                drift_flag = ""
                if drift != "N/A":
                    drift_val = float(drift.replace("s", "").replace("+", ""))
                    if drift_val > expected_cycle * 0.2:  # 20% tolerance
                        drift_flag = "⚠️ drift"
                    elif drift_val > expected_cycle * 0.5:
                        drift_flag = "🚨 drift"

                print(f"\n🫀 {group.upper()} ({key_str})")
                print(f"   • Symbols: {symbols}")
                print(f"   • Last updated: {ago}")
                print(f"   • TTL: {ttl if ttl >= 0 else '∞'}s")
                print(f"   • Avg cycle: {avg} (drift {drift}) {drift_flag}")
                print(f"   • Status: {status}")

        print("\n──────────────────────────────────────────────")
        print(f"UTC Time: {datetime.now(timezone.utc).isoformat()}")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        monitor(interval=1, expected_cycle=30)
    except KeyboardInterrupt:
        print("\n🛑 Stopped advanced heartbeat watcher.")

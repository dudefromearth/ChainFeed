"""
utils/heartbeat_watcher.py
──────────────────────────────────────────────
Live Redis monitor that watches all group heartbeats.
Shows:
  • Remaining TTL
  • Time since last heartbeat
  • Active / expired status
──────────────────────────────────────────────
"""

import json
import time
import redis
import os
from datetime import datetime, timezone

CLEAR = "cls" if os.name == "nt" else "clear"


def connect_redis():
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        return r
    except redis.ConnectionError as e:
        raise RuntimeError(f"❌ Cannot connect to Redis: {e}")


def fmt_time(ts: str) -> str:
    """Format timestamp delta from UTC now."""
    try:
        t = datetime.fromisoformat(ts)
        delta = datetime.now(timezone.utc) - t
        return f"{delta.total_seconds():.1f}s ago"
    except Exception:
        return "N/A"


def monitor(interval: int = 1):
    r = connect_redis()
    print("✅ Connected to Redis (localhost:6379)")
    print("👁️  Watching live heartbeats...\n")

    while True:
        os.system(CLEAR)
        print("💓  ChainFeed Heartbeat Monitor")
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
                ago = fmt_time(timestamp)
                status = "✅ ACTIVE" if ttl > 0 else "❌ EXPIRED"
                print(f"\n🫀 {group.upper()} ({key_str})")
                print(f"   • Symbols: {symbols}")
                print(f"   • Last updated: {ago}")
                print(f"   • TTL: {ttl if ttl >= 0 else '∞'}s")
                print(f"   • Status: {status}")

        print("\n──────────────────────────────────────────────")
        print(f"UTC Time: {datetime.now(timezone.utc).isoformat()}")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n🛑 Stopped heartbeat watcher.")
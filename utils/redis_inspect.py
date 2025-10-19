"""
utils/redis_inspect.py
──────────────────────────────────────────────
Quick inspection utility for Redis-stored ChainFeed data.
Prints all chain snapshots and heartbeats in human-readable form.
──────────────────────────────────────────────
"""

import json
import redis
from datetime import datetime, timezone


def connect_redis():
    """Connect to Redis locally."""
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        print("✅ Connected to Redis (localhost:6379)")
        return r
    except redis.ConnectionError as e:
        raise RuntimeError(f"❌ Cannot connect to Redis: {e}")


def inspect_snapshots(r):
    """Inspect all chain snapshots stored in Redis."""
    print("\n🔍 Inspecting chain snapshots...")
    keys = sorted(r.keys("chain:*snapshot"))
    if not keys:
        print("⚠️ No snapshot keys found.")
        return

    for key in keys:
        key_str = key.decode()
        data = json.loads(r.get(key))
        print(f"\n📦 {key_str}")
        print(f"  • Contracts: {len(data.get('contracts', []))}")
        print(f"  • Normalized: {data.get('normalized', False)}")
        meta = data.get('metadata', {})
        if meta:
            print(f"  • Metadata keys: {list(meta.keys())}")
        print(f"  • Published at: {data.get('published_at', 'N/A')}")


def inspect_heartbeats(r):
    """Inspect heartbeat status for all groups."""
    print("\n💓 Inspecting heartbeats...")
    keys = sorted(r.keys("heartbeat:*"))
    if not keys:
        print("⚠️ No heartbeat keys found.")
        return

    for key in keys:
        key_str = key.decode()
        ttl = r.ttl(key)
        data = json.loads(r.get(key))
        print(f"\n🫀 {key_str}")
        print(f"  • Group: {data['group']}")
        print(f"  • Symbols: {data['symbols']}")
        print(f"  • Timestamp: {data['timestamp']}")
        print(f"  • TTL: {ttl if ttl >= 0 else '∞'}s")


def main():
    r = connect_redis()
    inspect_snapshots(r)
    inspect_heartbeats(r)

    print("\n✅ Redis inspection complete.")
    now = datetime.now(timezone.utc).isoformat()
    print(f"Timestamp: {now}")


if __name__ == "__main__":
    main()
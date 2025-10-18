# chain_publisher.py

import json
import redis
from datetime import datetime, timezone
from utils.redis_keys import RedisKeys

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def iso_to_epoch(ts: str) -> int:
    """Convert ISO timestamp to epoch seconds."""
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())

def post_chain_snapshot(symbol: str, ts: str, primary: dict, raw: dict, mode: str = "minimal", ttl: int = 1200):
    """Store a normalized snapshot in Redis using canonical keys."""
    ep = iso_to_epoch(ts)
    primary_key = RedisKeys.full_feed_key(symbol, ts)
    raw_key = RedisKeys.full_feed_raw_key(symbol, ts)

    # Write the full payloads
    pipe = r.pipeline()
    pipe.set(primary_key, json.dumps(primary))
    pipe.expire(primary_key, ttl)
    pipe.zadd(RedisKeys.trail_full_key(symbol), {primary_key: ep})

    pipe.set(raw_key, json.dumps(raw))
    pipe.expire(raw_key, ttl)
    pipe.zadd(RedisKeys.trail_full_raw_key(symbol), {raw_key: ep})

    # Update pointers
    pipe.set(RedisKeys.latest_full_key(symbol), primary_key)
    pipe.set(RedisKeys.latest_full_raw_key(symbol), raw_key)

    # Trim trails
    cutoff = ep - ttl
    pipe.zremrangebyscore(RedisKeys.trail_full_key(symbol), 0, cutoff)
    pipe.zremrangebyscore(RedisKeys.trail_full_raw_key(symbol), 0, cutoff)

    pipe.execute()

    print(f"[📡] Posted snapshot: {primary_key} (mode={mode}, count={primary.get('count', '?')})")

def publish_full_snapshot(symbol: str, ts: str, key: str, count: int, mode: str = "minimal"):
    """Optional pub/sub message (for full payload updates)."""
    chan = RedisKeys.full_pubsub_channel(symbol)
    msg = {
        "type": "full",
        "symbol": symbol,
        "ts": ts,
        "key": key,
        "count": count,
        "total_volume": 0,
        "total_oi": 0,
        "mode": mode
    }
    sent = r.publish(chan, json.dumps(msg))
    print(f"[📢] Published to {chan} (subscribers={sent})")
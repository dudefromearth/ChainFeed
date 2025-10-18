import time
import json
import redis
from datetime import datetime, timezone

from utils.redis_keys import RedisKeys
from utils.symbol_utils import get_configured_symbols, inspect_symbol_status

class HeartbeatInjector:
    def __init__(self, redis_host="localhost", redis_port=6379, interval_sec=3):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.interval_sec = interval_sec

    def make_payload(self):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Discover symbols from current Redis keys or configuration
        symbols = get_configured_symbols()

        feeds = {}
        for symbol in symbols:
            status = inspect_symbol_status(self.redis, symbol)
            feeds[symbol] = status

        # Determine overall status
        any_missing = any(not s["full"] or not s["diff"] for s in feeds.values())
        all_ok = all(s["full"] and s["diff"] and s["live"] for s in feeds.values())

        overall_status = "active" if all_ok else ("idle" if not any_missing else "missing")

        return {
            "ts": now,
            "status": overall_status,
            "feeds": feeds,
            "notes": "Auto-generated heartbeat",
            "source": "heartbeat_injector",
        }

    def run(self):
        print(f"[~] Starting Heartbeat Injector, interval={self.interval_sec}s")
        while True:
            payload = self.make_payload()
            try:
                self.redis.set(RedisKeys.HEARTBEAT.value, json.dumps(payload), ex=10)
                print(f"[✓] Heartbeat @ {payload['ts']}  status={payload['status']}")
            except Exception as e:
                print(f"[!] Redis error: {e}")
            time.sleep(self.interval_sec)

if __name__ == "__main__":
    injector = HeartbeatInjector()
    injector.run()
"""
core/heartbeat_monitor.py
──────────────────────────────────────────────
Monitors all group heartbeats in Redis and reports liveness.

States:
  - alive: heartbeat within freshness threshold
  - stale: heartbeat older than threshold but not expired
  - dead:  heartbeat missing or invalid

Publishes system summary → Redis key: "system:status"
──────────────────────────────────────────────
"""

import json
import time
import redis
import warnings
from datetime import datetime, timezone, timedelta

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

DEFAULT_HEARTBEAT_PREFIX = "heartbeat:"
DEFAULT_SYSTEM_STATUS_KEY = "system:status"
DEFAULT_FRESHNESS_THRESHOLD = timedelta(seconds=30)
DEFAULT_STALE_THRESHOLD = timedelta(seconds=90)
DEFAULT_POLL_INTERVAL = 5  # seconds


# ──────────────────────────────────────────────
# Redis Client
# ──────────────────────────────────────────────

def get_redis_client() -> redis.Redis:
    """Connect to local Redis."""
    try:
        client = redis.Redis(host="localhost", port=6379, db=0)
        client.ping()
        print("✅ Connected to Redis (localhost:6379)")
        return client
    except redis.ConnectionError as e:
        raise RuntimeError(f"❌ Cannot connect to Redis: {e}")


# ──────────────────────────────────────────────
# Heartbeat Monitor Core
# ──────────────────────────────────────────────

class HeartbeatMonitor:
    """
    Watches all `heartbeat:*` keys and reports liveness state.
    Also publishes an aggregate system health summary to Redis.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        freshness: timedelta = DEFAULT_FRESHNESS_THRESHOLD,
        stale_after: timedelta = DEFAULT_STALE_THRESHOLD,
        system_key: str = DEFAULT_SYSTEM_STATUS_KEY,
    ):
        self.redis = redis_client
        self.freshness = freshness
        self.stale_after = stale_after
        self.system_key = system_key

    # ──────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────
    def _get_utc_now(self):
        return datetime.now(timezone.utc)

    def _decode(self, raw):
        if not raw:
            return None
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return raw

    def _parse_heartbeat(self, raw_json):
        """Parse and validate a single heartbeat payload."""
        try:
            data = json.loads(self._decode(raw_json))
            ts = datetime.fromisoformat(data["timestamp"])
            if ts.tzinfo is None:
                warnings.warn(f"⚠️ Heartbeat timestamp missing tzinfo: {data}")
                ts = ts.replace(tzinfo=timezone.utc)
            data["_parsed_ts"] = ts
            return data
        except Exception as e:
            warnings.warn(f"❌ Failed to parse heartbeat: {e}")
            return None

    def _evaluate_status(self, hb):
        """Determine heartbeat state based on timestamp."""
        if hb is None:
            return "dead"

        now = self._get_utc_now()
        age = now - hb["_parsed_ts"]

        if age <= self.freshness:
            return "alive"
        elif age <= self.stale_after:
            return "stale"
        return "dead"

    # ──────────────────────────────────────────────
    # Core monitoring logic
    # ──────────────────────────────────────────────
    def check_all(self):
        """Fetch and evaluate all heartbeat keys."""
        keys = self.redis.keys(f"{DEFAULT_HEARTBEAT_PREFIX}*")
        now = self._get_utc_now()
        print(f"\n⏱️ Checking {len(keys)} heartbeats at {now.isoformat()}")

        status_report = {"alive": [], "stale": [], "dead": []}

        for key in keys:
            hb_raw = self.redis.get(key)
            hb_data = self._parse_heartbeat(hb_raw)
            state = self._evaluate_status(hb_data)
            name = self._decode(key).replace(DEFAULT_HEARTBEAT_PREFIX, "")
            entry = {
                "group": name,
                "state": state,
                "timestamp": hb_data["timestamp"] if hb_data else None,
                "symbols": hb_data.get("symbols") if hb_data else [],
            }
            status_report[state].append(entry)
            print(f"  • {name:<20} → {state.upper()}")

        if not keys:
            print("⚠️ No heartbeat keys found in Redis.")

        # Publish system summary
        self._publish_system_status(status_report)
        return status_report

    # ──────────────────────────────────────────────
    # System summary publisher
    # ──────────────────────────────────────────────
    def _publish_system_status(self, report):
        """Store aggregated heartbeat status in Redis."""
        payload = {
            "timestamp": self._get_utc_now().isoformat(),
            "summary": {
                "alive": len(report["alive"]),
                "stale": len(report["stale"]),
                "dead": len(report["dead"]),
            },
            "groups": report,
        }
        self.redis.set(self.system_key, json.dumps(payload))
        print(f"📡 Published system summary → {self.system_key}")

    # ──────────────────────────────────────────────
    # Continuous monitor
    # ──────────────────────────────────────────────
    def watch(self, interval: int = DEFAULT_POLL_INTERVAL):
        """Continuously monitor heartbeats at fixed interval."""
        print(f"\n👁️  Starting Heartbeat Monitor (interval={interval}s)...\n")
        while True:
            try:
                self.check_all()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n🛑 Monitor stopped manually.")
                break
            except Exception as e:
                warnings.warn(f"❌ Monitor encountered error: {e}")
                time.sleep(interval)


# ──────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor ChainFeed heartbeats in Redis.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously monitor heartbeats (default: run once)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help="Polling interval in seconds (used with --watch)",
    )
    args = parser.parse_args()

    redis_client = get_redis_client()
    monitor = HeartbeatMonitor(redis_client)

    if args.watch:
        monitor.watch(interval=args.interval)
    else:
        monitor.check_all()
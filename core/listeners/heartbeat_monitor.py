#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Heartbeat Monitor
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-25
#
# Purpose:
# --------
# Monitors all active node heartbeats in Redis and emits alerts
# if any node's heartbeat is missing or stale beyond threshold.
#
# Publishes alerts to Redis under:
#   truth:alert:system
#
# Example alert payload:
# {
#   "node_id": "studiotwo.local_chainfeed",
#   "timestamp": "2025-10-25T12:30:00Z",
#   "severity": "warning",
#   "message": "Heartbeat missing for 45s"
# }
#
# ===============================================================

import time
import json
import redis
import logging
from datetime import datetime, timezone


class HeartbeatMonitor:
    def __init__(self, redis_client, check_interval: int = 15, max_age: int = 30, logger=None):
        """
        :param redis_client: active Redis client
        :param check_interval: how often to scan for heartbeats (sec)
        :param max_age: max allowed heartbeat age before alert (sec)
        """
        self.redis = redis_client
        self.check_interval = check_interval
        self.max_age = max_age
        self.logger = logger or logging.getLogger("HeartbeatMonitor")
        self.running = False

    # -----------------------------------------------------------
    # 🌿 Utility: current UTC time
    # -----------------------------------------------------------
    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    # -----------------------------------------------------------
    # 🌿 Main Loop
    # -----------------------------------------------------------
    def start(self):
        if self.running:
            self.logger.warning("⚠️ HeartbeatMonitor already running.")
            return
        self.running = True
        self.logger.info(f"👁️ HeartbeatMonitor started (interval={self.check_interval}s, threshold={self.max_age}s).")

        try:
            while self.running:
                self._scan()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("🛑 HeartbeatMonitor stopped by user.")
            self.running = False
        except Exception as e:
            self.logger.error(f"HeartbeatMonitor error: {e}", exc_info=True)
            self.running = False

    # -----------------------------------------------------------
    # 🌿 Scan all heartbeats in Redis
    # -----------------------------------------------------------
    def _scan(self):
        keys = self.redis.keys("truth:heartbeat:*")
        now = self.now_utc()

        for key in keys:
            try:
                raw = self.redis.get(key)
                if not raw:
                    continue
                data = json.loads(raw)
                ts_str = data.get("timestamp")
                node_id = data.get("node_id", "unknown")
                if not ts_str:
                    continue

                hb_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                age = (now - hb_time).total_seconds()

                if age > self.max_age:
                    self._alert(node_id, age)
                    self.logger.warning(f"⚠️  Heartbeat stale: {node_id} ({int(age)}s old)")
                else:
                    self.logger.info(f"💓 {node_id} healthy ({int(age)}s old)")

            except Exception as e:
                self.logger.error(f"Error checking {key}: {e}", exc_info=True)

    # -----------------------------------------------------------
    # 🌿 Emit alert to Redis
    # -----------------------------------------------------------
    def _alert(self, node_id: str, age: float):
        payload = {
            "node_id": node_id,
            "timestamp": self.now_utc().isoformat(),
            "severity": "warning",
            "message": f"Heartbeat missing or stale ({int(age)}s old)"
        }
        self.redis.publish("truth:alert:system", json.dumps(payload))
        self.redis.set(f"truth:alert:{node_id}", json.dumps(payload))


# ---------------------------------------------------------------
# 🧩 Standalone test harness
# ---------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S"
    )

    r = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)
    monitor = HeartbeatMonitor(redis_client=r, check_interval=10, max_age=30)
    monitor.start()
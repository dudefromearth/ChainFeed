"""
core/heartbeat_injector.py
--------------------------

Heartbeat Injector

Publishes periodic heartbeat messages into Redis so other nodes and
the mesh watcher can monitor liveness and latency.
Also publishes lightweight real-time mesh:update events for
FrontEndNode SSE gateways to broadcast.
"""

import json
import time
from datetime import datetime, timezone
from utils.logger import get_logger
from utils.redis_client import get_redis_client
from config.chainfeed_constants import (
    HEARTBEAT_TTL_SEC,
    HEARTBEAT_KEY_TEMPLATE,
    NODE_ID,
    FEED_GROUPS,
    HEARTBEAT_VERSION,
)

# ----------------------------------------------------------
# Logger and Redis
# ----------------------------------------------------------
logger = get_logger("heartbeat.injector")
redis = get_redis_client()


class HeartbeatInjector:
    """
    Periodically publishes node heartbeat messages into Redis.
    Each heartbeat includes node_id, group, timestamp, and schema version.
    Also emits a mesh:update event for live SSE synchronization.
    """

    def __init__(self, interval_sec: int = 5):
        self.interval_sec = interval_sec
        self.node_id = NODE_ID
        self.groups = FEED_GROUPS or ["index_complex"]

    def _build_heartbeat(self, group: str) -> dict:
        """Construct a heartbeat payload."""
        return {
            "node_id": self.node_id,
            "group": group,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "online",
            "version": HEARTBEAT_VERSION,
        }

    def run(self):
        """Main heartbeat emission loop."""
        logger.info(f"💓 Heartbeat injector started for node '{self.node_id}'.")
        while True:
            try:
                for group in self.groups:
                    key = HEARTBEAT_KEY_TEMPLATE.format(group=group)
                    payload = self._build_heartbeat(group)

                    # Store heartbeat in Redis
                    redis.set(key, json.dumps(payload), ex=HEARTBEAT_TTL_SEC)
                    redis.hset("mesh:state", self.node_id, json.dumps(payload))

                    # 🟢 Publish live mesh update event
                    redis.publish("mesh:update", json.dumps(payload))

                    logger.debug(
                        f"🩺 Heartbeat sent | group={group} | node={self.node_id}"
                    )

                time.sleep(self.interval_sec)

            except Exception as e:
                logger.error(f"❌ Heartbeat injector error: {e}", exc_info=True)
                time.sleep(self.interval_sec * 2)


if __name__ == "__main__":
    injector = HeartbeatInjector()
    injector.run()
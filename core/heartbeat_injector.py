"""
core/heartbeat_injector.py
--------------------------

Heartbeat Injector (Atomic Mesh Update)

Publishes periodic heartbeat messages into Redis so other nodes and
the mesh watcher can monitor liveness and latency.

✅ Improvements
- Uses Redis pipeline (MULTI/EXEC) to update all feed groups atomically.
- Ensures `mesh:state` never appears partially populated.
- Still publishes lightweight mesh:update events for FrontEndNode SSE gateways.
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
    MESH_STATE_KEY,
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
    Uses a Redis pipeline to ensure atomic mesh:state updates.
    """

    def __init__(self, interval_sec: int = 5):
        self.interval_sec = interval_sec
        self.node_id = NODE_ID
        self.groups = FEED_GROUPS or ["index_complex"]

    def _build_heartbeat(self, group: str) -> dict:
        """Construct a heartbeat payload."""
        # Optional: add group-symbol mapping if available
        from config.chainfeed_constants import SYMBOL_GROUP_MAP
        symbols = SYMBOL_GROUP_MAP.get(group, [])
        return {
            "node_id": self.node_id,
            "group": group,
            "symbols": symbols,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "online",
            "version": HEARTBEAT_VERSION,
        }

    def run(self):
        """Main heartbeat emission loop."""
        logger.info(f"💓 Heartbeat injector started for node '{self.node_id}' (atomic mode).")

        while True:
            try:
                # --- Begin atomic pipeline ---
                pipe = redis.pipeline(transaction=True)

                for group in self.groups:
                    key = HEARTBEAT_KEY_TEMPLATE.format(group=group)
                    payload = self._build_heartbeat(group)

                    # Store heartbeat (with TTL)
                    from utils.redis_client import redis_set_with_policy
                    redis_set_with_policy(redis, key, json.dumps(payload))

                    # Update mesh:state field
                    mesh_field = f"{self.node_id}:{group}"
                    pipe.hset(MESH_STATE_KEY, mesh_field, json.dumps(payload))

                    # Publish live mesh update
                    pipe.publish("mesh:update", json.dumps(payload))

                # Execute all at once
                pipe.execute()
                # --- End atomic pipeline ---

                logger.debug(
                    f"🩺 Atomic heartbeat update complete for node={self.node_id} groups={self.groups}"
                )

                time.sleep(self.interval_sec)

            except Exception as e:
                logger.error(f"❌ Heartbeat injector error: {e}", exc_info=True)
                time.sleep(self.interval_sec * 2)


if __name__ == "__main__":
    injector = HeartbeatInjector()
    injector.run()
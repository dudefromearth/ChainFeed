"""
core/heartbeat_watcher.py
-------------------------

Predictive Heartbeat Watcher with Mesh Cleanup
----------------------------------------------

Monitors all node heartbeats in Redis, evaluates liveness,
and automatically removes or marks nodes that have gone silent
beyond their allowed TTL (stale or dead nodes).

Refactored to:
- Use canonical constants
- Structured logging
- Predictive drift tracking
- Auto-prune mesh registry for stale nodes
"""

import json
import time
from datetime import datetime, timezone
from utils.redis_client import get_redis_client
from utils.logger import get_logger
from config.chainfeed_constants import (
    HEARTBEAT_TTL_SEC,
    HEARTBEAT_KEY_TEMPLATE,
    HEARTBEAT_VERSION,
    MESH_STATE_KEY,
)

logger = get_logger("heartbeat.watcher")
redis = get_redis_client()


class HeartbeatWatcher:
    """
    Predictive heartbeat watcher that monitors node health
    and prunes stale entries from the mesh registry.

    Features:
      - Monitors all heartbeat:* keys in Redis
      - Computes drift per node (seconds since last update)
      - Marks or removes nodes with expired TTL
      - Publishes health summary logs
    """

    def __init__(self, redis_client=None, ttl: int = HEARTBEAT_TTL_SEC):
        self.redis = redis_client or redis
        self.ttl = ttl
        self.mesh_state = {}  # {node_id: {status, last_seen, drift}}

    def run(self):
        """Main watcher loop."""
        logger.info("👁️  Heartbeat watcher started (predictive mode).")
        while True:
            try:
                self._poll()
                time.sleep(self.ttl / 3)
            except Exception as e:
                logger.error(f"Watcher runtime error: {e}", exc_info=True)
                time.sleep(2)

    def _poll(self):
        """Poll heartbeat keys and update mesh state."""
        keys = self.redis.keys("heartbeat:*")
        now = datetime.now(timezone.utc)
        logger.debug(f"Polling {len(keys)} heartbeat keys...")

        # Temporary record for updated nodes
        current_nodes = {}

        for key in keys:
            raw = self.redis.get(key)
            if not raw:
                continue

            try:
                hb = json.loads(raw)
                node_id = hb.get("node_id")
                group = hb.get("group", "unknown")
                ts = datetime.fromisoformat(hb["timestamp"])
                drift = (now - ts).total_seconds()

                if drift > self.ttl:
                    logger.warning(
                        f"💀 Node offline | node={node_id} group={group} drift={drift:.1f}s > ttl={self.ttl}s"
                    )
                    self._mark_offline(node_id, group, ts)
                else:
                    logger.debug(
                        f"✅ Node healthy | node={node_id} group={group} drift={drift:.1f}s"
                    )
                    current_nodes[node_id] = {
                        "group": group,
                        "status": "online",
                        "timestamp": ts.isoformat(),
                        "version": HEARTBEAT_VERSION,
                    }

            except Exception as e:
                logger.error(f"Error processing {key}: {e}", exc_info=True)

        # Sync mesh registry
        self._sync_mesh_state(current_nodes)

    def _mark_offline(self, node_id: str, group: str, ts: datetime):
        """Mark a node as offline in Redis mesh state."""
        state = {
            "group": group,
            "status": "offline",
            "timestamp": ts.isoformat(),
            "version": HEARTBEAT_VERSION,
        }
        self.redis.hset(MESH_STATE_KEY, node_id, json.dumps(state))
        logger.info(f"🕱 Node marked offline: {node_id}")

    def _sync_mesh_state(self, current_nodes: dict):
        """
        Synchronize the mesh registry with the latest health data.
        - Updates online nodes
        - Removes stale entries not seen in current polling cycle
        """
        try:
            existing = self.redis.hgetall(MESH_STATE_KEY)
            # Handle both bytes and string responses
            existing_nodes = (
                [n.decode("utf-8") for n in existing.keys()]
                if isinstance(next(iter(existing.keys()), ""), bytes)
                else list(existing.keys())
            )
            current_set = set(current_nodes.keys())

            # Remove stale entries
            for node_id in existing_nodes:
                if node_id not in current_set:
                    logger.warning(f"🧹 Removing stale node: {node_id}")
                    self.redis.hdel(MESH_STATE_KEY, node_id)

            # Update current healthy nodes
            for node_id, state in current_nodes.items():
                self.redis.hset(MESH_STATE_KEY, node_id, json.dumps(state))

        except Exception as e:
            logger.error(f"Error syncing mesh state: {e}", exc_info=True)

        # ==========================================================
        # Runtime Entrypoint
        # ==========================================================
        if __name__ == "__main__":
            print("✅ Heartbeat watcher starting up...")  # <--- add this line for debugging
            watcher = HeartbeatWatcher()
            watcher.run()
"""
utils/integration_sync.py
-------------------------

Publishes the canonical ChainFeed integration schema to Redis.

This schema serves as the single source of truth for:
  • Redis key naming conventions
  • Heartbeat payload structure
  • System versioning metadata

All components — ChainFeed nodes, Tomcat SSE services, and React frontends —
should reference this schema (via Redis or REST) to remain synchronized.

Schema key in Redis:
    meta:chainfeed:integration

Update notifications are published on channel:
    integration:schema:update
"""

import json
from datetime import datetime
from utils.redis_client import get_redis_client
from utils.logger import get_logger
from config.chainfeed_constants import (
    REDIS_KEYS,
    REDIS_PREFIX,
    CHANNEL_PREFIX,
    REDIS_KEY_VERSION,
    HEARTBEAT_VERSION,
    HEARTBEAT_INTERVAL_SEC,
    HEARTBEAT_TTL_SEC,
    INTEGRATION_KEY,
    INTEGRATION_CHANNEL,
)

# ----------------------------------------------------------
# Logger and Redis setup
# ----------------------------------------------------------
logger = get_logger("integration.sync")
redis = get_redis_client()


# ----------------------------------------------------------
# Core function
# ----------------------------------------------------------
def publish_integration_schema():
    """
    Publishes the canonical ChainFeed integration schema to Redis.

    Returns:
        dict: The published schema document.
    """
    try:
        schema = {
            "version": REDIS_KEY_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "REDIS_PREFIX": REDIS_PREFIX,
            "CHANNEL_PREFIX": CHANNEL_PREFIX,
            "REDIS_KEYS": REDIS_KEYS,
            "HEARTBEAT_SCHEMA": {
                "version": HEARTBEAT_VERSION,
                "interval_sec": HEARTBEAT_INTERVAL_SEC,
                "ttl_sec": HEARTBEAT_TTL_SEC,
                "fields": {
                    "timestamp": "UTC ISO-8601 timestamp of last heartbeat",
                    "node_id": "Unique node identifier (string)",
                    "group": "Feed group (spx_complex, ndx_complex, etc.)",
                    "status": "online | lagging | offline",
                    "version": "Heartbeat protocol version",
                    "uptime_sec": "Cumulative uptime in seconds"
                },
                "example": {
                    "timestamp": "2025-10-21T12:00:00Z",
                    "node_id": "studioone_chainfeed",
                    "group": "spx_complex",
                    "status": "online",
                    "version": HEARTBEAT_VERSION,
                    "uptime_sec": 60
                }
            },
        }

        # Write schema to Redis
        redis.hset(INTEGRATION_KEY, mapping={"schema": json.dumps(schema)})
        redis.publish(INTEGRATION_CHANNEL, json.dumps(schema))

        logger.info(
            f"✅ Published integration schema | version={schema['version']} "
            f"heartbeat={schema['HEARTBEAT_SCHEMA']['version']}"
        )
        return schema

    except Exception as e:
        logger.error(f"❌ Failed to publish integration schema: {e}", exc_info=True)
        raise


# ----------------------------------------------------------
# Utility function (optional)
# ----------------------------------------------------------
def fetch_integration_schema():
    """
    Retrieves the current integration schema from Redis.
    Useful for verification and unit tests.

    Returns:
        dict: The schema document as a Python dictionary.
    """
    try:
        raw = redis.hget(INTEGRATION_KEY, "schema")
        if not raw:
            logger.warning("No integration schema found in Redis.")
            return {}
        schema = json.loads(raw)
        logger.info(f"Fetched integration schema version={schema.get('version')}")
        return schema
    except Exception as e:
        logger.error(f"Error fetching integration schema: {e}", exc_info=True)
        return {}


# ----------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------
if __name__ == "__main__":
    print("🧭 Publishing ChainFeed integration schema...")
    schema = publish_integration_schema()
    print(json.dumps(schema, indent=2))
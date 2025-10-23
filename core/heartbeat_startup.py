"""
core/heartbeat_startup.py
-------------------------

ChainFeed Node Startup Coordinator
----------------------------------
Brings a ChainFeed node online, connects to Redis, synchronizes integration schema,
validates feed metadata (expirations, etc.), and starts heartbeat injector + watcher.

Now fully declarative:
- Dynamically bootstraps all symbols from GROUP_SYMBOL_MAP
- Registers each node across all feed complexes
- Publishes full mesh state into Redis
"""

import asyncio
import json
from datetime import datetime, timezone

from utils.logger import get_logger
from utils.redis_client import get_redis_client
from core.integration_sync import publish_integration_schema
from core.heartbeat_injector import HeartbeatInjector
from core.heartbeat_watcher import HeartbeatWatcher
from core.feed_bootstrap import FeedBootstrap
from config.chainfeed_constants import (
    NODE_ID,
    GROUP_SYMBOL_MAP,
    MESH_STATE_KEY,
    CHAINFEED_VERSION,
)

logger = get_logger("heartbeat.startup")
redis = get_redis_client()


# ==========================================================
# Feed Bootstrap
# ==========================================================
async def run_bootstrap_for_symbol(symbol: str) -> bool:
    """Async helper for concurrent feed bootstraps."""
    try:
        bootstrap = FeedBootstrap(symbol)
        result = bootstrap.ensure_expirations_cached()
        return result
    except Exception as e:
        logger.error(f"Bootstrap error for {symbol}: {e}", exc_info=True)
        return False


async def run_feed_bootstraps():
    """
    Run feed bootstrap validations for all symbols in GROUP_SYMBOL_MAP.
    Returns a dict {symbol: status_bool}.
    """
    all_symbols = sorted({sym for symbols in GROUP_SYMBOL_MAP.values() for sym in symbols})
    logger.info(f"🧩 Running feed bootstraps for: {', '.join(all_symbols)}")

    tasks = [run_bootstrap_for_symbol(sym) for sym in all_symbols]
    results = await asyncio.gather(*tasks)

    bootstrap_results = dict(zip(all_symbols, results))
    for sym, ok in bootstrap_results.items():
        if ok:
            logger.info(f"✅ {sym} feed bootstrap verified.")
        else:
            logger.warning(f"⚠️ {sym} feed bootstrap failed or incomplete.")
    return bootstrap_results


# ==========================================================
# Mesh Registration
# ==========================================================
def register_node_in_mesh():
    """
    Register this node across all feed complexes in Redis.
    Creates entries like:
        mesh:state -> {
            "studioone_chainfeed:spx_complex": {...},
            "studioone_chainfeed:index_complex": {...},
            ...
        }
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    feed_groups = list(GROUP_SYMBOL_MAP.keys())
    logger.info(f"🕸️ Registering node '{NODE_ID}' across feed groups: {', '.join(feed_groups)}")

    for group, symbols in GROUP_SYMBOL_MAP.items():
        node_key = f"{NODE_ID}:{group}"
        state = {
            "node_id": NODE_ID,
            "group": group,
            "symbols": symbols,
            "timestamp": timestamp,
            "status": "online",
            "version": CHAINFEED_VERSION,
        }
        try:
            redis.hset(MESH_STATE_KEY, node_key, json.dumps(state))
            logger.info(f"✅ Registered {node_key} in mesh.")
        except Exception as e:
            logger.error(f"❌ Failed to register {node_key}: {e}")


# ==========================================================
# Main Startup Sequence
# ==========================================================
async def main():
    """Main node startup sequence."""
    logger.info("🧠 ChainFeed node startup initiated.")

    # Step 1: Redis connection test
    try:
        redis.ping()
        logger.info("✅ Connected to Redis.")
    except Exception as e:
        logger.critical(f"❌ Cannot connect to Redis: {e}")
        return

    # Step 2: Publish integration schema
    publish_integration_schema()

    # Step 3: Mesh registration (multi-group)
    register_node_in_mesh()

    # Step 4: Run feed bootstraps
    bootstrap_results = await run_feed_bootstraps()
    successful = [s for s, ok in bootstrap_results.items() if ok]

    if not successful:
        logger.critical("🚫 No feeds passed bootstrap validation. Node entering safe mode.")
        return
    else:
        logger.info(f"✅ Feeds verified: {', '.join(successful)}")

    # Step 5: Start heartbeat injector + watcher
    injector = HeartbeatInjector()
    watcher = HeartbeatWatcher()

    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.to_thread(injector.run))
    loop.create_task(asyncio.to_thread(watcher.run))

    logger.info(f"🚀 Node '{NODE_ID}' active with complexes: {', '.join(GROUP_SYMBOL_MAP.keys())}")

    # Keep the event loop running
    while True:
        await asyncio.sleep(10)


# ==========================================================
# Entrypoint
# ==========================================================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("🛑 Node shutdown requested by user.")
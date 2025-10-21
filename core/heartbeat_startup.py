"""
core/heartbeat_startup.py
-------------------------

ChainFeed Node Startup Coordinator
----------------------------------
Brings a ChainFeed node online, connects to Redis, synchronizes integration schema,
validates feed metadata (expirations, etc.), and starts heartbeat injector + watcher.

Critical: FeedBootstrap is used to ensure all configured feeds are metadata-ready
before allowing live heartbeats or feed activation.
"""

import asyncio
from utils.logger import get_logger
from utils.redis_client import get_redis_client
from core.integration_sync import publish_integration_schema
from core.heartbeat_injector import HeartbeatInjector
from core.heartbeat_watcher import HeartbeatWatcher
from core.feed_bootstrap import FeedBootstrap
from config.chainfeed_constants import NODE_ID, FEED_GROUPS

logger = get_logger("heartbeat.startup")
redis = get_redis_client()


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
    Run feed bootstrap validations for all configured symbols.
    Returns a dict {symbol: status_bool}.
    """
    # You can adjust this list as needed or make it dynamic from config
    symbols = ["SPX", "ES"]
    logger.info(f"🧩 Running feed bootstraps for: {', '.join(symbols)}")

    tasks = [run_bootstrap_for_symbol(sym) for sym in symbols]
    results = await asyncio.gather(*tasks)

    bootstrap_results = dict(zip(symbols, results))
    for sym, ok in bootstrap_results.items():
        if ok:
            logger.info(f"✅ {sym} feed bootstrap verified.")
        else:
            logger.warning(f"⚠️ {sym} feed bootstrap failed or incomplete.")
    return bootstrap_results


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

    # Step 3: Mesh registration (via integration schema sync)
    node_name = NODE_ID
    logger.info(f"🕸️ Registered node '{node_name}' in mesh.")

    # Step 4: Run feed bootstraps
    bootstrap_results = await run_feed_bootstraps()
    successful = [s for s, ok in bootstrap_results.items() if ok]

    if not successful:
        logger.critical("🚫 No feeds passed bootstrap validation. Node entering safe mode.")
        return
    else:
        logger.info(f"✅ Feeds verified: {', '.join(successful)}")

    # Step 5: Start heartbeat injector
    injector = HeartbeatInjector()
    watcher = HeartbeatWatcher()

    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.to_thread(injector.run))
    loop.create_task(asyncio.to_thread(watcher.run))

    logger.info(f"🚀 Node '{node_name}' active with feeds: {', '.join(successful)}")

    # Keep the event loop running
    while True:
        await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("🛑 Node shutdown requested by user.")
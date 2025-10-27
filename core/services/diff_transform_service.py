#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – DiffTransformService (v1.0)
# ===============================================================
# Computes deltas between successive Full ChainFeed frames stored in Redis.
# Publishes serialized ChainFeed(feed_type="diff") back to Redis.
# ===============================================================

import time
import threading
import logging
from core.models.chain_models import ChainFeed

class DiffTransformService(threading.Thread):
    """Continuously computes diffs between sequential Full ChainFeeds in Redis."""

    def __init__(self, redis_client, symbols, interval_sec=10, logger=None):
        super().__init__(daemon=True)
        self.redis = redis_client
        self.symbols = symbols
        self.interval = interval_sec
        self.logger = logger or logging.getLogger("DiffTransformService")
        self.running = False

    def run(self):
        self.running = True
        self.logger.info(f"🧮 DiffTransformService started (interval={self.interval}s)")
        while self.running:
            for sym in self.symbols:
                try:
                    self._compute_and_publish_diff(sym)
                except Exception as e:
                    self.logger.error(f"❌ Diff computation failed for {sym}: {e}", exc_info=True)
            time.sleep(self.interval)

    def _compute_and_publish_diff(self, symbol: str):
        latest_key = f"truth:chain:full:{symbol}"
        prev_key = f"truth:chain:full:{symbol}:prev"
        diff_key = f"truth:chain:diff:{symbol}"

        if not (self.redis.exists(latest_key) and self.redis.exists(prev_key)):
            return

        current = ChainFeed.deserialize(self.redis.get(latest_key))
        previous = ChainFeed.deserialize(self.redis.get(prev_key))

        diff_feed = current.to_diff(previous)
        self.redis.set(diff_key, diff_feed.persistable())
        self.logger.info(f"📊 Published diff ChainFeed for {symbol} → {diff_key}")

    def stop(self):
        self.running = False
        self.logger.info("🛑 DiffTransformService stopped gracefully.")
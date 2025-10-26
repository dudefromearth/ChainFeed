#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Feed Orchestration Service (Phase 3.5)
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
#  Orchestrates initialization of data providers, feed workers,
#  and external data sources such as RSS-based alert feeds.
#
#  Phase 3.5 integrates:
#   • Market-aware validation (via MarketStateValidator)
#   • Synthetic-safe startup logic
#   • RSSFeedIngestor for Google Alerts / News Streams
#
# Publishes:
#   truth:feed:{symbol}:status
#   truth:feed:rss:{source}:latest
#   truth:feed:rss:{source}:history
# ===============================================================

import json
import time
import threading
from datetime import datetime, timezone

from core.startup.services.market_state_validator import MarketStateValidator
from core.startup.services.rss_feed_ingestor import RSSFeedIngestor


# ---------------------------------------------------------------
# 🧩 FeedWorker (stub for live ingestion)
# ---------------------------------------------------------------
class FeedWorker(threading.Thread):
    """Represents a single symbol’s ingestion loop."""

    def __init__(self, redis_client, symbol: str, interval: int, logger):
        super().__init__(daemon=True)
        self.redis = redis_client
        self.symbol = symbol
        self.interval = interval
        self.logger = logger
        self.running = True

    def run(self):
        self.logger.info(f"🧩 FeedWorker started for {self.symbol} (interval={self.interval}s)")
        while self.running:
            try:
                ts = datetime.now(timezone.utc).isoformat()
                key = f"truth:feed:{self.symbol}:status"
                self.redis.set(key, json.dumps({"timestamp": ts, "status": "active"}))
                self.logger.debug(f"[{self.symbol}] heartbeat → {key}")
            except Exception as e:
                self.logger.error(f"[{self.symbol}] worker error: {e}", exc_info=True)
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.logger.info(f"🛑 FeedWorker stopped for {self.symbol}")


# ---------------------------------------------------------------
# 🧠 FeedOrchestrationService
# ---------------------------------------------------------------
class FeedOrchestrationService:
    """Coordinates all provider and feed worker initialization."""

    def __init__(self, redis_client, truth_cfg, logger):
        self.redis = redis_client
        self.truth = truth_cfg or {}
        self.logger = logger
        self.providers = {}
        self.feed_workers = []
        self.rss_ingestors = []
        self.running = False
        self.market_validator = MarketStateValidator()

    # -----------------------------------------------------------
    # 🔌 Initialize and Register Providers
    # -----------------------------------------------------------
    def _init_providers(self):
        providers = self.truth.get("providers", {}).get("data_providers", {})
        if not providers:
            self.logger.warning("⚠️ No data providers defined in Truth.")
            return

        active = []
        for name, cfg in providers.items():
            if not cfg.get("enabled", False):
                self.logger.info(f"⏸️ Provider {name} disabled in Truth.")
                continue
            active.append(name)
            try:
                status_key = f"truth:provider:{name}:status"
                meta_key = f"truth:provider:{name}:metadata"
                self.redis.set(status_key, "connected")
                self.redis.set(meta_key, json.dumps(cfg))
                self.logger.info(f"✅ Provider {name} registered and marked connected.")
            except Exception as e:
                self.logger.error(f"❌ Provider registration failed for {name}: {e}")

        registry = {"providers": active, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.redis.set("truth:feed:registry", json.dumps(registry))
        self.logger.info(f"📡 Provider registry published → {registry}")

    # -----------------------------------------------------------
    # 🧩 Initialize Feed Workers (market-aware)
    # -----------------------------------------------------------
    def _init_feeds(self):
        chainfeed = self.truth.get("chainfeed", {})
        symbols = chainfeed.get("default_symbols", [])
        feed_scope = chainfeed.get("feed_scope", {}).get("default", {})
        interval = int(feed_scope.get("update_interval_sec", 10))

        if not symbols:
            self.logger.warning("⚠️ No default symbols defined in Truth.")
            return

        self.logger.info(f"🚀 Launching feed workers for symbols: {symbols}")

        for sym in symbols:
            valid, reason = self.market_validator.validate_feed_availability(sym)
            if not valid:
                self.logger.warning(f"⚠️ Feed for {sym} skipped: {reason}")
                val_key = f"truth:feed:{sym}:validation"
                self.redis.set(
                    val_key,
                    json.dumps({
                        "symbol": sym,
                        "valid": valid,
                        "reason": reason,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }),
                )
                continue

            worker = FeedWorker(self.redis, sym, interval, self.logger)
            worker.start()
            self.feed_workers.append(worker)
            self.logger.info(f"✅ Worker thread started for {sym}")

    # -----------------------------------------------------------
    # 📰 Initialize RSS Feeds (Google Alerts, etc.)
    # -----------------------------------------------------------
    def _init_rss_feeds(self):
        rss_feeds = self.truth.get("providers", {}).get("rss_feeds", {})
        if not rss_feeds:
            self.logger.info("📰 No RSS feeds configured in Truth.")
            return

        for name, cfg in rss_feeds.items():
            if not cfg.get("enabled", False):
                self.logger.info(f"⏸️ RSS feed group {name} disabled.")
                continue

            try:
                ingestor = RSSFeedIngestor(self.redis, cfg, self.logger)
                ingestor.start()
                self.rss_ingestors.append(ingestor)
                self.logger.info(f"🗞️ RSSFeedIngestor started for {name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to start RSSFeedIngestor for {name}: {e}", exc_info=True)

    # -----------------------------------------------------------
    # 🌿 Start Service
    # -----------------------------------------------------------
    def start(self):
        self.logger.info("🌿 Starting Feed Orchestration Service...")
        self.running = True

        try:
            self._init_providers()
            self._init_feeds()
            self._init_rss_feeds()
            self.logger.info("✅ Feed Orchestration Service fully initialized.")
        except Exception as e:
            self.logger.error(f"❌ Feed Orchestration Service startup failed: {e}", exc_info=True)
            self.running = False

    # -----------------------------------------------------------
    # 🛑 Stop Service
    # -----------------------------------------------------------
    def stop(self):
        self.logger.info("🛑 Stopping Feed Orchestration Service...")
        self.running = False

        for worker in self.feed_workers:
            worker.stop()

        for rss in self.rss_ingestors:
            rss.stop()

        self.logger.info("🌳 All feed workers and RSS ingestors stopped gracefully.")
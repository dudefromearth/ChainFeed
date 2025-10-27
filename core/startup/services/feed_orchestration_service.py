#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Feed Orchestration Service (Type-Safe Refactor)
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
#  Orchestrates initialization of data providers, feed workers,
#  and external data sources such as RSS-based alert feeds.
#
#  Refactor Summary:
#   • Replaced untyped JSON payloads with typed models
#     (FeedStatusPayload, FeedRegistryPayload)
#   • Ensures consistent, schema-validated serialization
# ===============================================================

import time
import threading

from core.startup.services.market_state_validator import MarketStateValidator
from core.startup.services.rss_feed_ingestor import RSSFeedIngestor
from core.models.truth_models import FeedStatusPayload, FeedRegistryPayload


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
                payload = FeedStatusPayload(
                    node_id="studiotwo.local_chainfeed",
                    status="active",
                    feed_group=self.symbol,
                    item_count=0,
                    active=True
                )
                key = f"truth:feed:{self.symbol}:status"
                self.redis.set(key, payload.model_dump_json())
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
                meta_key = f"truth:provider:{name}:metadata"
                payload = FeedStatusPayload(
                    node_id="studiotwo.local_chainfeed",
                    status="connected",
                    feed_group=name,
                    item_count=len(cfg.get("sources", [])) if "sources" in cfg else 0,
                    active=True
                )
                self.redis.set(meta_key, payload.model_dump_json())
                self.logger.info(f"✅ Provider {name} registered and marked connected.")
            except Exception as e:
                self.logger.error(f"❌ Provider registration failed for {name}: {e}")

        try:
            registry_payload = FeedRegistryPayload(
                node_id="studiotwo.local_chainfeed",
                status="active",
                rss_groups=active
            )
            self.redis.set("truth:feed:registry", registry_payload.model_dump_json())
            self.logger.info(f"📡 Provider registry published → {active}")
        except Exception as e:
            self.logger.error(f"❌ Failed to publish provider registry: {e}", exc_info=True)

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
            # ============================================================
            # ⚠️ TEMPORARY VALIDATION BYPASS
            # ------------------------------------------------------------
            # The IsItTradable validator will be implemented later tonight.
            # For now, all feeds are permitted so we can test live chain
            # ingestion (ES, SPY, etc.) without time-based restrictions.
            # ============================================================
            valid = True
            reason = "Validation temporarily disabled for live chain testing"

            # Original validation (to be re-enabled later):
            # valid, reason = self.market_validator.validate_feed_availability(sym)

            if not valid:
                self.logger.warning(f"⚠️ Feed for {sym} skipped: {reason}")
                val_key = f"truth:feed:{sym}:validation"
                payload = FeedStatusPayload(
                    node_id="studiotwo.local_chainfeed",
                    status="invalid",
                    feed_group=sym,
                    item_count=0,
                    active=False
                )
                self.redis.set(val_key, payload.model_dump_json())
                continue

            worker = FeedWorker(self.redis, sym, interval, self.logger)
            worker.start()
            self.feed_workers.append(worker)
            self.logger.info(f"✅ Worker thread started for {sym}")

    # -----------------------------------------------------------
    # 🧱 Initialize Raw Chain Feeds (new)
    # -----------------------------------------------------------
    def _init_raw_chain_feeds(self):
        """Starts background ingestors for Raw option chains."""
        chainfeed = self.truth.get("chainfeed", {})
        raw_cfg = chainfeed.get("raw", {})

        symbols = chainfeed.get("default_symbols", [])

        if not (raw_cfg.get("enabled") and symbols):
            self.logger.info("ℹ️ Raw chain feed disabled or no symbols defined.")
            return

        from core.ingestors.raw_chain_ingestor import RawChainIngestor

        for sym in symbols:
            try:
                ingestor = RawChainIngestor(self.redis, self.truth, sym, self.logger)
                ingestor.start()
                self.feed_workers.append(ingestor)
                self.logger.info(f"✅ Raw chain ingestor started for {sym}")
            except Exception as e:
                self.logger.error(f"❌ Failed to start Raw chain ingestor for {sym}: {e}", exc_info=True)

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
            self._init_raw_chain_feeds()  # ✅ NEW — Raw Chain Integration

            # -----------------------------------------------------------
            # 🌱 Safe debug: Inspect chainfeed + raw config if present
            # -----------------------------------------------------------
            chain_cfg = self.truth.get("chainfeed", {})
            raw_cfg = chain_cfg.get("raw", {})
            default_symbols = chain_cfg.get("default_symbols", [])

            self.logger.info(f"🧭 DEBUG chainfeed config → {chain_cfg}")
            self.logger.info(f"🧭 DEBUG raw_cfg → {raw_cfg}")
            self.logger.info(f"🧭 DEBUG default_symbols → {default_symbols}")
            # -----------------------------------------------------------

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
#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Startup Sequence (v1.2)
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Orchestrates ChainFeed system initialization using modular
# service components. Each subsystem (Truth, Heartbeat, etc.)
# owns its own lifecycle and reports status back to the orchestrator.
#
# New in v1.2:
#   • Added Step 6b — Synthetic Spot Service integration
#   • Publishes SPX_synth / NDX_synth synthetic spot prices to Redis
#   • Graceful shutdown for RSS Feed Ingestors
# ===============================================================

import logging
import os
import redis
import json
import time
import threading
from datetime import datetime, timezone

from core.startup.services.truth_service import TruthService
from core.startup.services.heartbeat_service import HeartbeatService
from core.startup.services.entity_seat_service import EntitySeatService
from core.startup.services.entity_arrival_service import EntityArrivalService
from core.startup.services.feed_orchestration_service import FeedOrchestrationService
from core.services.synthetic_spot_service import SyntheticSpotService
from core.startup.services.rss_feed_ingestor import RSSFeedIngestor


class StartupSequence:
    def __init__(self):
        # --- Logging setup ---
        self.logger = logging.getLogger("StartupSequence")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%H:%M:%S"
        )

        self.logger.info("🌿 ChainFeed Startup Sequence (v1.2)")
        self.status = {}
        self.redis_client = None
        self.truth_service = None
        self.heartbeat_service = None
        self.truth_cfg = None
        self.synthetic_spot = None

        # --- Runtime service references ---
        self.rss_ingestors = []  # 🗞️ RSS feed threads (Google + Financial)

    # -----------------------------------------------------------
    # 🌿 Step 1: Connect to Redis
    # -----------------------------------------------------------
    def connect_redis(self):
        try:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            self.redis_client = redis.StrictRedis(
                host=host, port=port, decode_responses=True
            )
            self.redis_client.ping()
            self.logger.info(f"✅ Redis connection established at {host}:{port}")
            self.status["redis"] = "ok"
        except Exception as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
            self.status["redis"] = "error"
            raise

    # -----------------------------------------------------------
    # 🌿 Step 2: Initialize Core Services (Truth + Heartbeat)
    # -----------------------------------------------------------
    def init_core_services(self):
        try:
            self.truth_service = TruthService(self.redis_client, self.logger)
            self.truth_service.start()
            self.truth_cfg = self.truth_service.truth_cfg
            self.logger.info("✅ TruthService loaded and active.")
            self.status["truth"] = "ok"

            self.heartbeat_service = HeartbeatService(
                self.redis_client, self.truth_cfg, self.logger
            )
            self.heartbeat_service.start()
            self.logger.info("✅ HeartbeatService started.")
            self.status["heartbeat"] = "ok"

        except Exception as e:
            self.logger.error(f"❌ Failed to start core services: {e}", exc_info=True)
            self.status["core_services"] = "error"
            raise

    # -----------------------------------------------------------
    # 🌿 Step 3: Feed Orchestration Service (Simplified)
    # -----------------------------------------------------------
    def init_feed_service(self):
        """Initializes the ChainFeed fetching system (stub for now)."""
        try:
            self.logger.info("🚀 Initializing ChainFeed Fetch Service (stub)...")

            # 👇 Safe no-op operation to satisfy IDE and type checkers
            _ = self.truth_cfg.get("chainfeed", {})  # harmless reference to config

            # This is where we’ll later initialize the PolygonFetcher or others.
            self.status["feed_service"] = "stub"
            self.publish_status("feed_service_initialized")
            self.logger.info("✅ ChainFeed Fetch Service stub initialized successfully.")

        except Exception as e:
            self.logger.error(f"❌ Feed Orchestration Service startup failed: {e}", exc_info=True)
            self.status["feed_service"] = "error"

    # -----------------------------------------------------------
    # 🌿 Step 3.7: Diff Transform Service
    # -----------------------------------------------------------
    def init_diff_transform_service(self):
        """Starts the DiffTransformService for continuous feed deltas."""
        try:
            from core.services.diff_transform_service import DiffTransformService

            chainfeed_cfg = self.truth_cfg.get("chainfeed", {})
            symbols = chainfeed_cfg.get("default_symbols", [])
            interval = int(chainfeed_cfg.get("diff_interval_sec", 10))

            if not symbols:
                self.logger.info("ℹ️ No symbols defined for DiffTransformService.")
                return

            self.logger.info("🚀 Initializing DiffTransformService...")

            self.diff_service = DiffTransformService(
                redis_client=self.redis_client,
                symbols=symbols,
                interval_sec=interval,
                logger=self.logger
            )
            self.diff_service.start()

            self.status["diff_transform"] = "active"
            self.publish_status("diff_transform_active")
            self.logger.info(f"✅ DiffTransformService initialized and active ({interval}s interval).")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize DiffTransformService: {e}", exc_info=True)
            self.status["diff_transform"] = "error"
            self.publish_status("diff_transform_error")

    # -----------------------------------------------------------
    # 🌿 Step 3.5: RSS Feed Ingestion Service
    # -----------------------------------------------------------
    def init_rss_feeds(self):
        """Initialize all RSS feed ingestion threads as defined in Truth."""
        try:
            rss_config = self.truth_cfg.get("providers", {}).get("rss_feeds", {})
            if not rss_config:
                self.logger.info("ℹ️ No RSS feed groups defined in Truth.")
                return

            self.logger.info("🚀 Initializing RSS Feed Ingestion Service...")

            active_groups = []
            self.rss_ingestors = []

            for group_name, group_cfg in rss_config.items():
                if not group_cfg.get("enabled", False):
                    self.logger.info(f"⏸️ RSS feed group {group_name} disabled in Truth.")
                    continue

                ingestor = RSSFeedIngestor(
                    redis_client=self.redis_client,
                    cfg=group_cfg,
                    logger=self.logger
                )
                ingestor.start()
                self.rss_ingestors.append(ingestor)
                active_groups.append(group_cfg.get("name", group_name))

                self.logger.info(
                    f"🗞️ RSS group '{group_cfg.get('name', group_name)}' started "
                    f"({len(group_cfg.get('sources', []))} sources, interval={group_cfg.get('poll_interval_sec', 600)}s)"
                )

            if active_groups:
                registry = {
                    "rss_groups": active_groups,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                self.redis_client.set("truth:feed:rss:registry", json.dumps(registry))
                self.logger.info(f"📡 RSS feed registry published → {registry}")

            self.status["rss_feeds"] = "ok"
            self.logger.info("✅ RSS Feed Ingestion Service initialized and active.")

        except Exception as e:
            self.logger.error(f"❌ RSS Feed Ingestion Service startup failed: {e}", exc_info=True)
            self.status["rss_feeds"] = "error"

    # -----------------------------------------------------------
    # 🌿 Step 4: Synthetic Spot Service
    # -----------------------------------------------------------
    def init_synthetic_spot_service(self):
        """Initializes the Synthetic Spot Service (SPX_synth / NDX_synth)."""
        self.logger.info("🚀 Initializing Synthetic Spot Service...")
        try:
            self.synthetic_spot = SyntheticSpotService(
                redis_client=self.redis_client,
                truth_cfg=self.truth_cfg,
                logger=self.logger
            )
            self.synthetic_spot.start()
            self.status["synthetic_spot"] = "active"
            self.publish_status("synthetic_spot_active")
            self.logger.info("✅ Synthetic Spot Service initialized and active.")
        except Exception as e:
            self.logger.error(f"❌ Failed to start Synthetic Spot Service: {e}", exc_info=True)
            self.status["synthetic_spot"] = "error"
            self.publish_status("synthetic_spot_error")

    # -----------------------------------------------------------
    # 🌿 Step 5: Convexity GPT Agent (Stub)
    # -----------------------------------------------------------
    def init_convexity(self):
        self.logger.info("🚀 Activating Convexity GPT (stub)...")
        time.sleep(0.5)
        self.logger.info("✅ Convexity stub started.")
        self.status["convexity"] = "stub"

    # -----------------------------------------------------------
    # 🌿 Step 6: Entity Bridge Preparation
    # -----------------------------------------------------------
    def init_entity_bridge(self):
        self.logger.info("🚀 Initializing Entity Bridge...")
        seat_service = EntitySeatService(
            redis_client=self.redis_client,
            logger=self.logger,
            truth_cfg=self.truth_cfg,
            node_id=f"{os.uname().nodename.lower()}_chainfeed"
        )
        seat_info = seat_service.prepare()

        if seat_info:
            self.status["entity_seat"] = "prepared"
            self.publish_status("entity_seat_prepared")
            arrival_service = EntityArrivalService(
                redis_client=self.redis_client,
                logger=self.logger,
                seat_info=seat_info
            )
            arrival_service.announce()
            self.status["entity_arrival"] = "announced"
            self.publish_status("entity_arrival_announced")
        else:
            self.logger.warning("⚠️ Entity seat preparation failed — skipping arrival.")
            self.status["entity_bridge"] = "skipped"
            self.publish_status("entity_bridge_skipped")

    # -----------------------------------------------------------
    # 🌿 Step 7: Runtime Loop (Stub)
    # -----------------------------------------------------------
    def init_runtime_loop(self):
        self.logger.info("🌀 Starting runtime loop (stub)...")
        time.sleep(0.5)
        self.logger.info("✅ Runtime loop stub started.")
        self.status["runtime"] = "stub"

    # -----------------------------------------------------------
    # 🌿 Publish Startup Status
    # -----------------------------------------------------------
    def publish_status(self, phase):
        if not self.redis_client:
            return
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "status": self.status
        }
        self.redis_client.set("truth:system:startup_status", json.dumps(payload))
        self.logger.info(f"📡 Published startup phase → {phase}")

    # -----------------------------------------------------------
    # 🌿 Orchestration Sequence
    # -----------------------------------------------------------
    def run(self):
        self.logger.info("🌱 Beginning startup sequence...")

        # Step 1 — Redis
        self.connect_redis()
        self.publish_status("redis_connected")

        # Step 2 — Core Services
        self.init_core_services()
        self.publish_status("core_services_started")

        # Step 3 — Feed Orchestration Service
        self.init_feed_service()
        self.publish_status("feed_service_initialized")

        # Step 3.7 — Diff Transform Service
        self.init_diff_transform_service()

        # Step 3.5 — RSS Feed Ingestion
        self.logger.info("🗞️ Initializing RSS Feed Ingestors...")
        try:
            self.init_rss_feeds()
            self.publish_status("rss_feeds_initialized")
            self.logger.info("✅ RSS Feed Ingestion Service initialized successfully.")
        except Exception as e:
            self.logger.error(f"❌ RSS Feed Ingestion Service failed: {e}", exc_info=True)
            self.status["rss_feeds"] = "error"
            self.publish_status("rss_feeds_failed")

        # Step 4 — Synthetic Spot Service
        self.init_synthetic_spot_service()
        self.publish_status("synthetic_spot_initialized")

        # Step 5 — Convexity GPT
        self.init_convexity()
        self.publish_status("convexity_initialized")

        # Step 6 — Entity Bridge
        self.init_entity_bridge()
        self.publish_status("entity_bridge_initialized")

        # Step 7 — Runtime Loop
        self.init_runtime_loop()
        self.publish_status("runtime_started")

        self.logger.info("🌱 Entity bridge established. The Path has a seat at the table.")
        self.logger.info("🌳 ChainFeed startup sequence complete.")
        self.publish_status("startup_complete")

        self.logger.info("💓 Core services running in background.")
        self.logger.info("🪶 System startup is complete and stable.")
        self.logger.info("🕓 Waiting indefinitely to maintain runtime heartbeat...")

        try:
            while True:
                time.sleep(60)

        except KeyboardInterrupt:
            self.logger.info("🛑 Shutdown signal received.")
            try:
                # --- Announce shutdown to Redis ---
                if self.redis_client:
                    payload = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "shutting_down",
                        "node_id": getattr(self.heartbeat_service, "node_id", "unknown")
                    }
                    self.redis_client.set("truth:system:shutdown_notice", json.dumps(payload))
                    self.redis_client.publish("truth:alert:system", json.dumps(payload))
                    self.logger.info("📡 Published system shutdown notice to Redis.")

                # --- Final heartbeat before stop ---
                if self.heartbeat_service and self.heartbeat_service.emitter:
                    try:
                        node_id = getattr(self.heartbeat_service, "node_id", "unknown")
                        payload = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "status": "shutting_down",
                            "node_id": node_id
                        }
                        heartbeat_key = f"truth:heartbeat:{node_id}"
                        self.redis_client.set(heartbeat_key, json.dumps(payload))
                        self.logger.info(f"💓 Final heartbeat (shutting_down) written to {heartbeat_key}.")
                    except Exception as e:
                        self.logger.error(f"Error writing final heartbeat: {e}", exc_info=True)

                # --- Gracefully stop RSS feed threads ---
                if hasattr(self, "rss_ingestors") and self.rss_ingestors:
                    self.logger.info("🛑 Stopping all RSS feed ingestors...")
                    for ingestor in self.rss_ingestors:
                        try:
                            ingestor.stop()
                            self.logger.info(f"🪶 RSS ingestor stopped → {ingestor.cfg.get('name', 'unknown')}")
                        except Exception as e:
                            self.logger.error(f"Error stopping RSS ingestor: {e}", exc_info=True)

                if hasattr(self, "diff_service") and self.diff_service:
                    self.logger.info("🛑 Stopping DiffTransformService...")
                    self.diff_service.stop()

                # --- Allow observers to register the shutdown ---
                shutdown_delay = int(os.getenv("SHUTDOWN_GRACE_DELAY", "5"))
                self.logger.info(f"🕓 Grace period before shutdown ({shutdown_delay}s)...")
                time.sleep(shutdown_delay)

            finally:
                if self.heartbeat_service:
                    self.heartbeat_service.stop()
                if self.truth_service:
                    self.truth_service.stop()
                if self.synthetic_spot:
                    self.synthetic_spot.stop()
                self.logger.info("🌳 ChainFeed node fully terminated.")


# ---------------------------------------------------------------
# 🧩 Main entry point
# ---------------------------------------------------------------
if __name__ == "__main__":
    seq = StartupSequence()
    seq.run()
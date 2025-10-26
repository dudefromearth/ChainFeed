#!/usr/bin/env python3
# ===============================================================
# 🌿 TruthService – Canonical Truth Manager
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Manages the canonical truth lifecycle:
#   - Loads from local seed file (canonical_truth.json)
#   - Syncs with Redis (truth:integration:schema)
#   - Publishes updates and listens for live schema changes
#
# Provides a stable interface for the Startup Orchestrator.
# ===============================================================

import json
from datetime import datetime, timezone
from pathlib import Path
from core.listeners.truth_listener import TruthListener


class TruthService:
    def __init__(self, redis_client, logger, schema_path="config/canonical_truth.json"):
        self.redis = redis_client
        self.logger = logger
        self.schema_path = Path(schema_path)
        self.truth_cfg = {}
        self.listener = None

    # -----------------------------------------------------------
    # 🌿 Load + Sync Truth
    # -----------------------------------------------------------
    def start(self):
        self.logger.info("📖 Starting TruthService...")
        self._load_truth()
        self._start_listener()
        self.logger.info("✅ TruthService initialized and listening for updates.")

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.logger.info("👂 TruthListener stopped gracefully.")

    # -----------------------------------------------------------
    # 🌿 Load Truth from File and Redis
    # -----------------------------------------------------------
    def _load_truth(self):
        local_truth = {}
        if self.schema_path.exists():
            with open(self.schema_path, "r") as f:
                local_truth = json.load(f)
            self.logger.info(f"📄 Loaded seed truth from {self.schema_path.name}")

        redis_raw = self.redis.get("truth:integration:schema")
        if redis_raw:
            redis_truth = json.loads(redis_raw)
            redis_ver = redis_truth.get("version")
            local_ver = local_truth.get("version")

            def vnum(v): return [int(x) for x in v.strip("v").split(".")]
            if not local_ver or vnum(redis_ver) > vnum(local_ver):
                self.logger.info(f"🌀 Using newer truth from Redis (v{redis_ver})")
                self.truth_cfg = redis_truth
            else:
                self.logger.info(f"📦 Redis truth older or equal; keeping local (v{local_ver})")
                self.truth_cfg = local_truth
                self._publish_truth(local_truth)
        else:
            self.logger.warning("⚠️ No truth found in Redis. Publishing local seed version.")
            self.truth_cfg = local_truth
            self._publish_truth(local_truth)

    # -----------------------------------------------------------
    # 🌿 Publish Truth to Redis
    # -----------------------------------------------------------
    def _publish_truth(self, truth_dict):
        self.redis.set("truth:integration:schema", json.dumps(truth_dict))
        self.logger.info("📡 Published canonical truth → truth:integration:schema")

    # -----------------------------------------------------------
    # 🌿 Publish Truth Update
    # -----------------------------------------------------------
    def publish_update(self):
        old_ver = self.truth_cfg.get("version", "v0.0.0")
        v_parts = [int(x) for x in old_ver.strip("v").split(".")]
        v_parts[-1] += 1
        new_ver = f"v{'.'.join(map(str, v_parts))}"

        self.truth_cfg["version"] = new_ver
        self.truth_cfg["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.redis.set("truth:integration:schema", json.dumps(self.truth_cfg))
        self.redis.publish("truth:update:schema", new_ver)
        self.logger.info(f"📡 Truth update published → {new_ver}")

    # -----------------------------------------------------------
    # 🌿 Start Truth Listener
    # -----------------------------------------------------------
    def _start_listener(self):
        def on_update(new_truth):
            self.logger.info(f"🔄 TruthListener received new schema (v{new_truth.get('version')})")
            self.truth_cfg = new_truth

        self.listener = TruthListener(
            redis_client=self.redis,
            on_update_callback=on_update,
            poll_interval=5,
            logger=self.logger
        )
        self.listener.start()
        self.logger.info("👂 TruthListener started.")
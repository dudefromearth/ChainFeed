#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Truth Service (v2.0, Type-Safe)
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Manages canonical truth data shared across ChainFeed nodes.
# Loads and publishes the local truth schema, synchronizes
# with Redis, and listens for external updates.
#
# v2.0 Changes:
#   • Integrated TruthSchemaPayload / TruthUpdatePayload
#   • Type-safe Redis serialization (.to_json)
#   • Schema version consistency enforcement
#   • Clean startup and listener shutdown
# ===============================================================

import json
import threading
import time
from datetime import datetime, timezone

from core.models.truth_models import TruthSchemaPayload, TruthUpdatePayload


class TruthService:
    """Central authority for canonical truth schema."""

    def __init__(self, redis_client, logger):
        self.redis = redis_client
        self.logger = logger
        self.truth_cfg = None
        self.listener_thread = None
        self.running = False
        self.key_canonical = "truth:integration:schema"
        self.channel_updates = "truth:update:schema"

    # -----------------------------------------------------------
    # 🌱 Load Canonical Truth from File
    # -----------------------------------------------------------
    def load_canonical_truth(self, file_path="canonical_truth.json"):
        """Loads canonical truth from JSON file."""
        possible_paths = [
            file_path,
            f"./{file_path}",
            f"./config/{file_path}",  # ✅ Add this line
            f"./core/config/{file_path}",
            f"/app/{file_path}",
            f"/app/config/{file_path}",  # ✅ Add this too for Docker compatibility
            f"/app/core/config/{file_path}"
        ]

        for path in possible_paths:
            try:
                with open(path, "r") as f:
                    self.truth_cfg = json.load(f)
                    version = self.truth_cfg.get("version", "v1.0")
                    self.logger.info(f"📄 Loaded seed truth from {path} (vv{version})")
                    return self.truth_cfg
            except FileNotFoundError:
                continue
            except Exception as e:
                self.logger.error(f"❌ Error reading truth file {path}: {e}", exc_info=True)

        self.logger.error(f"❌ No canonical truth file found in {possible_paths}")
        raise FileNotFoundError("canonical_truth.json not found in known locations.")

    # -----------------------------------------------------------
    # 📡 Publish Canonical Truth to Redis
    # -----------------------------------------------------------
    def publish_truth(self):
        """Publishes the loaded truth schema to Redis as a typed payload."""
        if not self.truth_cfg:
            self.logger.error("❌ Cannot publish truth: No schema loaded.")
            return

        payload = TruthSchemaPayload(
            version=self.truth_cfg.get("version", "v1.0"),
            schema=self.truth_cfg,
            source_node="local",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        self.redis.set(self.key_canonical, payload.to_json())
        self.logger.info(f"📡 Published canonical truth → {self.key_canonical}")

    # -----------------------------------------------------------
    # 🔄 Synchronize Truth with Redis
    # -----------------------------------------------------------
    def sync_with_redis(self):
        """Checks if Redis truth is newer or older than local copy."""
        try:
            redis_data = self.redis.get(self.key_canonical)
            if redis_data:
                redis_truth = json.loads(redis_data)
                redis_version = redis_truth.get("version", "v0.0")

                local_version = self.truth_cfg.get("version", "v0.0")
                if redis_version > local_version:
                    self.truth_cfg = redis_truth.get("schema", self.truth_cfg)
                    self.logger.info(f"📦 Adopted newer truth from Redis (vv{redis_version})")
                else:
                    self.logger.info(f"📦 Redis truth older or equal; keeping local (vv{local_version})")
            else:
                self.logger.warning("⚠️ No truth found in Redis. Publishing local seed version.")
                self.publish_truth()
        except Exception as e:
            self.logger.error(f"❌ Failed to synchronize truth with Redis: {e}", exc_info=True)

    # -----------------------------------------------------------
    # 👂 Start Truth Listener Thread
    # -----------------------------------------------------------
    def start_listener(self):
        """Subscribes to schema update notifications in Redis."""
        def _listen():
            pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(self.channel_updates)
            self.logger.info(f"📡 Subscribed to {self.channel_updates} channel.")
            while self.running:
                try:
                    message = pubsub.get_message(timeout=1)
                    if not message:
                        continue

                    if message["type"] == "message":
                        data = json.loads(message["data"])
                        update = TruthUpdatePayload(**data)
                        self.logger.info(f"🔄 TruthListener received new schema (vv{update.version})")
                        self.truth_cfg = update.schema
                except Exception as e:
                    self.logger.error(f"❌ TruthListener error: {e}", exc_info=True)
                    time.sleep(1)

        self.running = True
        self.listener_thread = threading.Thread(target=_listen, daemon=True)
        self.listener_thread.start()
        self.logger.info("👂 TruthListener started.")

    # -----------------------------------------------------------
    # 🚀 Start Truth Service
    # -----------------------------------------------------------
    def start(self):
        """Loads truth, syncs with Redis, publishes, and starts listener."""
        self.logger.info("📖 Starting TruthService...")
        self.load_canonical_truth()
        self.sync_with_redis()
        self.publish_truth()
        self.start_listener()
        self.logger.info("✅ TruthService initialized and listening for updates.")

    # -----------------------------------------------------------
    # 🛑 Stop Truth Service
    # -----------------------------------------------------------
    def stop(self):
        """Stops the truth listener thread gracefully."""
        self.running = False
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=3)
        self.logger.info("👂 TruthListener stopped gracefully.")
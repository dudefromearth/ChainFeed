#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Truth Listener
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-25
#
# Purpose:
# --------
# Watches Redis for updates to the canonical truth schema and
# dynamically reloads configuration in memory. This allows all
# ChainFeed nodes to stay synchronized with the global Truth.
#
# Listens on:
#   - Redis keyspace notifications for "truth:integration:schema"
#   - Optional Pub/Sub channel "truth:update:schema"
#
# On detection:
#   - Reloads JSON from Redis
#   - Updates in-memory configuration reference
#   - Logs changes and version diffs
#
# ===============================================================

import json
import time
import threading
import redis
import logging
from datetime import datetime, timezone


class TruthListener:
    def __init__(self, redis_client, on_update_callback, poll_interval=5, logger=None):
        """
        :param redis_client: Active Redis connection
        :param on_update_callback: Function to call when truth changes
        :param poll_interval: Fallback poll interval (if keyspace notifications not available)
        """
        self.redis = redis_client
        self.on_update = on_update_callback
        self.poll_interval = poll_interval
        self.logger = logger or logging.getLogger("TruthListener")
        self.running = False
        self.last_version = None
        self.thread = None

    # -----------------------------------------------------------
    # 🌿 Start Listener
    # -----------------------------------------------------------
    def start(self):
        if self.running:
            self.logger.warning("⚠️ TruthListener already running.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        self.logger.info("👂 TruthListener started (poll every %ss)." % self.poll_interval)

    # -----------------------------------------------------------
    # 🌿 Stop Listener
    # -----------------------------------------------------------
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.logger.info("🛑 TruthListener stopped.")

    # -----------------------------------------------------------
    # 🌿 Main Listen Loop
    # -----------------------------------------------------------
    def _listen_loop(self):
        """
        Attempts to use Redis Pub/Sub or keyspace notifications.
        Falls back to polling if unavailable.
        """
        try:
            pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe("truth:update:schema")
            self.logger.info("📡 Subscribed to truth:update:schema channel.")

            # Also try keyspace notifications
            try:
                self.redis.config_set("notify-keyspace-events", "KEA")
                pubsub.psubscribe("__keyspace@0__:truth:integration:schema")
                self.logger.info("🔑 Subscribed to Redis keyspace events for truth:integration:schema")
            except Exception as e:
                self.logger.warning(f"⚠️ Keyspace notifications unavailable: {e}")

            # Main loop
            while self.running:
                message = pubsub.get_message(timeout=self.poll_interval)
                if message:
                    event_type = message.get("type")
                    data = message.get("data")
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    if event_type in ("message", "pmessage"):
                        self.logger.info(f"🌀 Truth update detected via {event_type}: {data}")
                        self._reload_truth()
                else:
                    # Poll fallback
                    self._check_truth_poll()

        except Exception as e:
            self.logger.error(f"TruthListener error: {e}", exc_info=True)
            self.running = False

    # -----------------------------------------------------------
    # 🌿 Poll Fallback (if no events fired)
    # -----------------------------------------------------------
    def _check_truth_poll(self):
        try:
            raw = self.redis.get("truth:integration:schema")
            if not raw:
                return
            truth = json.loads(raw)
            version = truth.get("version", "unknown")

            if self.last_version != version:
                self.logger.info(f"🌀 Truth version changed → {self.last_version} → {version}")
                self.last_version = version
                self.on_update(truth)

        except Exception as e:
            self.logger.error(f"Polling error in TruthListener: {e}", exc_info=True)

    # -----------------------------------------------------------
    # 🌿 Reload Handler
    # -----------------------------------------------------------
    def _reload_truth(self):
        try:
            raw = self.redis.get("truth:integration:schema")
            if not raw:
                self.logger.warning("⚠️ No truth found in Redis during update event.")
                return
            truth = json.loads(raw)
            version = truth.get("version", "unknown")

            self.logger.info(f"📖 Reloaded truth from Redis (v{version}) at {datetime.now(timezone.utc).isoformat()}")
            self.last_version = version
            self.on_update(truth)

        except Exception as e:
            self.logger.error(f"Failed to reload truth: {e}", exc_info=True)
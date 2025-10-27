#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Heartbeat Emitter (v2.0, Type-Safe)
# ===============================================================
# Author: StudioTwo Build Lab / Convexity GPT
# Date:   2025-10-26
#
# Purpose:
# --------
# Emits periodic heartbeat messages to Redis indicating
# node liveness, health, and operational mode.
#
# v2.0 Changes:
#   • Integrated with HeartbeatPayload (type-safe schema)
#   • Auto timestamps and schema versioning
#   • Clean stop signal handling
# ===============================================================

import time
import threading
from core.models.truth_models import HeartbeatPayload


class HeartbeatEmitter:
    """Publishes liveness heartbeats for this node into Redis."""

    def __init__(
        self,
        redis_client,
        node_id: str,
        interval: int = 15,
        mode: str = "LIVE",
        version: str = "v1.0",
        logger=None,
    ):
        self.redis = redis_client
        self.node_id = node_id
        self.interval = interval
        self.mode = mode
        self.version = version
        self.logger = logger
        self.key = f"truth:heartbeat:{node_id}"
        self.running = False
        self.thread = None

    # -----------------------------------------------------------
    # 🌱 Start Emitter Thread
    # -----------------------------------------------------------
    def start(self):
        if self.running:
            if self.logger:
                self.logger.warning("💓 HeartbeatEmitter already running.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        if self.logger:
            self.logger.info(f"💓 HeartbeatEmitter started (interval={self.interval}s).")

    # -----------------------------------------------------------
    # 🧠 Main Heartbeat Loop
    # -----------------------------------------------------------
    def _run(self):
        while self.running:
            try:
                payload = HeartbeatPayload(
                    node_id=self.node_id,
                    status="alive",
                    mode=self.mode,
                    version=self.version,
                    heartbeat_interval=self.interval,
                )

                self.redis.set(self.key, payload.to_json())

                if self.logger:
                    self.logger.info(f"💓 Heartbeat published → {self.key}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"❌ HeartbeatEmitter error: {e}", exc_info=True)
            time.sleep(self.interval)

    # -----------------------------------------------------------
    # 🛑 Stop Emitter
    # -----------------------------------------------------------
    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=self.interval)
        if self.logger:
            self.logger.info("💓 HeartbeatEmitter stopped gracefully.")
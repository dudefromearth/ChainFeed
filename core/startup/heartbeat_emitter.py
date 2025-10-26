#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Heartbeat Emitter
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-25
#
# Purpose:
# --------
# Provides a continuous heartbeat signal to Redis indicating
# system health, identity, and runtime phase.
#
# Publishes every N seconds (default 15) under:
#   truth:heartbeat:{node_id}
#
# JSON Payload Example:
# {
#   "node_id": "studio2_chainfeed",
#   "timestamp": "2025-10-25T12:14:00Z",
#   "status": "alive",
#   "mode": "LIVE",
#   "version": "v2.0"
# }
#
# ===============================================================

import threading
import time
import json
from datetime import datetime, timezone


class HeartbeatEmitter:
    def __init__(self, redis_client, node_id: str, interval: int = 15, mode: str = "LIVE", version: str = "v2.0", logger=None):
        self.redis = redis_client
        self.node_id = node_id
        self.interval = interval
        self.mode = mode
        self.version = version
        self.logger = logger
        self.key = f"truth:heartbeat:{node_id}"
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            if self.logger:
                self.logger.warning("💓 HeartbeatEmitter already running.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if self.logger:
            self.logger.info(f"💓 HeartbeatEmitter started (interval={self.interval}s) for node: {self.node_id}")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.logger:
            self.logger.info("💓 HeartbeatEmitter stopped.")

    def _run(self):
        while self.running:
            try:
                payload = {
                    "node_id": self.node_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "alive",
                    "mode": self.mode,
                    "version": self.version
                }
                self.redis.set(self.key, json.dumps(payload))
                if self.logger:
                    self.logger.info(f"💓 Heartbeat published → {self.key}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"HeartbeatEmitter error: {e}", exc_info=True)

            time.sleep(self.interval)
#!/usr/bin/env python3
# ===============================================================
# 🌿 StartupStatusListener – Mesh Startup Progress Tracker
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Monitors the Redis key `truth:system:startup_status` and logs
# progress updates for each node in a multi-node federation.
#
# Useful for orchestrators, observers, and Convexity agents that
# must understand which nodes are active, ready, or blocked.
#
# Behavior:
#   - Polls Redis for updates to startup_status
#   - Detects node state transitions (initializing → ready)
#   - Optionally invokes callback for external UI or logging
#
# Redis Keys:
#   truth:system:startup_status
# ===============================================================

import json
import time


class StartupStatusListener:
    def __init__(self, redis_client, logger, poll_interval=5, callback=None):
        self.redis = redis_client
        self.logger = logger
        self.poll_interval = poll_interval
        self.callback = callback
        self.running = False

    def start(self):
        """Start monitoring the startup status key."""
        self.logger.info("👁️ StartupStatusListener activated.")
        self.running = True
        last_status = None

        try:
            while self.running:
                raw = self.redis.get("truth:system:startup_status")
                if raw and raw != last_status:
                    last_status = raw
                    try:
                        data = json.loads(raw)
                        phase = data.get("phase", "?")
                        status = data.get("status", {})
                        node = data.get("node_id", "unknown")
                        self.logger.info(f"📡 Startup phase update [{phase}] from {node}")
                        if self.callback:
                            self.callback(data)
                    except Exception:
                        self.logger.warning("⚠️ Invalid JSON in startup status.")
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            self.logger.info("🛑 StartupStatusListener interrupted.")
        finally:
            self.running = False
            self.logger.info("👂 StartupStatusListener stopped gracefully.")

    def stop(self):
        """Stop monitoring."""
        self.running = False
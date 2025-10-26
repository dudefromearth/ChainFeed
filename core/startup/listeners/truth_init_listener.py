#!/usr/bin/env python3
# ===============================================================
# 🌿 TruthInitListener – Canonical Truth Gatekeeper
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Ensures the node does not proceed with startup until the
# canonical truth schema (`truth:integration:schema`) is present
# and readable from Redis.
#
# Used when a node is a follower in the mesh and must wait for
# the hub node to publish the canonical truth before proceeding.
#
# Behavior:
#   - Poll Redis periodically for the schema key
#   - Validate that the truth object is valid JSON
#   - Return loaded schema or None on timeout
#
# Redis Keys:
#   truth:integration:schema
# ===============================================================

import json
import time


class TruthInitListener:
    def __init__(self, redis_client, logger, poll_interval=2, timeout=30):
        self.redis = redis_client
        self.logger = logger
        self.poll_interval = poll_interval
        self.timeout = timeout

    def wait_for_truth(self):
        """Block until truth:integration:schema is available in Redis."""
        self.logger.info("⏳ Waiting for canonical truth to appear in Redis...")
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            raw = self.redis.get("truth:integration:schema")
            if raw:
                try:
                    truth = json.loads(raw)
                    ver = truth.get("version", "unknown")
                    self.logger.info(f"✅ Canonical truth detected (v{ver}).")
                    return truth
                except Exception:
                    self.logger.warning("⚠️ Invalid truth JSON detected; retrying...")
            time.sleep(self.poll_interval)

        self.logger.error("❌ Timeout waiting for canonical truth in Redis.")
        return None
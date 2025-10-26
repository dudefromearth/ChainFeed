#!/usr/bin/env python3
# ===============================================================
# 🌿 MeshReadyListener – Final Synchronization Barrier
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Waits for a `truth:mesh:ready` signal in Redis before allowing
# final activation of runtime services.
#
# Acts as the synchronization barrier between node-level startup
# and full mesh readiness (hub + spoke convergence).
#
# Behavior:
#   - Polls Redis or subscribes to Pub/Sub for mesh readiness flag
#   - Returns True once the mesh is ready or after timeout
#
# Redis Keys:
#   truth:mesh:ready
# ===============================================================

import time


class MeshReadyListener:
    def __init__(self, redis_client, logger, poll_interval=3, timeout=60):
        self.redis = redis_client
        self.logger = logger
        self.poll_interval = poll_interval
        self.timeout = timeout

    def wait_for_mesh_ready(self):
        """Block until the mesh readiness key appears or times out."""
        self.logger.info("⏳ Waiting for mesh readiness signal (truth:mesh:ready)...")
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            ready = self.redis.get("truth:mesh:ready")
            if ready and ready.lower() == "true":
                self.logger.info("✅ Mesh readiness confirmed.")
                return True
            time.sleep(self.poll_interval)

        self.logger.warning("⚠️ Timeout waiting for mesh readiness; proceeding cautiously.")
        return False
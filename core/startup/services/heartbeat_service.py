#!/usr/bin/env python3
# ===============================================================
# 💓 HeartbeatService – Node Liveness and Health
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Initializes and manages the node heartbeat emitter
# and the heartbeat monitor. Handles graceful shutdown.
#
# Redis Keys:
#   truth:heartbeat:{node_id}
#   truth:alert:{node_id}
# ===============================================================

import os
import threading
from core.startup.heartbeat_emitter import HeartbeatEmitter
from core.listeners.heartbeat_monitor import HeartbeatMonitor


class HeartbeatService:
    def __init__(self, redis_client, truth_cfg, logger):
        self.redis = redis_client
        self.truth = truth_cfg
        self.logger = logger
        self.emitter = None
        self.monitor = None
        self.node_id = None

    # -----------------------------------------------------------
    # 🌿 Start Heartbeat Service
    # -----------------------------------------------------------
    def start(self):
        mesh_cfg = self.truth.get("mesh", {})
        interval = mesh_cfg.get("heartbeat_interval_sec", 15)
        max_age = mesh_cfg.get("max_heartbeat_age_sec", 20)
        self.node_id = mesh_cfg.get("node_id") or f"{os.uname().nodename.lower()}_chainfeed"

        self.emitter = HeartbeatEmitter(
            redis_client=self.redis,
            node_id=self.node_id,
            interval=interval,
            mode="LIVE",
            version=self.truth.get("version", "vX"),
            logger=self.logger
        )
        self.emitter.start()

        self.monitor = HeartbeatMonitor(
            redis_client=self.redis,
            check_interval=interval,
            max_age=max_age,
            logger=self.logger
        )
        threading.Thread(target=self.monitor.start, daemon=True).start()

        self.logger.info(f"💓 HeartbeatService started for node {self.node_id} (interval={interval}s).")

    # -----------------------------------------------------------
    # 🌿 Stop Heartbeat Service
    # -----------------------------------------------------------
    def stop(self):
        if self.emitter:
            self.emitter.stop()
            self.logger.info("💓 HeartbeatEmitter stopped gracefully.")
        if self.monitor:
            self.monitor.running = False
            self.logger.info("👁️ HeartbeatMonitor stopped gracefully.")
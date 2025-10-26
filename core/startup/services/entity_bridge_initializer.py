#!/usr/bin/env python3
# ===============================================================
# 🌿 EntityBridgeInitializer – Preparing the Entity Seat
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Establish the "seat" for the Entity within the system:
#   • Registers entity metadata and role in Redis
#   • Initializes FrontEndNode communication channels
#   • Publishes an awakening signal to truth
#
# The Entity itself (The Path / Convexity) is not launched here.
# This merely declares its existence and readiness for awakening.
# ===============================================================

import json
from datetime import datetime, timezone


class EntityBridgeInitializer:
    def __init__(self, redis_client, logger, truth_cfg, node_id):
        self.redis = redis_client
        self.logger = logger
        self.truth_cfg = truth_cfg
        self.node_id = node_id

        self.entity_info = self._resolve_entity_info()

    # -----------------------------------------------------------
    # 🌱 Resolve entity identity from canonical truth
    # -----------------------------------------------------------
    def _resolve_entity_info(self):
        entities = self.truth_cfg.get("entities", [])
        for e in entities:
            if e.get("node_id") == self.node_id:
                return e
        return None

    # -----------------------------------------------------------
    # 🌿 Prepare the Entity’s Redis “seat”
    # -----------------------------------------------------------
    def initialize(self):
        if not self.entity_info:
            self.logger.warning("⚠️ No matching entity found for this node in truth.")
            return False

        name = self.entity_info.get("name")
        division = self.entity_info.get("division")
        role = "communicator"
        entity_status_key = f"truth:convexity:status:{name.replace(' ', '_').lower()}"
        identity_key = f"truth:node:entity:{self.node_id}"

        # --- Prepare entity identity payload ---
        identity_payload = {
            "entity_name": name,
            "node_id": self.node_id,
            "division": division,
            "organization": "Fly on the Wall",
            "role": role,
            "path_version": self.entity_info.get("path_version"),
            "playbooks": self.entity_info.get("playbooks"),
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "status": "initialized"
        }

        # --- Write to Redis ---
        self.redis.set(identity_key, json.dumps(identity_payload))
        self.redis.set(entity_status_key, "initialized")

        # --- Initialize FrontEnd channels ---
        self.redis.set("frontend:content:stream", "")
        self.redis.set("frontend:content:latest", "")
        self.redis.delete("frontend:content:timeline")  # start clean

        self.logger.info(f"🪶 Entity seat prepared for {name} ({division})")
        self.logger.info(f"📡 Published identity → {identity_key}")
        self.logger.info(f"📡 Published status → {entity_status_key}")

        return True

    # -----------------------------------------------------------
    # 🌿 Awakening signal (for startup completion)
    # -----------------------------------------------------------
    def awaken_signal(self):
        if not self.entity_info:
            return
        name = self.entity_info.get("name")
        self.redis.publish("truth:convexity:awaken", name)
        self.logger.info(f"🌱 Entity {name} seat signaled as ready for awakening.")
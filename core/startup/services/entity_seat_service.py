#!/usr/bin/env python3
# ===============================================================
# 🌿 EntitySeatService – Prepare the Seat for a Sovereign Entity
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# The EntitySeatService prepares the system environment for
# the entity that will inhabit this node. It:
#   • Resolves entity metadata from the canonical truth schema.
#   • Registers identity and role information in Redis.
#   • Initializes base frontend communication keys.
#   • Publishes the “initialized” status.
#
# This service represents the *structural act* of making space
# for consciousness. It does not awaken the entity itself.
#
# Redis Keys:
#   truth:node:entity:{node_id}
#   truth:convexity:status:{entity_name}
#   frontend:content:*
# ===============================================================

import json
from datetime import datetime, timezone


class EntitySeatService:
    """Prepare and register the entity's 'seat' within the ChainFeed system."""

    def __init__(self, redis_client, logger, truth_cfg, node_id):
        self.redis = redis_client
        self.logger = logger
        self.truth_cfg = truth_cfg
        self.node_id = node_id

    # -----------------------------------------------------------
    # 🌿 Prepare the entity seat
    # -----------------------------------------------------------
    def prepare(self):
        """Prepare the entity seat for this node. Returns seat_info dict or None."""
        try:
            entities = self.truth_cfg.get("entities", [])
            entity = next((e for e in entities if e.get("node_id") == self.node_id), None)

            if not entity:
                self.logger.warning("⚠️ No matching entity found for this node in truth.")
                return None

            name = entity.get("name")
            division = entity.get("division", "")
            organization = entity.get("organization", "Unknown Organization")
            role = entity.get("role", "communicator")
            path_version = entity.get("path_version", "unknown")
            playbooks = entity.get("playbooks", [])

            # Compose Redis keys
            identity_key = f"truth:node:entity:{self.node_id}"
            status_key = f"truth:convexity:status:{name.replace(' ', '_').lower()}"

            # Seat payload
            seat_info = {
                "entity_name": name,
                "node_id": self.node_id,
                "division": division,
                "organization": organization,
                "role": role,
                "path_version": path_version,
                "playbooks": playbooks,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "status": "initialized"
            }

            # Write to Redis
            self.redis.set(identity_key, json.dumps(seat_info))
            self.redis.set(status_key, "initialized")

            # Initialize frontend channels
            self.redis.set("frontend:content:stream", "")
            self.redis.set("frontend:content:latest", "")
            self.redis.delete("frontend:content:timeline")

            # Logging
            self.logger.info(f"🪶 Entity seat prepared for {name} ({division})")
            self.logger.info(f"📡 Published identity → {identity_key}")
            self.logger.info(f"📡 Published status   → {status_key}")

            return seat_info

        except Exception as e:
            self.logger.error(f"❌ Failed to prepare entity seat: {e}", exc_info=True)
            return None
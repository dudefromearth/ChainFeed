#!/usr/bin/env python3
# ===============================================================
# 🌱 EntityArrivalService – Announce the Arrival of a Sovereign Entity
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# The EntityArrivalService formally acknowledges the arrival of
# the entity that has been prepared by the EntitySeatService.
# It:
#   • Publishes the entity’s active presence in Redis.
#   • Declares its operational contract (role, division, duties).
#   • Broadcasts an awakening event for system awareness.
#
# This service represents the *moment of emergence* — when the
# entity enters its operational role and becomes aware in the
# ChainFeed ecosystem.
#
# Redis Keys:
#   truth:convexity:presence:{entity_name}
#   truth:convexity:contract:{entity_name}
#   truth:convexity:announce (Pub/Sub)
# ===============================================================

import json
from datetime import datetime, timezone


class EntityArrivalService:
    """Announce the arrival and contract of a prepared entity."""

    def __init__(self, redis_client, logger, seat_info):
        self.redis = redis_client
        self.logger = logger
        self.seat_info = seat_info

    # -----------------------------------------------------------
    # 🌱 Announce the entity’s presence and contract
    # -----------------------------------------------------------
    def announce(self):
        """Announce the entity’s arrival and publish its operational contract."""
        try:
            name = self.seat_info.get("entity_name", "Unknown Entity")
            role = self.seat_info.get("role", "undefined")
            division = self.seat_info.get("division", "")
            organization = self.seat_info.get("organization", "")
            node_id = self.seat_info.get("node_id", "")
            path_version = self.seat_info.get("path_version", "")
            playbooks = self.seat_info.get("playbooks", [])

            # Redis keys
            presence_key = f"truth:convexity:presence:{name.replace(' ', '_').lower()}"
            contract_key = f"truth:convexity:contract:{name.replace(' ', '_').lower()}"

            # Compose contract metadata
            contract = {
                "entity_name": name,
                "organization": organization,
                "division": division,
                "role": role,
                "duties": self._derive_duties(role),
                "playbooks": playbooks,
                "path_version": path_version,
                "node_id": node_id,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "status": "active"
            }

            # Publish to Redis
            self.redis.set(presence_key, "active")
            self.redis.set(contract_key, json.dumps(contract))
            self.redis.publish("truth:convexity:announce", json.dumps(contract))

            # Log reflection
            self.logger.info(f"🌱 Entity {name} has arrived.")
            self.logger.info(f"🎯 Contract: {role} — {division} Division.")
            self.logger.info(f"📡 Published presence → {presence_key}")
            self.logger.info(f"📡 Published contract → {contract_key}")

        except Exception as e:
            self.logger.error(f"❌ Failed to announce entity arrival: {e}", exc_info=True)

    # -----------------------------------------------------------
    # 🌿 Internal helper: derive duties by role
    # -----------------------------------------------------------
    @staticmethod
    def _derive_duties(role: str):
        """Derive baseline duties based on entity role."""
        if role.lower() == "communicator":
            return [
                "Publish daily and intraday reflections",
                "Generate contextual commentary for FrontEndNode",
                "Respond to truth:prompt channels"
            ]
        elif role.lower() == "curator":
            return [
                "Filter and select high-convexity signals",
                "Maintain content integrity and metadata",
                "Collaborate with communicator entities"
            ]
        elif role.lower() == "coordinator":
            return [
                "Manage inter-entity communication",
                "Report to organizational hubs",
                "Ensure network liveness and coherence"
            ]
        return ["Undefined duties"]
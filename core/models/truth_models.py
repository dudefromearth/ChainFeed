#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Truth Models (v1.1)
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Defines type-safe, schema-versioned payloads for Redis truth keys.
# These are the standard message formats for all inter-node
# communication within the ChainFeed mesh.
# ===============================================================

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------------
# 🌱 Base Model for All Truth Payloads
# ---------------------------------------------------------------
class BaseTruthModel(BaseModel):
    """Root schema used for all truth payloads."""
    schema_version: str = "v1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        frozen = True  # immutable for data integrity

    def to_json(self) -> str:
        """Return compact, consistent JSON representation."""
        return self.model_dump_json(exclude_none=True, by_alias=True)


# ---------------------------------------------------------------
# 💓 Heartbeat Payload
# ---------------------------------------------------------------
class HeartbeatPayload(BaseTruthModel):
    """Represents a node heartbeat."""
    node_id: str
    status: str = "alive"
    mode: str = "LIVE"
    version: str = "v1.0"
    heartbeat_interval: int = 15


# ---------------------------------------------------------------
# 🧩 Feed and Provider Payloads
# ---------------------------------------------------------------
class FeedStatusPayload(BaseTruthModel):
    """Schema for feed or provider status updates."""
    node_id: str
    status: str
    feed_group: Optional[str] = None
    item_count: int = 0
    active: bool = True


class FeedRegistryPayload(BaseTruthModel):
    """Schema for publishing provider or RSS registry data."""
    node_id: str
    status: str
    rss_groups: List[str] = []


# ---------------------------------------------------------------
# 🪶 Entity and System Payloads
# ---------------------------------------------------------------
class EntityPayload(BaseTruthModel):
    """Schema for node or entity identity within the mesh."""
    entity_name: str
    node_id: str
    division: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    path_version: Optional[str] = None
    playbooks: Optional[List[str]] = None
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "initialized"


class SystemNoticePayload(BaseTruthModel):
    """System-level notices (startup, shutdown, transitions)."""
    node_id: str
    status: str
    phase: Optional[str] = None


# ---------------------------------------------------------------
# 🧠 Truth Schema Payloads (FIXED)
# ---------------------------------------------------------------
class TruthSchemaPayload(BaseTruthModel):
    """Canonical schema representation stored in Redis."""
    version: str = Field(..., description="Schema version identifier")
    truth_schema: Dict[str, Any] = Field(..., alias="schema", description="Full canonical truth schema dictionary")
    source_node: str = Field(..., description="Node identifier that published this schema")


class TruthUpdatePayload(BaseTruthModel):
    """Represents a schema update message broadcast over Redis."""
    version: str = Field(..., description="Updated truth version")
    truth_schema: Dict[str, Any] = Field(..., alias="schema", description="Updated truth content")
    updated_by: str = Field(..., description="Node ID or service publishing the update")
    reason: Optional[str] = Field(None, description="Optional explanation of update reason")
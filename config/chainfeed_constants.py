"""
config/chainfeed_constants.py
-----------------------------

Canonical configuration and constant definitions for ChainFeed.

This file centralizes all constants used across the ChainFeed ecosystem —
including Redis key templates, heartbeat configuration, schema versions,
and integration metadata.

Every backend node (ChainFeed) and frontend system (SSE / React) reads
from this shared schema, either directly or via Redis integration export.
"""

import os

# ==========================================================
# Versioning
# ==========================================================
CHAINFEED_VERSION = "v1.0.0"
REDIS_KEY_VERSION = "v1.0.0"
HEARTBEAT_VERSION = "v1.0.0"

# ==========================================================
# Redis Prefixes and Base Keys
# ==========================================================
REDIS_PREFIX = "chainfeed"
CHANNEL_PREFIX = "pubsub"

# ==========================================================
# Node Identity (auto-detect or override per machine / .env)
# ==========================================================
NODE_ID = os.getenv("NODE_ID", "studiotwo_chainfeed")  # unique node name
FEED_GROUPS = ["spx_complex", "index_complex", "futures_complex"]

# ==========================================================
# Redis Key Templates
# ==========================================================
KEY_TEMPLATE_RAW = f"{REDIS_PREFIX}:{{symbol}}:raw"
KEY_TEMPLATE_FULL = f"{REDIS_PREFIX}:{{symbol}}:full"
KEY_TEMPLATE_DIFF = f"{REDIS_PREFIX}:{{symbol}}:diff"

# Feed Expiration Caches
KEY_TEMPLATE_FEED_EXPIRATIONS = f"{REDIS_PREFIX}:{{symbol}}:expirations"
KEY_META_EXPIRATIONS = f"{REDIS_PREFIX}:meta:expirations"

# Heartbeats
KEY_HEARTBEAT = "heartbeat:{group}"

# ==========================================================
# Integration Schema Metadata
# ==========================================================
REDIS_KEYS = {
    # Canonical meta/config keys
    "meta_constants": "meta:chainfeed:constants",
    "config": "config:chainfeed:{node_id}",

    # Feed storage keys
    "feed_raw": KEY_TEMPLATE_RAW,
    "feed_full": KEY_TEMPLATE_FULL,
    "feed_diff": KEY_TEMPLATE_DIFF,
    "feed_expirations": KEY_TEMPLATE_FEED_EXPIRATIONS,

    # Heartbeats
    "heartbeat": KEY_HEARTBEAT,

    # Channels
    "channel_pattern": f"{CHANNEL_PREFIX}:{{symbol}}:{{feed_type}}",
}

# ==========================================================
# Heartbeat Configuration
# ==========================================================
HEARTBEAT_INTERVAL_SEC = 5
HEARTBEAT_TTL_SEC = 15
HEARTBEAT_KEY_TEMPLATE = KEY_HEARTBEAT

# ==========================================================
# Integration + Mesh
# ==========================================================
INTEGRATION_KEY = "meta:chainfeed:integration"
INTEGRATION_CHANNEL = "integration:schema:update"

MESH_NODES_KEY = "mesh:nodes"
MESH_STATE_KEY = "mesh:state"

# ==========================================================
# Symbol / Feed Defaults
# ==========================================================
DEFAULT_SYMBOLS = ["SPX", "ES", "NDX"]
DEFAULT_FEEDS = ["full", "diff"]
DEFAULT_GROUPS = ["spx_complex", "ndx_complex", "index_complex", "futures_complex"]

# ==========================================================
# Logging Defaults
# ==========================================================
LOG_LEVEL = "INFO"

# ==========================================================
# Consolidated Metadata
# ==========================================================
CONSTANTS_METADATA = {
    "version": CHAINFEED_VERSION,
    "redis_key_version": REDIS_KEY_VERSION,
    "heartbeat_version": HEARTBEAT_VERSION,
    "heartbeat_interval_sec": HEARTBEAT_INTERVAL_SEC,
    "heartbeat_ttl_sec": HEARTBEAT_TTL_SEC,
    "default_symbols": DEFAULT_SYMBOLS,
    "default_feeds": DEFAULT_FEEDS,
    "default_groups": DEFAULT_GROUPS,
    "node_id": NODE_ID,
    "feed_groups": FEED_GROUPS,
}
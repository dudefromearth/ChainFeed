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
import socket
import yaml
from pathlib import Path

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
# Resolve node identity in the following priority order:
# 1. NODE_ID environment variable (explicit override)
# 2. variant_config.yaml (per-node config)
# 3. hostname-based fallback
# 4. final hardcoded fallback (legacy)

CONFIG_PATH = Path(__file__).parent / "variant_config.yaml"

try:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            variant_cfg = yaml.safe_load(f) or {}
        NODE_ID = os.getenv(
            "NODE_ID",
            variant_cfg.get("node_id", f"{socket.gethostname().lower()}_chainfeed")
        )
    else:
        NODE_ID = os.getenv("NODE_ID", f"{socket.gethostname().lower()}_chainfeed")
except Exception as e:
    # Absolute fallback for robustness
    NODE_ID = f"{socket.gethostname().lower()}_chainfeed"

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
# TTL Defaults (Seconds)
# ==========================================================
HEARTBEAT_TTL_SEC = 15
FEED_TTL_SEC = 15
MESH_TTL_SEC = 30

# ==========================================================
# Heartbeat Configuration
# ==========================================================
HEARTBEAT_INTERVAL_SEC = 15
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
DEFAULT_SYMBOLS = ["SPX", "ES", "NDX", "NQ"]
DEFAULT_FEEDS = ["full", "diff"]
DEFAULT_GROUPS = ["spx_complex", "ndx_complex", "index_complex", "futures_complex"]

# ==========================================================
# Symbol-to-Group Mapping (multi-group aware)
# ==========================================================
SYMBOL_GROUP_MAP = {
    # SPX Complex
    "SPX": ["spx_complex", "index_complex"],
    "ES": ["spx_complex", "futures_complex"],
    "SPY": ["spx_complex"],

    # NDX Complex
    "NDX": ["ndx_complex", "index_complex"],
    "NQ": ["ndx_complex", "futures_complex"],
    "QQQ": ["ndx_complex"],

    # Index-only
    "XSP": ["index_complex"],
}

# ==========================================================
# Group-to-Symbol Reverse Mapping
# ==========================================================
GROUP_SYMBOL_MAP = {}
for symbol, groups in SYMBOL_GROUP_MAP.items():
    for group in groups:
        GROUP_SYMBOL_MAP.setdefault(group, []).append(symbol)

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

# ==========================================================
# Redis Pipe TTL and Persistence Policy
# ==========================================================
# Defines how long each Redis key type should live (in seconds).
# -1 means "persistent" (no expiry).
# This is the canonical TTL definition used by all writers.

PIPE_TTL_POLICY = {
    # --- Meta & Integration (Persistent)
    "meta:": -1,
    "config:": -1,

    # --- Mesh & Topology (Semi-Persistent)
    "mesh:": 600,          # 10 minutes

    # --- Heartbeats (Short-Lived)
    "heartbeat:": 15,      # Matches HEARTBEAT_TTL_SEC

    # --- Feed Data (Ephemeral, updates rapidly)
    "chainfeed:": 20,      # Option chain cache or normalized feed data
    "feed:": 15,           # Real-time feed health

    # --- Expirations (Static Reference)
    "expirations:": -1,    # Only refreshed by bootstrap
}

# Helper constants
DEFAULT_TTL = 15
PERSISTENT_TTL = -1
LONG_TTL = 600
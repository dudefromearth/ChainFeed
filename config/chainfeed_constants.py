# chainfeed_constants.py

# Redis key patterns (per symbol)
KEY_PREFIX = "chainfeed"
KEY_TEMPLATE_RAW = f"{KEY_PREFIX}:{{symbol}}:raw"
KEY_TEMPLATE_FULL = f"{KEY_PREFIX}:{{symbol}}:full"
KEY_TEMPLATE_DIFF = f"{KEY_PREFIX}:{{symbol}}:diff"
KEY_TEMPLATE_EXPIRATIONS = f"{KEY_PREFIX}:expirations"
KEY_HEARTBEAT = f"{KEY_PREFIX}:heartbeat"

# Redis TTLs (in seconds)
TTL_CHAIN_SNAPSHOT = 30
TTL_EXPIRATIONS = 86400  # 1 day

# Feed types
FEED_RAW = "raw"
FEED_FULL = "full"
FEED_DIFF = "diff"

# Pub/Sub channels (optional, if used)
CHANNEL_PREFIX = "pubsub"
CHANNEL_TEMPLATE = f"{CHANNEL_PREFIX}:{{symbol}}:{{feed_type}}"

# Supported feed types
SUPPORTED_FEEDS = [FEED_RAW, FEED_FULL, FEED_DIFF]
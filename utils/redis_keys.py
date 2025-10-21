# utils/redis_keys.py
from config.chainfeed_constants import (
    REDIS_KEYS,
    KEY_PREFIX,
    KEY_TEMPLATE_RAW,
    KEY_TEMPLATE_FULL,
    KEY_TEMPLATE_DIFF,
    KEY_TEMPLATE_EXPIRATIONS,
    KEY_HEARTBEAT,
)

# Optional: keep these aliases so older code still works
HEARTBEAT = KEY_HEARTBEAT
FULL_FEED = KEY_TEMPLATE_FULL
DIFF_FEED = KEY_TEMPLATE_DIFF
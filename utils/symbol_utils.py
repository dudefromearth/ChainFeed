import redis
from utils.redis_keys import RedisKeys

# Default symbols for initial deployment
DEFAULT_SYMBOLS = ["SPX", "ES"]

def get_configured_symbols():
    """
    Placeholder for config-driven or environment-driven symbol list.
    For now, returns hardcoded list.
    """
    return DEFAULT_SYMBOLS

def inspect_symbol_status(r: redis.Redis, symbol: str):
    """
    Check presence of FULL, FULL_RAW, DIFF for the symbol.
    Determine if it's 'live' based on key TTLs or values.
    """
    full_key = RedisKeys.latest_full_key(symbol)
    diff_key = RedisKeys.latest_diff_key(symbol)

    full_exists = r.exists(full_key)
    diff_exists = r.exists(diff_key)

    full_ttl = r.ttl(full_key)
    diff_ttl = r.ttl(diff_key)

    full_live = full_ttl > 0
    diff_live = diff_ttl > 0

    return {
        "full": bool(full_exists),
        "diff": bool(diff_exists),
        "live": full_live and diff_live,
        "full_ttl": full_ttl,
        "diff_ttl": diff_ttl,
    }
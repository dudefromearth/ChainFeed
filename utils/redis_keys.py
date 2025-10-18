# core/redis_keys.py

class RedisKeys:
    HEARTBEAT = "CHAIN:HEARTBEAT"
    FULL_FEED = "CHAIN:FEED:FULL"
    DIFF_FEED = "CHAIN:FEED:DIFF"
    SIGMA = "CHAIN:SIGMA"

    POINTER_FULL_LATEST = "POINTER:FEED:FULL:LATEST"
    SYSTEM_LAST_UPDATE = "SYSTEM:LAST_UPDATE"

    @staticmethod
    def full_key(symbol: str, ts: str) -> str:
        return f"CHAIN:FEED:FULL:{symbol}:{ts}"

    @staticmethod
    def diff_key(symbol: str, ts: str) -> str:
        return f"CHAIN:FEED:DIFF:{symbol}:{ts}"
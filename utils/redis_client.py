# core/redis_client.py

import redis

_redis_instance = None

def get_redis_client(host="localhost", port=6379, db=0) -> redis.Redis:
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    return _redis_instance

from config.chainfeed_constants import PIPE_TTL_POLICY

def redis_set_with_policy(redis, key: str, value: str):
    """
    Set a Redis key using the canonical TTL policy from PIPE_TTL_POLICY.
    If the key prefix isn't found, applies a default TTL (15s).
    """
    for prefix, ttl in PIPE_TTL_POLICY.items():
        if key.startswith(prefix):
            redis.set(key, value, ex=None if ttl == -1 else ttl)
            return
    redis.set(key, value, ex=15)
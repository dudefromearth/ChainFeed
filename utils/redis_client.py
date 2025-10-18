# core/redis_client.py

import redis

_redis_instance = None

def get_redis_client(host="localhost", port=6379, db=0) -> redis.Redis:
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    return _redis_instance
"""TTL Caching Engine with In-Memory fallback and Redis support for Beauty Care Platform."""

import time
import json
import os
from typing import Any, Optional

try:
    import redis
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_timeout=1.0)
    _redis_client.ping()
    HAS_REDIS = True
except Exception:
    HAS_REDIS = False
    _redis_client = None


class TTLMemoryCache:
    """In-memory TTL Cache with optional Redis backing."""
    def __init__(self):
        self._store = {}

    def get(self, key: str) -> Optional[Any]:
        if HAS_REDIS and _redis_client:
            try:
                val = _redis_client.get(key)
                if val:
                    return json.loads(val.decode("utf-8"))
            except Exception:
                pass

        entry = self._store.get(key)
        if not entry:
            return None
        expire_at, value = entry
        if time.time() > expire_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if HAS_REDIS and _redis_client:
            try:
                _redis_client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
                return
            except Exception:
                pass

        expire_at = time.time() + ttl_seconds
        self._store[key] = (expire_at, value)

    def delete(self, key: str) -> None:
        if HAS_REDIS and _redis_client:
            try:
                _redis_client.delete(key)
            except Exception:
                pass
        self._store.pop(key, None)

    def clear(self) -> None:
        if HAS_REDIS and _redis_client:
            try:
                _redis_client.flushdb()
            except Exception:
                pass
        self._store.clear()


# Global shared cache instance
cache = TTLMemoryCache()

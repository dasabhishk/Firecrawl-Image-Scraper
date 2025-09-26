from cachetools import TTLCache
from typing import Optional, List, Any
import hashlib

_cache = TTLCache(maxsize=100, ttl=600)

def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def get_cached_result(cache_key: str) -> Optional[List[str]]:
    hashed_key = _hash_key(cache_key)
    return _cache.get(hashed_key)

def set_cached_result(cache_key: str, value: List[str]) -> None:
    hashed_key = _hash_key(cache_key)
    _cache[hashed_key] = value

def clear_cache() -> None:
    _cache.clear()
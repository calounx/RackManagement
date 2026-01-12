"""
Cache module for HomeRack API.
Provides Redis-based caching with graceful degradation.
"""

from .redis import RedisCache, get_redis_cache
from .decorators import cache_result, invalidate_cache

__all__ = [
    "RedisCache",
    "get_redis_cache",
    "cache_result",
    "invalidate_cache",
]

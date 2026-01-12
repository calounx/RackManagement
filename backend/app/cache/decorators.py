"""
Cache decorators for function result caching.
"""

import hashlib
import json
import logging
from typing import Callable, Optional, Any
from functools import wraps

from .redis import get_redis_cache

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate cache key from function arguments.

    Args:
        prefix: Cache key prefix (e.g., "thermal:rack")
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Create a stable representation of arguments
    key_parts = [prefix]

    # Add positional args
    for arg in args:
        if hasattr(arg, "id"):
            # For SQLAlchemy models, use ID
            key_parts.append(str(arg.id))
        elif hasattr(arg, "__dict__"):
            # For objects with dict, skip (too complex)
            continue
        else:
            key_parts.append(str(arg))

    # Add keyword args (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        if hasattr(v, "id"):
            key_parts.append(f"{k}:{v.id}")
        elif not hasattr(v, "__dict__"):
            key_parts.append(f"{k}:{v}")

    return ":".join(key_parts)


def cache_result(
    prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.

    Args:
        prefix: Cache key prefix (e.g., "thermal", "optimization")
        ttl: Time to live in seconds (default: from settings)
        key_func: Custom function to generate cache key (optional)

    Usage:
        @cache_result(prefix="thermal:rack", ttl=300)
        def expensive_function(rack_id: int):
            # ... expensive computation
            return result

    The decorator:
    - Checks cache before executing function
    - Returns cached result if available
    - Executes function and caches result if not cached
    - Gracefully degrades if Redis is unavailable
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_redis_cache()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.info(f"Cache HIT for {func.__name__}: {cache_key}")
                return cached_value

            # Execute function
            logger.info(f"Cache MISS for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl=ttl)

            return result

        # Add helper method to wrapper for manual cache invalidation
        def invalidate(*args, **kwargs):
            """Invalidate cache for specific arguments."""
            cache = get_redis_cache()
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, *args, **kwargs)
            cache.delete(cache_key)
            logger.info(f"Cache invalidated for {func.__name__}: {cache_key}")

        wrapper.invalidate = invalidate
        wrapper.cache_prefix = prefix

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate all cache entries matching pattern.

    Args:
        pattern: Redis key pattern (e.g., "thermal:rack:*")

    Usage:
        # Invalidate all thermal cache for a specific rack
        invalidate_cache("thermal:rack:123:*")

        # Invalidate all thermal cache
        invalidate_cache("thermal:*")
    """
    cache = get_redis_cache()
    deleted = cache.delete_pattern(pattern)
    logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
    return deleted


def invalidate_rack_thermal_cache(rack_id: int):
    """
    Invalidate all thermal analysis cache for a specific rack.

    Args:
        rack_id: Rack ID
    """
    pattern = f"thermal:rack:{rack_id}:*"
    return invalidate_cache(pattern)


def invalidate_rack_optimization_cache(rack_id: int):
    """
    Invalidate all optimization cache for a specific rack.

    Args:
        rack_id: Rack ID
    """
    pattern = f"optimization:rack:{rack_id}:*"
    return invalidate_cache(pattern)


def invalidate_search_cache():
    """
    Invalidate all device specification search cache.
    """
    pattern = "search:specs:*"
    return invalidate_cache(pattern)


def generate_thermal_cache_key(rack_id: int, rack_updated_at: Any = None) -> str:
    """
    Generate cache key for thermal analysis.

    Includes rack update timestamp to auto-invalidate on changes.

    Args:
        rack_id: Rack ID
        rack_updated_at: Rack last modified timestamp

    Returns:
        Cache key
    """
    if rack_updated_at:
        # Include timestamp hash for auto-invalidation
        timestamp_str = str(rack_updated_at)
        timestamp_hash = hashlib.md5(timestamp_str.encode()).hexdigest()[:8]
        return f"thermal:rack:{rack_id}:{timestamp_hash}"
    else:
        return f"thermal:rack:{rack_id}"


def generate_optimization_cache_key(
    rack_id: int,
    weights: dict,
    locked_positions: list = None
) -> str:
    """
    Generate cache key for optimization results.

    Includes config hash to cache different optimization configurations.

    Args:
        rack_id: Rack ID
        weights: Optimization weights
        locked_positions: Locked device positions

    Returns:
        Cache key
    """
    # Create stable config representation
    config = {
        "weights": weights,
        "locked": sorted(locked_positions) if locked_positions else []
    }
    config_str = json.dumps(config, sort_keys=True)
    config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]

    return f"optimization:rack:{rack_id}:{config_hash}"


def generate_search_cache_key(query: str, **filters) -> str:
    """
    Generate cache key for device spec search.

    Args:
        query: Search query
        **filters: Additional filters

    Returns:
        Cache key
    """
    # Create stable search representation
    search_params = {"query": query, **filters}
    params_str = json.dumps(search_params, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

    return f"search:specs:{params_hash}"

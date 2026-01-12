"""
Redis cache client with connection pooling, retry logic, and graceful degradation.
"""

import json
import logging
from typing import Optional, Any, Union
from contextlib import asynccontextmanager
import redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis cache client with connection pooling and graceful degradation.

    Features:
    - Connection pooling for efficient resource usage
    - Exponential backoff retry logic for transient failures
    - Circuit breaker pattern for sustained failures
    - Graceful degradation (cache misses on Redis failures)
    - JSON serialization for complex data types
    """

    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self._enabled = settings.CACHE_ENABLED and settings.REDIS_ENABLED
        self._redis_url = settings.get_cache_redis_url()
        self._is_available = False
        self._failure_count = 0
        self._max_failures = 5

        if self._enabled and self._redis_url:
            try:
                self._initialize_client()
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self._enabled = False

    def _initialize_client(self):
        """Initialize Redis client with connection pool."""
        try:
            # Parse Redis URL and create connection pool
            self.pool = ConnectionPool.from_url(
                self._redis_url,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_keepalive=True,
                health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
                decode_responses=True,
            )

            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            self.client.ping()
            self._is_available = True
            self._failure_count = 0

            logger.info("Redis cache initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self._is_available = False
            raise

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled and self._is_available

    def is_available(self) -> bool:
        """
        Check if Redis is available (circuit breaker pattern).

        After max_failures consecutive failures, circuit is opened
        and cache is considered unavailable until manual reset.
        """
        if not self._enabled:
            return False

        if self._failure_count >= self._max_failures:
            logger.warning(
                f"Redis circuit breaker OPEN: {self._failure_count} failures. "
                "Cache disabled until manual recovery."
            )
            return False

        return self._is_available

    def _record_failure(self):
        """Record a failure and potentially open circuit breaker."""
        self._failure_count += 1
        if self._failure_count >= self._max_failures:
            logger.error(
                f"Redis circuit breaker OPENED after {self._failure_count} failures"
            )
            self._is_available = False

    def _record_success(self):
        """Record a success and reset failure count."""
        if self._failure_count > 0:
            logger.info("Redis recovered, resetting failure count")
        self._failure_count = 0
        self._is_available = True

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.5, max=5),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _execute_with_retry(self, func, *args, **kwargs):
        """Execute Redis command with retry logic."""
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found/error
        """
        if not self.is_available():
            logger.debug(f"Cache disabled, skipping GET: {key}")
            return None

        try:
            value = self._execute_with_retry(self.client.get, key)

            if value is None:
                logger.debug(f"Cache MISS: {key}")
                return None

            # Deserialize JSON
            result = json.loads(value)
            logger.debug(f"Cache HIT: {key}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize cache value for {key}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Cache GET failed for {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.debug(f"Cache disabled, skipping SET: {key}")
            return False

        try:
            # Serialize to JSON
            serialized = json.dumps(value, default=str)

            # Set with optional TTL
            if ttl:
                self._execute_with_retry(self.client.setex, key, ttl, serialized)
            else:
                self._execute_with_retry(self.client.set, key, serialized)

            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True

        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize cache value for {key}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Cache SET failed for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.is_available():
            logger.debug(f"Cache disabled, skipping DELETE: {key}")
            return False

        try:
            result = self._execute_with_retry(self.client.delete, key)
            logger.debug(f"Cache DELETE: {key} (deleted: {result})")
            return result > 0
        except Exception as e:
            logger.warning(f"Cache DELETE failed for {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "thermal:rack:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            logger.debug(f"Cache disabled, skipping DELETE_PATTERN: {pattern}")
            return 0

        try:
            # Find matching keys
            keys = self._execute_with_retry(self.client.keys, pattern)

            if not keys:
                logger.debug(f"No keys matched pattern: {pattern}")
                return 0

            # Delete all matching keys
            deleted = self._execute_with_retry(self.client.delete, *keys)
            logger.info(f"Cache DELETE_PATTERN: {pattern} ({deleted} keys deleted)")
            return deleted

        except Exception as e:
            logger.warning(f"Cache DELETE_PATTERN failed for {pattern}: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all cache entries (DANGEROUS - use with caution).

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.debug("Cache disabled, skipping CLEAR_ALL")
            return False

        try:
            self._execute_with_retry(self.client.flushdb)
            logger.warning("Cache cleared: FLUSHDB executed")
            return True
        except Exception as e:
            logger.error(f"Cache CLEAR_ALL failed: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.is_available():
            return {
                "enabled": self._enabled,
                "available": False,
                "failure_count": self._failure_count,
            }

        try:
            info = self._execute_with_retry(self.client.info, "stats")
            memory_info = self._execute_with_retry(self.client.info, "memory")

            return {
                "enabled": self._enabled,
                "available": True,
                "failure_count": self._failure_count,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "used_memory": memory_info.get("used_memory_human", "unknown"),
                "used_memory_bytes": memory_info.get("used_memory", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                "enabled": self._enabled,
                "available": False,
                "error": str(e)
            }

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    def health_check(self) -> bool:
        """
        Perform health check on Redis connection.

        Returns:
            True if healthy, False otherwise
        """
        if not self._enabled:
            return False

        try:
            response = self._execute_with_retry(self.client.ping)
            return response is True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    def close(self):
        """Close Redis connection and cleanup resources."""
        if self.pool:
            try:
                self.pool.disconnect()
                logger.info("Redis connection pool closed")
            except Exception as e:
                logger.error(f"Error closing Redis pool: {e}")


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """
    Get or create global Redis cache instance (singleton pattern).

    Returns:
        RedisCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = RedisCache()

    return _cache_instance


def close_redis_cache():
    """Close global Redis cache instance."""
    global _cache_instance

    if _cache_instance:
        _cache_instance.close()
        _cache_instance = None

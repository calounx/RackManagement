#!/usr/bin/env python3
"""
Test script for Redis cache implementation.
Verifies cache functionality, invalidation, and graceful degradation.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cache import get_redis_cache


def test_cache_basic_operations():
    """Test basic cache operations (set, get, delete)."""
    print("\n=== Testing Basic Cache Operations ===")
    cache = get_redis_cache()

    # Test availability
    print(f"Cache enabled: {cache.is_enabled()}")
    print(f"Cache available: {cache.is_available()}")

    if not cache.is_available():
        print("WARNING: Cache not available, skipping tests")
        return

    # Test SET
    key = "test:basic:key"
    value = {"message": "Hello, Cache!", "number": 42}
    print(f"\nSetting key '{key}' with value: {value}")
    success = cache.set(key, value, ttl=60)
    print(f"Set result: {success}")

    # Test GET
    print(f"\nGetting key '{key}'")
    retrieved = cache.get(key)
    print(f"Retrieved: {retrieved}")
    assert retrieved == value, "Retrieved value doesn't match!"

    # Test DELETE
    print(f"\nDeleting key '{key}'")
    deleted = cache.delete(key)
    print(f"Delete result: {deleted}")

    # Verify deletion
    retrieved_after = cache.get(key)
    print(f"Value after delete: {retrieved_after}")
    assert retrieved_after is None, "Key should be None after deletion!"

    print("\nBasic operations test: PASSED")


def test_cache_ttl():
    """Test cache TTL (time-to-live)."""
    print("\n=== Testing Cache TTL ===")
    cache = get_redis_cache()

    if not cache.is_available():
        print("WARNING: Cache not available, skipping test")
        return

    key = "test:ttl:key"
    value = {"expires": "soon"}

    print(f"Setting key '{key}' with 2 second TTL")
    cache.set(key, value, ttl=2)

    print("Retrieving immediately...")
    retrieved = cache.get(key)
    print(f"Retrieved: {retrieved}")
    assert retrieved == value, "Should retrieve value immediately!"

    print("Waiting 3 seconds for TTL to expire...")
    time.sleep(3)

    print("Retrieving after TTL expiration...")
    retrieved_after = cache.get(key)
    print(f"Retrieved after expiration: {retrieved_after}")
    assert retrieved_after is None, "Key should be None after TTL expiration!"

    print("\nTTL test: PASSED")


def test_cache_pattern_deletion():
    """Test pattern-based cache deletion."""
    print("\n=== Testing Pattern Deletion ===")
    cache = get_redis_cache()

    if not cache.is_available():
        print("WARNING: Cache not available, skipping test")
        return

    # Set multiple keys with same pattern
    pattern = "test:pattern"
    keys = [
        f"{pattern}:key1",
        f"{pattern}:key2",
        f"{pattern}:key3",
        "test:other:key"
    ]

    print(f"\nSetting {len(keys)} test keys")
    for key in keys:
        cache.set(key, {"key": key}, ttl=300)
        print(f"  Set: {key}")

    # Delete by pattern
    delete_pattern = f"{pattern}:*"
    print(f"\nDeleting keys matching pattern: {delete_pattern}")
    deleted_count = cache.delete_pattern(delete_pattern)
    print(f"Deleted {deleted_count} keys")

    # Verify deletion
    print("\nVerifying deletion:")
    for key in keys:
        value = cache.get(key)
        if pattern in key and key.startswith(f"{pattern}:"):
            assert value is None, f"{key} should be deleted!"
            print(f"  {key}: None (correctly deleted)")
        else:
            print(f"  {key}: {value} (preserved)")

    # Cleanup
    cache.delete("test:other:key")

    print("\nPattern deletion test: PASSED")


def test_cache_stats():
    """Test cache statistics retrieval."""
    print("\n=== Testing Cache Statistics ===")
    cache = get_redis_cache()

    if not cache.is_available():
        print("WARNING: Cache not available, skipping test")
        return

    stats = cache.get_stats()
    print("\nCache Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    assert "enabled" in stats, "Stats should include 'enabled'"
    assert "available" in stats, "Stats should include 'available'"

    print("\nStats test: PASSED")


def test_cache_health_check():
    """Test cache health check."""
    print("\n=== Testing Health Check ===")
    cache = get_redis_cache()

    if not cache.is_available():
        print("WARNING: Cache not available, skipping test")
        return

    is_healthy = cache.health_check()
    print(f"Health check result: {is_healthy}")

    assert is_healthy, "Cache should be healthy!"

    print("\nHealth check test: PASSED")


def test_cache_graceful_degradation():
    """Test graceful degradation when cache is disabled."""
    print("\n=== Testing Graceful Degradation ===")

    # This test simulates cache being unavailable
    # The application should continue working without crashing

    cache = get_redis_cache()

    # Test operations when cache might not be available
    key = "test:degradation:key"
    value = {"test": "data"}

    print(f"\nAttempting cache operations (may gracefully fail):")
    print(f"  Set: {cache.set(key, value, ttl=60)}")
    print(f"  Get: {cache.get(key)}")
    print(f"  Delete: {cache.delete(key)}")

    print("\nGraceful degradation test: PASSED")


def main():
    """Run all cache tests."""
    print("=" * 60)
    print("Redis Cache Implementation Test Suite")
    print("=" * 60)

    try:
        test_cache_basic_operations()
        test_cache_ttl()
        test_cache_pattern_deletion()
        test_cache_stats()
        test_cache_health_check()
        test_cache_graceful_degradation()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

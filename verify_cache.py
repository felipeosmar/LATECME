#!/usr/bin/env python3
"""
Verification script to test Redis connectivity and cache operations.
Tests:
1. Redis connection
2. cache.set() and cache.get()
3. Cache key generation with prefix
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.cache import cache
from django.conf import settings


def test_redis_connection():
    """Test if Redis connection is working."""
    try:
        # Test basic connection
        cache.set('test_connection', 'ok', timeout=10)
        result = cache.get('test_connection')
        if result != 'ok':
            raise ValueError(f"Expected 'ok', got '{result}'")
        cache.delete('test_connection')
        return True
    except Exception as e:
        raise RuntimeError(f"Redis connection failed: {str(e)}")


def test_cache_operations():
    """Test cache set and get operations."""
    try:
        test_data = {
            'string': 'test_value',
            'number': 12345,
            'list': [1, 2, 3],
            'dict': {'key': 'value'}
        }

        for key, value in test_data.items():
            cache_key = f'test_{key}'
            cache.set(cache_key, value, timeout=10)
            result = cache.get(cache_key)
            if result != value:
                raise ValueError(f"Cache operation failed for {key}: expected {value}, got {result}")
            cache.delete(cache_key)

        return True
    except Exception as e:
        raise RuntimeError(f"Cache operations failed: {str(e)}")


def test_cache_key_generation():
    """Test cache key generation with prefix."""
    try:
        # Verify cache configuration
        cache_config = settings.CACHES.get('default', {})
        backend = cache_config.get('BACKEND')
        key_prefix = cache_config.get('KEY_PREFIX', '')

        if backend != 'django_redis.cache.RedisCache':
            raise ValueError(f"Expected django_redis.cache.RedisCache backend, got {backend}")

        if not key_prefix:
            raise ValueError("Cache KEY_PREFIX not configured")

        # Test key with prefix
        test_key = 'dashboard_test'
        test_value = 'cached_data'
        cache.set(test_key, test_value, timeout=10)
        result = cache.get(test_key)

        if result != test_value:
            raise ValueError(f"Key generation test failed: expected {test_value}, got {result}")

        cache.delete(test_key)
        return True
    except Exception as e:
        raise RuntimeError(f"Cache key generation test failed: {str(e)}")


def main():
    """Run all cache verification tests."""
    try:
        test_redis_connection()
        test_cache_operations()
        test_cache_key_generation()
        print("Cache test: PASSED")
        return 0
    except Exception as e:
        print(f"Cache test: FAILED - {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

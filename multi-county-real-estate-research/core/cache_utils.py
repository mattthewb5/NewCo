"""
Simple in-memory caching for API responses.

Caches API responses to improve performance and reduce redundant calls.
Uses TTL (time-to-live) to ensure data freshness while maintaining performance.

Benefits:
- Faster repeat queries (no API roundtrip)
- Reduced load on external APIs
- Better user experience in UI

Note: This is in-memory caching - resets on restart. For production with
multiple workers, consider Redis or similar distributed cache.

Last Updated: November 2025
Phase: 4 - Performance Enhancement
Status: Production-ready
"""

from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Tuple
import hashlib
import json

# Simple in-memory cache storage
# Structure: {cache_key: (cached_data, timestamp)}
_cache: Dict[str, Tuple[Any, datetime]] = {}

# Cache statistics
_cache_stats = {
    "hits": 0,      # Number of cache hits
    "misses": 0,    # Number of cache misses
    "evictions": 0  # Number of expired entries removed
}


def get_cache_key(*args, **kwargs) -> str:
    """
    Generate a unique cache key from function arguments.

    Args:
        *args: Positional arguments to hash
        **kwargs: Keyword arguments to hash

    Returns:
        MD5 hash of serialized arguments

    Example:
        >>> get_cache_key("Ashburn, VA", lat=39.0, lon=-77.5)
        'a1b2c3d4e5f6...'
    """
    try:
        # Serialize arguments to JSON (sorted for consistency)
        key_data = json.dumps(
            {"args": args, "kwargs": kwargs},
            sort_keys=True,
            default=str  # Handle non-JSON types
        )
        # Return MD5 hash
        return hashlib.md5(key_data.encode()).hexdigest()
    except (TypeError, ValueError):
        # Fallback: use string representation
        return hashlib.md5(str((args, kwargs)).encode()).hexdigest()


def cached(ttl_minutes: int = 60):
    """
    Decorator to cache function results with time-to-live.

    Caches the return value of a function based on its arguments.
    Cached values expire after ttl_minutes.

    Args:
        ttl_minutes: Time-to-live in minutes (default: 60)

    Returns:
        Decorated function with caching behavior

    Usage:
        @cached(ttl_minutes=30)
        def expensive_api_call(address: str) -> dict:
            # ... expensive operation
            return result

        # First call - cache miss, calls function
        result1 = expensive_api_call("123 Main St")

        # Second call within 30 min - cache hit, returns cached value
        result2 = expensive_api_call("123 Main St")  # Fast!
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate unique cache key for this function call
            cache_key = f"{func.__module__}.{func.__name__}:{get_cache_key(*args, **kwargs)}"

            # Check if we have a cached result
            if cache_key in _cache:
                cached_data, cached_time = _cache[cache_key]

                # Check if cache entry is still valid
                age = datetime.now() - cached_time
                if age < timedelta(minutes=ttl_minutes):
                    # Cache hit!
                    _cache_stats["hits"] += 1
                    return cached_data
                else:
                    # Expired - remove it
                    del _cache[cache_key]
                    _cache_stats["evictions"] += 1

            # Cache miss - call the actual function
            _cache_stats["misses"] += 1
            result = func(*args, **kwargs)

            # Store result in cache with timestamp
            _cache[cache_key] = (result, datetime.now())

            return result

        return wrapper
    return decorator


def clear_cache():
    """
    Clear all cached data.

    Useful for testing or when you need fresh data.

    Example:
        >>> from core.cache_utils import clear_cache
        >>> clear_cache()  # All cached data removed
    """
    global _cache
    _cache = {}
    print("Cache cleared")


def get_cache_stats() -> dict:
    """
    Get cache performance statistics.

    Returns:
        Dictionary with hits, misses, evictions, and hit rate

    Example:
        >>> from core.cache_utils import get_cache_stats
        >>> stats = get_cache_stats()
        >>> print(f"Hit rate: {stats['hit_rate']:.1f}%")
    """
    stats = _cache_stats.copy()

    # Calculate hit rate
    total = stats["hits"] + stats["misses"]
    if total > 0:
        stats["hit_rate"] = (stats["hits"] / total) * 100
    else:
        stats["hit_rate"] = 0.0

    # Add cache size
    stats["cache_size"] = len(_cache)

    return stats


def get_cache_info() -> dict:
    """
    Get detailed cache information for debugging.

    Returns:
        Dictionary with cache statistics and contents summary

    Example:
        >>> from core.cache_utils import get_cache_info
        >>> info = get_cache_info()
        >>> print(f"Cached entries: {info['entries']}")
    """
    stats = get_cache_stats()

    # Add cache entry details
    entries = []
    for key, (data, timestamp) in _cache.items():
        age_seconds = (datetime.now() - timestamp).total_seconds()
        entries.append({
            "key": key[:50] + "..." if len(key) > 50 else key,  # Truncate long keys
            "age_seconds": age_seconds,
            "age_minutes": age_seconds / 60
        })

    return {
        **stats,
        "entries": len(entries),
        "cached_items": entries[:10]  # Show first 10 for brevity
    }


# Convenience function for logging cache stats
def print_cache_stats():
    """Print cache statistics in a readable format."""
    stats = get_cache_stats()

    print("\n" + "=" * 50)
    print("CACHE STATISTICS")
    print("=" * 50)
    print(f"Hits:       {stats['hits']:,}")
    print(f"Misses:     {stats['misses']:,}")
    print(f"Evictions:  {stats['evictions']:,}")
    print(f"Hit Rate:   {stats['hit_rate']:.1f}%")
    print(f"Cache Size: {stats['cache_size']} entries")
    print("=" * 50 + "\n")

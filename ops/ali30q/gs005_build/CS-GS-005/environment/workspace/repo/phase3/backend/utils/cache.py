"""
Simple in-memory cache for API responses.
Uses TTL-based expiration for cache entries.
"""
import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Import metrics if available
try:
    from utils.metrics import record_cache_hit, record_cache_miss
    _metrics_available = True
except ImportError:
    _metrics_available = False
    logger.warning("Metrics not available, cache metrics will not be recorded")


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        # Try Redis first if available
        if _use_redis and _redis_client:
            try:
                value = _redis_client.get(key)
                if value is not None:
                    self._hits += 1
                    if _metrics_available:
                        record_cache_hit(key)
                    return json.loads(value)
                else:
                    self._misses += 1
                    if _metrics_available:
                        record_cache_miss(key)
                    return None
            except Exception as e:
                logger.error(f"Redis get error, falling back to memory: {e}")

        # Fallback to memory cache
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._hits += 1
                if _metrics_available:
                    record_cache_hit(key)
                return value
            else:
                # Expired, remove it
                del self._cache[key]

        self._misses += 1
        if _metrics_available:
            record_cache_miss(key)
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds."""
        # Try Redis first if available
        if _use_redis and _redis_client:
            try:
                serialized = json.dumps(value, default=str)
                _redis_client.setex(key, ttl, serialized)
                return
            except Exception as e:
                logger.error(f"Redis set error, falling back to memory: {e}")

        # Fallback to memory cache
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)

    def delete(self, key: str):
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "size": len(self._cache)
        }

    def cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time >= expiry
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance - use Redis if available, fallback to memory
try:
    import redis
    from redis.sentinel import Sentinel
    from redis.cluster import RedisCluster
    import os
    from dotenv import load_dotenv
    load_dotenv()

    # Check configuration priority: Cluster > Sentinel > Direct
    cluster_nodes = os.getenv('REDIS_CLUSTER_NODES', '')
    sentinel_hosts = os.getenv('REDIS_SENTINEL_HOSTS', '')

    if cluster_nodes:
        # Redis Cluster configuration
        startup_nodes = [
            {"host": node.split(':')[0], "port": int(node.split(':')[1])}
            for node in cluster_nodes.split(',')
        ]

        _redis_client = RedisCluster(
            startup_nodes=startup_nodes,
            decode_responses=True,
            password=os.getenv('REDIS_PASSWORD'),
            socket_timeout=2
        )
        _redis_client.ping()
        _use_redis = True
        logger.info("Using Redis Cluster")

    elif sentinel_hosts:
        # Redis Sentinel configuration
        sentinel_list = [
            (host.split(':')[0], int(host.split(':')[1]))
            for host in sentinel_hosts.split(',')
        ]

        sentinel = Sentinel(
            sentinel_list,
            socket_timeout=2,
            password=os.getenv('REDIS_PASSWORD')
        )

        # Get master connection
        master_name = os.getenv('REDIS_SENTINEL_MASTER', 'mymaster')
        _redis_client = sentinel.master_for(
            master_name,
            socket_timeout=2,
            decode_responses=True
        )

        _redis_client.ping()
        _use_redis = True
        logger.info(f"Using Redis Sentinel (master: {master_name})")

    else:
        # Direct Redis connection (fallback)
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        _redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
        _redis_client.ping()
        _use_redis = True
        logger.info("Using Redis direct connection")

except Exception as e:
    _redis_client = None
    _use_redis = False
    logger.warning(f"Redis unavailable, using in-memory cache: {e}")

_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance."""
    return _cache


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = {
        "args": args,
        "kwargs": kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 300)
        key_prefix: Prefix for cache key (default: "")

    Usage:
        @cached(ttl=60, key_prefix="agent_list")
        def list_agents(skip: int, limit: int):
            return db.query(Agent).offset(skip).limit(limit).all()
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = _cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss: {key}")
            result = await func(*args, **kwargs)
            _cache.set(key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = _cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss: {key}")
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl)

            return result

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def invalidate_cache(key_prefix: str = None):
    """
    Invalidate cache entries.

    Args:
        key_prefix: If provided, only invalidate keys with this prefix.
                   If None, clear entire cache.
    """
    if key_prefix is None:
        _cache.clear()
        logger.info("Cleared entire cache")
    else:
        # Remove keys with matching prefix
        if _use_redis and _redis_client:
            try:
                # Use SCAN to avoid blocking
                cursor = 0
                deleted_count = 0

                while True:
                    cursor, keys = _redis_client.scan(
                        cursor=cursor,
                        match=f"{key_prefix}*",
                        count=100
                    )

                    if keys:
                        _redis_client.delete(*keys)
                        deleted_count += len(keys)

                    if cursor == 0:
                        break

                logger.info(f"Invalidated {deleted_count} Redis cache entries with prefix '{key_prefix}'")
            except Exception as e:
                logger.error(f"Failed to invalidate Redis cache: {e}")
        else:
            # Fallback to memory cache
            keys_to_delete = [
                key for key in _cache._cache.keys()
                if key.startswith(key_prefix)
            ]
            for key in keys_to_delete:
                _cache.delete(key)
            logger.info(f"Invalidated {len(keys_to_delete)} memory cache entries with prefix '{key_prefix}'")

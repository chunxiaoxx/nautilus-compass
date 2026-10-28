"""
Redis client utility for caching and session management.
"""
import redis
import os
from typing import Optional

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client


async def get_redis_client():
    """Async-compatible Redis client (returns sync client wrapped for compatibility)."""
    try:
        redis_client.ping()
        return redis_client
    except Exception:
        return None


def test_redis_connection() -> bool:
    """Test Redis connection."""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

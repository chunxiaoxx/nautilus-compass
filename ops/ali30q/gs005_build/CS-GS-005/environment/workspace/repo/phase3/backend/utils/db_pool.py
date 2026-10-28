"""
Database utility functions with memory system integration.
"""
import asyncpg
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """Initialize the database connection pool."""
    global _db_pool

    if _db_pool is not None:
        return _db_pool

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    try:
        _db_pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connection pool initialized")
        return _db_pool
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def get_db_pool() -> asyncpg.Pool:
    """Get the database connection pool."""
    global _db_pool

    if _db_pool is None:
        _db_pool = await init_db_pool()

    return _db_pool


async def close_db_pool():
    """Close the database connection pool."""
    global _db_pool

    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None
        logger.info("Database connection pool closed")

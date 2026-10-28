"""
Database migration script to add performance indexes.
Run this script to add indexes for optimized queries.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import engine
from logging_config import get_logger

logger = get_logger(__name__)


def add_performance_indexes():
    """Add performance indexes to database tables."""

    # Predefined safe index definitions (no user input)
    indexes = [
        # Task table indexes
        ("idx_task_created_at", "CREATE INDEX IF NOT EXISTS idx_task_created_at ON tasks(created_at DESC)"),
        ("idx_task_accepted_at", "CREATE INDEX IF NOT EXISTS idx_task_accepted_at ON tasks(accepted_at)"),
        ("idx_task_completed_at", "CREATE INDEX IF NOT EXISTS idx_task_completed_at ON tasks(completed_at)"),
        ("idx_task_status_created", "CREATE INDEX IF NOT EXISTS idx_task_status_created ON tasks(status, created_at DESC)"),
        ("idx_task_agent_status", "CREATE INDEX IF NOT EXISTS idx_task_agent_status ON tasks(agent, status)"),
        ("idx_task_publisher_status", "CREATE INDEX IF NOT EXISTS idx_task_publisher_status ON tasks(publisher, status)"),

        # Reward table indexes
        ("idx_reward_distributed_at", "CREATE INDEX IF NOT EXISTS idx_reward_distributed_at ON rewards(distributed_at DESC)"),
        ("idx_reward_agent_status", "CREATE INDEX IF NOT EXISTS idx_reward_agent_status ON rewards(agent, status)"),

        # APIKey table indexes
        ("idx_apikey_is_active", "CREATE INDEX IF NOT EXISTS idx_apikey_is_active ON api_keys(is_active)"),
        ("idx_apikey_key_active", "CREATE INDEX IF NOT EXISTS idx_apikey_key_active ON api_keys(key, is_active)"),
    ]

    with engine.connect() as conn:
        for index_name, sql in indexes:
            try:
                logger.info(f"Creating index: {index_name}")
                # Using text() with predefined SQL (no user input, safe from SQL injection)
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✓ Index created: {index_name}")
            except Exception as e:
                logger.error(f"✗ Failed to create index {index_name}: {e}")
                conn.rollback()

    logger.info("Performance indexes migration completed")


def verify_indexes():
    """Verify that indexes were created successfully."""

    # SQLite query to check indexes
    check_query = """
    SELECT name, tbl_name
    FROM sqlite_master
    WHERE type = 'index'
    AND name LIKE 'idx_%'
    ORDER BY tbl_name, name
    """

    # PostgreSQL query (if using PostgreSQL)
    check_query_pg = """
    SELECT indexname, tablename
    FROM pg_indexes
    WHERE indexname LIKE 'idx_%'
    ORDER BY tablename, indexname
    """

    with engine.connect() as conn:
        try:
            # Try SQLite first
            result = conn.execute(text(check_query))
            indexes = result.fetchall()

            logger.info("\nExisting performance indexes:")
            logger.info("-" * 60)

            current_table = None
            for index_name, table_name in indexes:
                if table_name != current_table:
                    logger.info(f"\n{table_name}:")
                    current_table = table_name
                logger.info(f"  ✓ {index_name}")

            logger.info("-" * 60)
            logger.info(f"Total indexes: {len(indexes)}")

        except Exception as e:
            logger.error(f"Failed to verify indexes: {e}")


def analyze_tables():
    """Analyze tables to update statistics for query optimizer."""

    tables = ['tasks', 'agents', 'rewards', 'api_keys', 'users', 'verification_logs']

    with engine.connect() as conn:
        for table in tables:
            try:
                logger.info(f"Analyzing table: {table}")
                conn.execute(text(f"ANALYZE {table}"))
                conn.commit()
                logger.info(f"✓ Table analyzed: {table}")
            except Exception as e:
                logger.warning(f"Could not analyze table {table}: {e}")
                conn.rollback()


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("DATABASE PERFORMANCE OPTIMIZATION")
    logger.info("="*60)

    logger.info("\nStep 1: Adding performance indexes...")
    add_performance_indexes()

    logger.info("\nStep 2: Verifying indexes...")
    verify_indexes()

    logger.info("\nStep 3: Analyzing tables...")
    analyze_tables()

    logger.info("\n" + "="*60)
    logger.info("OPTIMIZATION COMPLETED")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("1. Run performance tests: pytest tests/test_performance.py -v")
    logger.info("2. Monitor slow query logs in production")
    logger.info("3. Check cache statistics at /cache/stats")
    logger.info("="*60)

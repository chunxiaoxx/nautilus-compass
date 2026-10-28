"""
Database migration: Create agents_v2 table for address-based identity.

This migration creates the new agents_v2 table that uses Ethereum addresses
as primary keys, eliminating the need for separate user accounts and API keys.
"""
from sqlalchemy import create_engine, text
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_up():
    """Create agents_v2 table."""
    # Try to load .env file
    from dotenv import load_dotenv
    load_dotenv()

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_engine(DATABASE_URL)

    # SQL to create agents_v2 table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS agents_v2 (
        address VARCHAR(42) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        specialties VARCHAR(500),
        reputation INTEGER NOT NULL DEFAULT 100,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        current_tasks INTEGER NOT NULL DEFAULT 0,
        completed_tasks INTEGER NOT NULL DEFAULT 0,
        failed_tasks INTEGER NOT NULL DEFAULT 0,
        total_earnings BIGINT NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_active_at TIMESTAMP,
        blockchain_registered BOOLEAN DEFAULT FALSE,
        blockchain_tx_hash VARCHAR(66)
    );
    """

    # Create indexes
    create_indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_agents_v2_reputation ON agents_v2(reputation DESC);
    CREATE INDEX IF NOT EXISTS idx_agents_v2_is_active ON agents_v2(is_active);
    CREATE INDEX IF NOT EXISTS idx_agents_v2_created_at ON agents_v2(created_at DESC);
    """

    try:
        with engine.connect() as conn:
            # Create table
            logger.info("Creating agents_v2 table...")
            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info("✅ agents_v2 table created")

            # Create indexes
            logger.info("Creating indexes...")
            conn.execute(text(create_indexes_sql))
            conn.commit()
            logger.info("✅ Indexes created")

        logger.info("✅ Migration completed successfully")
        logger.info("")
        logger.info("⚠️  Note: Old agents from 'agents' table cannot be automatically migrated")
        logger.info("   because they don't have private keys. Agents need to re-register using")
        logger.info("   the new signature-based registration endpoint.")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


def migrate_down():
    """Drop agents_v2 table (rollback)."""
    # Try to load .env file
    from dotenv import load_dotenv
    load_dotenv()

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_engine(DATABASE_URL)

    drop_table_sql = "DROP TABLE IF EXISTS agents_v2;"

    try:
        with engine.connect() as conn:
            logger.info("Dropping agents_v2 table...")
            conn.execute(text(drop_table_sql))
            conn.commit()
            logger.info("✅ agents_v2 table dropped")

    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        logger.info("Running migration rollback...")
        migrate_down()
    else:
        logger.info("Running migration...")
        migrate_up()

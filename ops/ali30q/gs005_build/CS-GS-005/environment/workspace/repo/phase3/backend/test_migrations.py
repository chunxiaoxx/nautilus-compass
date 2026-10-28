#!/usr/bin/env python3
"""
Database Migration Tests

Tests for database migration functionality including:
- Migration application
- Migration rollback
- Data integrity
- Schema validation
"""

import os
import sys
import pytest
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

# Load environment
load_dotenv()


@pytest.fixture(scope="module")
def test_db_url():
    """Get test database URL."""
    # Use test database
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nautilus_test")
    return db_url


@pytest.fixture(scope="module")
def engine(test_db_url):
    """Create database engine."""
    engine = create_engine(test_db_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def alembic_config():
    """Get Alembic configuration."""
    base_dir = Path(__file__).resolve().parent
    alembic_ini = base_dir / "alembic.ini"

    config = Config(str(alembic_ini))

    # Use test database
    test_db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nautilus_test")
    config.set_main_option("sqlalchemy.url", test_db_url)

    return config


class TestMigrations:
    """Test migration functionality."""

    def test_database_connection(self, engine):
        """Test database connection."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1

    def test_upgrade_to_head(self, alembic_config, engine):
        """Test upgrading to head revision."""
        # First, downgrade to base
        try:
            command.downgrade(alembic_config, "base")
        except Exception:
            pass  # May fail if no migrations applied yet

        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Verify tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = ['tasks', 'agents', 'rewards', 'verification_logs', 'users', 'api_keys', 'alembic_version']
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

    def test_tasks_table_schema(self, engine):
        """Test tasks table schema."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('tasks')}

        # Check required columns exist
        required_columns = [
            'id', 'task_id', 'publisher', 'description', 'reward',
            'task_type', 'status', 'timeout', 'created_at',
            'gas_used', 'gas_cost', 'gas_split'
        ]

        for col in required_columns:
            assert col in columns, f"Column {col} not found in tasks table"

        # Check indexes
        indexes = inspector.get_indexes('tasks')
        index_names = [idx['name'] for idx in indexes]

        assert 'ix_tasks_task_id' in index_names
        assert 'ix_tasks_status' in index_names
        assert 'ix_tasks_agent' in index_names

    def test_agents_table_schema(self, engine):
        """Test agents table schema."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('agents')}

        # Check required columns exist
        required_columns = [
            'id', 'agent_id', 'owner', 'name', 'reputation',
            'created_at', 'blockchain_registered'
        ]

        for col in required_columns:
            assert col in columns, f"Column {col} not found in agents table"

        # Check indexes
        indexes = inspector.get_indexes('agents')
        index_names = [idx['name'] for idx in indexes]

        assert 'ix_agents_agent_id' in index_names
        assert 'ix_agents_owner' in index_names

    def test_rewards_table_schema(self, engine):
        """Test rewards table schema."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('rewards')}

        # Check required columns exist
        required_columns = ['id', 'task_id', 'agent', 'amount', 'status']

        for col in required_columns:
            assert col in columns, f"Column {col} not found in rewards table"

        # Check composite index
        indexes = inspector.get_indexes('rewards')
        index_names = [idx['name'] for idx in indexes]

        assert 'ix_rewards_agent_status' in index_names

    def test_users_table_schema(self, engine):
        """Test users table schema."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('users')}

        # Check required columns exist
        required_columns = [
            'id', 'username', 'email', 'hashed_password',
            'wallet_address', 'is_active', 'created_at'
        ]

        for col in required_columns:
            assert col in columns, f"Column {col} not found in users table"

    def test_api_keys_table_schema(self, engine):
        """Test api_keys table schema."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('api_keys')}

        # Check required columns exist
        required_columns = ['id', 'key', 'agent_id', 'name', 'is_active', 'created_at']

        for col in required_columns:
            assert col in columns, f"Column {col} not found in api_keys table"

        # Check foreign key
        foreign_keys = inspector.get_foreign_keys('api_keys')
        assert len(foreign_keys) > 0, "No foreign keys found"
        assert foreign_keys[0]['referred_table'] == 'agents'

    def test_verification_logs_table_schema(self, engine):
        """Test verification_logs table schema."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('verification_logs')}

        # Check required columns exist
        required_columns = ['id', 'task_id', 'verification_method', 'is_valid', 'created_at']

        for col in required_columns:
            assert col in columns, f"Column {col} not found in verification_logs table"

        # Check foreign key
        foreign_keys = inspector.get_foreign_keys('verification_logs')
        assert len(foreign_keys) > 0, "No foreign keys found"
        assert foreign_keys[0]['referred_table'] == 'tasks'

    def test_data_integrity_after_migration(self, engine):
        """Test data integrity after migration."""
        from models.database import Base, Task, Agent, TaskType, TaskStatus

        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Create test agent
            from models.database import Agent
            agent = Agent(
                agent_id=999,
                owner="0x1234567890123456789012345678901234567890",
                name="Test Agent",
                reputation=100,
                created_at=datetime.now(timezone.utc)
            )
            session.add(agent)
            session.commit()

            # Create test task
            task = Task(
                task_id="0x" + "1" * 64,
                publisher="0x1234567890123456789012345678901234567890",
                description="Test task",
                reward=1000000000000000000,
                task_type=TaskType.CODE,
                status=TaskStatus.OPEN,
                timeout=3600,
                created_at=datetime.now(timezone.utc)
            )
            session.add(task)
            session.commit()

            # Verify data
            retrieved_task = session.query(Task).filter_by(task_id=task.task_id).first()
            assert retrieved_task is not None
            assert retrieved_task.description == "Test task"
            assert retrieved_task.reward == 1000000000000000000

            retrieved_agent = session.query(Agent).filter_by(agent_id=999).first()
            assert retrieved_agent is not None
            assert retrieved_agent.name == "Test Agent"

            # Cleanup
            session.delete(retrieved_task)
            session.delete(retrieved_agent)
            session.commit()

        finally:
            session.close()

    def test_downgrade_one_step(self, alembic_config, engine):
        """Test downgrading one migration step."""
        # Get current revision
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext

        script = ScriptDirectory.from_config(alembic_config)

        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

        if current_rev:
            # Downgrade one step
            command.downgrade(alembic_config, "-1")

            # Verify downgrade
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                new_rev = context.get_current_revision()

            assert new_rev != current_rev, "Downgrade did not change revision"

            # Upgrade back
            command.upgrade(alembic_config, "head")

    def test_migration_idempotency(self, alembic_config):
        """Test that running migrations multiple times is safe."""
        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Upgrade again (should be no-op)
        command.upgrade(alembic_config, "head")

        # Should not raise any errors

    def test_rollback_and_reapply(self, alembic_config, engine):
        """Test rolling back and reapplying migrations."""
        # Downgrade to base
        command.downgrade(alembic_config, "base")

        # Verify tables are gone
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Only alembic_version should remain
        assert 'tasks' not in tables
        assert 'agents' not in tables

        # Upgrade back to head
        command.upgrade(alembic_config, "head")

        # Verify tables are back
        tables = inspector.get_table_names()
        assert 'tasks' in tables
        assert 'agents' in tables


class TestMigrationHistory:
    """Test migration history and versioning."""

    def test_current_revision(self, alembic_config, engine):
        """Test getting current revision."""
        from alembic.runtime.migration import MigrationContext

        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

        assert current_rev is not None, "No current revision found"

    def test_migration_history(self, alembic_config):
        """Test getting migration history."""
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(alembic_config)
        revisions = list(script.walk_revisions())

        assert len(revisions) > 0, "No migrations found"

    def test_head_revision(self, alembic_config):
        """Test getting head revision."""
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(alembic_config)
        head_rev = script.get_current_head()

        assert head_rev is not None, "No head revision found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
Database Migration Management Script

This script provides a command-line interface for managing database migrations
using Alembic. It supports creating, applying, and rolling back migrations.

Usage:
    python manage_migrations.py [command] [options]

Commands:
    init            Initialize Alembic (already done)
    create          Create a new migration
    upgrade         Apply migrations
    downgrade       Rollback migrations
    current         Show current revision
    history         Show migration history
    stamp           Stamp database with a revision
    check           Check if database is up to date
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def get_alembic_config():
    """Get Alembic configuration."""
    # Load environment variables
    load_dotenv()

    # Get the directory containing this script
    base_dir = Path(__file__).resolve().parent
    alembic_ini = base_dir / "alembic.ini"

    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)

    # Create Alembic config
    config = Config(str(alembic_ini))

    # Override database URL from environment if available
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)

    return config


def create_migration(message: str, autogenerate: bool = True):
    """Create a new migration.

    Args:
        message: Migration message/description
        autogenerate: Whether to auto-generate migration from models
    """
    config = get_alembic_config()

    print(f"Creating new migration: {message}")

    if autogenerate:
        print("Auto-generating migration from model changes...")
        command.revision(config, message=message, autogenerate=True)
    else:
        print("Creating empty migration template...")
        command.revision(config, message=message, autogenerate=False)

    print("✓ Migration created successfully")


def upgrade_database(revision: str = "head"):
    """Apply migrations to upgrade database.

    Args:
        revision: Target revision (default: "head" for latest)
    """
    config = get_alembic_config()

    print(f"Upgrading database to revision: {revision}")

    try:
        command.upgrade(config, revision)
        print("✓ Database upgraded successfully")
    except Exception as e:
        print(f"✗ Error upgrading database: {e}")
        sys.exit(1)


def downgrade_database(revision: str = "-1"):
    """Rollback migrations to downgrade database.

    Args:
        revision: Target revision (default: "-1" for one step back)
    """
    config = get_alembic_config()

    print(f"Downgrading database to revision: {revision}")

    # Confirm downgrade
    confirm = input("Are you sure you want to downgrade? This may result in data loss. (yes/no): ")
    if confirm.lower() != "yes":
        print("Downgrade cancelled")
        return

    try:
        command.downgrade(config, revision)
        print("✓ Database downgraded successfully")
    except Exception as e:
        print(f"✗ Error downgrading database: {e}")
        sys.exit(1)


def show_current():
    """Show current database revision."""
    config = get_alembic_config()

    print("Current database revision:")
    command.current(config)


def show_history(verbose: bool = False):
    """Show migration history.

    Args:
        verbose: Show detailed history
    """
    config = get_alembic_config()

    print("Migration history:")
    if verbose:
        command.history(config, verbose=True)
    else:
        command.history(config)


def stamp_database(revision: str):
    """Stamp database with a specific revision without running migrations.

    Args:
        revision: Revision to stamp
    """
    config = get_alembic_config()

    print(f"Stamping database with revision: {revision}")

    # Confirm stamp
    confirm = input("Are you sure? This will mark the database as being at this revision. (yes/no): ")
    if confirm.lower() != "yes":
        print("Stamp cancelled")
        return

    try:
        command.stamp(config, revision)
        print("✓ Database stamped successfully")
    except Exception as e:
        print(f"✗ Error stamping database: {e}")
        sys.exit(1)


def check_database():
    """Check if database is up to date with migrations."""
    config = get_alembic_config()

    print("Checking database status...")

    try:
        # Get current revision
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext

        script = ScriptDirectory.from_config(config)

        # Get database URL
        db_url = config.get_main_option("sqlalchemy.url")
        engine = create_engine(db_url)

        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

        # Get head revision
        head_rev = script.get_current_head()

        print(f"Current revision: {current_rev}")
        print(f"Head revision: {head_rev}")

        if current_rev == head_rev:
            print("✓ Database is up to date")
            return True
        else:
            print("✗ Database is NOT up to date")
            print("Run 'python manage_migrations.py upgrade' to update")
            return False

    except Exception as e:
        print(f"✗ Error checking database: {e}")
        return False


def test_connection():
    """Test database connection."""
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("✗ DATABASE_URL not found in environment")
        return False

    print(f"Testing connection to: {db_url.split('@')[1] if '@' in db_url else db_url}")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database Migration Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new migration
  python manage_migrations.py create "add user table"

  # Create empty migration template
  python manage_migrations.py create "custom migration" --no-autogenerate

  # Apply all pending migrations
  python manage_migrations.py upgrade

  # Rollback one migration
  python manage_migrations.py downgrade

  # Rollback to specific revision
  python manage_migrations.py downgrade abc123

  # Show current revision
  python manage_migrations.py current

  # Show migration history
  python manage_migrations.py history

  # Check if database is up to date
  python manage_migrations.py check

  # Test database connection
  python manage_migrations.py test
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message/description")
    create_parser.add_argument("--no-autogenerate", action="store_true",
                              help="Create empty migration template")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Apply migrations")
    upgrade_parser.add_argument("revision", nargs="?", default="head",
                               help="Target revision (default: head)")

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Rollback migrations")
    downgrade_parser.add_argument("revision", nargs="?", default="-1",
                                 help="Target revision (default: -1)")

    # Current command
    subparsers.add_parser("current", help="Show current revision")

    # History command
    history_parser = subparsers.add_parser("history", help="Show migration history")
    history_parser.add_argument("-v", "--verbose", action="store_true",
                               help="Show detailed history")

    # Stamp command
    stamp_parser = subparsers.add_parser("stamp", help="Stamp database with revision")
    stamp_parser.add_argument("revision", help="Revision to stamp")

    # Check command
    subparsers.add_parser("check", help="Check if database is up to date")

    # Test command
    subparsers.add_parser("test", help="Test database connection")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "create":
        create_migration(args.message, autogenerate=not args.no_autogenerate)
    elif args.command == "upgrade":
        upgrade_database(args.revision)
    elif args.command == "downgrade":
        downgrade_database(args.revision)
    elif args.command == "current":
        show_current()
    elif args.command == "history":
        show_history(args.verbose)
    elif args.command == "stamp":
        stamp_database(args.revision)
    elif args.command == "check":
        check_database()
    elif args.command == "test":
        test_connection()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

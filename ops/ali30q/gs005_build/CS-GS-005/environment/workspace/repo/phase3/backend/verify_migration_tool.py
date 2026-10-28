#!/usr/bin/env python3
"""
Verify Migration Tool Installation

This script verifies that the migration tool is properly installed and configured.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False


def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    if Path(dirpath).exists() and Path(dirpath).is_dir():
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {dirpath}")
        return False


def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        print(f"✓ Python package installed: {package_name}")
        return True
    except ImportError:
        print(f"✗ Python package NOT installed: {package_name}")
        return False


def check_environment_variable(var_name):
    """Check if an environment variable is set."""
    value = os.getenv(var_name)
    if value:
        # Mask password in DATABASE_URL
        if var_name == "DATABASE_URL" and "@" in value:
            parts = value.split("@")
            masked = parts[0].split(":")[:-1]
            masked.append("****")
            display_value = ":".join(masked) + "@" + parts[1]
        else:
            display_value = value
        print(f"✓ Environment variable set: {var_name}={display_value}")
        return True
    else:
        print(f"✗ Environment variable NOT set: {var_name}")
        return False


def verify_migration_files():
    """Verify migration files exist."""
    print("\n" + "="*60)
    print("Checking Migration Files")
    print("="*60)

    base_dir = Path(__file__).resolve().parent

    checks = [
        (base_dir / "alembic.ini", "Alembic configuration"),
        (base_dir / "alembic", "Alembic directory"),
        (base_dir / "alembic" / "env.py", "Alembic environment"),
        (base_dir / "alembic" / "script.py.mako", "Migration template"),
        (base_dir / "alembic" / "versions", "Versions directory"),
        (base_dir / "alembic" / "versions" / "001_initial_schema.py", "Initial migration"),
        (base_dir / "manage_migrations.py", "Migration management script"),
        (base_dir / "test_migrations.py", "Migration tests"),
    ]

    results = []
    for filepath, description in checks:
        if filepath.is_dir():
            results.append(check_directory_exists(filepath, description))
        else:
            results.append(check_file_exists(filepath, description))

    return all(results)


def verify_documentation():
    """Verify documentation files exist."""
    print("\n" + "="*60)
    print("Checking Documentation")
    print("="*60)

    base_dir = Path(__file__).resolve().parent

    checks = [
        (base_dir / "DATABASE_MIGRATION_GUIDE.md", "Migration guide"),
        (base_dir / "MIGRATION_TOOL_REPORT.md", "Tool report"),
        (base_dir / "MIGRATION_QUICK_REFERENCE.md", "Quick reference"),
    ]

    results = []
    for filepath, description in checks:
        results.append(check_file_exists(filepath, description))

    return all(results)


def verify_setup_scripts():
    """Verify setup scripts exist."""
    print("\n" + "="*60)
    print("Checking Setup Scripts")
    print("="*60)

    base_dir = Path(__file__).resolve().parent

    checks = [
        (base_dir / "setup_migrations.sh", "Linux/Mac setup script"),
        (base_dir / "setup_migrations.bat", "Windows setup script"),
    ]

    results = []
    for filepath, description in checks:
        results.append(check_file_exists(filepath, description))

    return all(results)


def verify_dependencies():
    """Verify required Python packages are installed."""
    print("\n" + "="*60)
    print("Checking Python Dependencies")
    print("="*60)

    packages = [
        "alembic",
        "sqlalchemy",
        "psycopg2",
        "dotenv",
    ]

    results = []
    for package in packages:
        results.append(check_python_package(package))

    return all(results)


def verify_environment():
    """Verify environment configuration."""
    print("\n" + "="*60)
    print("Checking Environment Configuration")
    print("="*60)

    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ .env file loaded")
    except Exception as e:
        print(f"✗ Failed to load .env file: {e}")
        return False

    # Check DATABASE_URL
    result = check_environment_variable("DATABASE_URL")

    return result


def verify_database_connection():
    """Verify database connection."""
    print("\n" + "="*60)
    print("Checking Database Connection")
    print("="*60)

    try:
        from dotenv import load_dotenv
        from sqlalchemy import create_engine, text

        load_dotenv()
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            print("✗ DATABASE_URL not found")
            return False

        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        print("✓ Database connection successful")
        return True

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def verify_alembic_config():
    """Verify Alembic configuration."""
    print("\n" + "="*60)
    print("Checking Alembic Configuration")
    print("="*60)

    try:
        from alembic.config import Config
        from dotenv import load_dotenv

        load_dotenv()

        base_dir = Path(__file__).resolve().parent
        alembic_ini = base_dir / "alembic.ini"

        config = Config(str(alembic_ini))

        # Check script location
        script_location = config.get_main_option("script_location")
        print(f"✓ Script location: {script_location}")

        # Check database URL
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            config.set_main_option("sqlalchemy.url", db_url)
            print("✓ Database URL configured")

        return True

    except Exception as e:
        print(f"✗ Alembic configuration error: {e}")
        return False


def verify_models():
    """Verify database models can be imported."""
    print("\n" + "="*60)
    print("Checking Database Models")
    print("="*60)

    try:
        from models.database import Base, Task, Agent, Reward, User, APIKey, VerificationLog
        print("✓ All models imported successfully")

        # Check metadata
        tables = Base.metadata.tables.keys()
        print(f"✓ Found {len(tables)} tables in metadata:")
        for table in tables:
            print(f"  - {table}")

        return True

    except Exception as e:
        print(f"✗ Failed to import models: {e}")
        return False


def main():
    """Main verification function."""
    print("="*60)
    print("Migration Tool Installation Verification")
    print("="*60)

    results = {
        "Migration Files": verify_migration_files(),
        "Documentation": verify_documentation(),
        "Setup Scripts": verify_setup_scripts(),
        "Dependencies": verify_dependencies(),
        "Environment": verify_environment(),
        "Database Connection": verify_database_connection(),
        "Alembic Config": verify_alembic_config(),
        "Database Models": verify_models(),
    }

    # Summary
    print("\n" + "="*60)
    print("Verification Summary")
    print("="*60)

    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✓ All checks passed! Migration tool is ready to use.")
        print("="*60)
        print("\nNext steps:")
        print("  1. Run: python manage_migrations.py check")
        print("  2. Run: python manage_migrations.py upgrade")
        print("  3. Run: pytest test_migrations.py")
        print("\nFor help:")
        print("  - python manage_migrations.py --help")
        print("  - cat DATABASE_MIGRATION_GUIDE.md")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("="*60)
        print("\nTroubleshooting:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Configure .env file with DATABASE_URL")
        print("  - Ensure PostgreSQL is running")
        print("  - Check DATABASE_MIGRATION_GUIDE.md for help")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
README for Database Migrations

Quick start guide for using the database migration tool.
"""

# Database Migrations

Complete database migration management using Alembic.

## Quick Start

### 1. Verify Installation

```bash
python verify_migration_tool.py
```

### 2. Setup (First Time)

**Linux/Mac:**
```bash
chmod +x setup_migrations.sh
./setup_migrations.sh
```

**Windows:**
```bash
setup_migrations.bat
```

### 3. Common Commands

```bash
# Check status
python manage_migrations.py check

# Apply migrations
python manage_migrations.py upgrade

# Create new migration
python manage_migrations.py create "description"

# Rollback
python manage_migrations.py downgrade
```

## Documentation

- **MIGRATION_QUICK_REFERENCE.md** - Quick commands and examples
- **DATABASE_MIGRATION_GUIDE.md** - Complete detailed guide
- **MIGRATION_TOOL_REPORT.md** - Technical documentation
- **MIGRATION_IMPLEMENTATION_SUMMARY.md** - Implementation overview

## Files

```
alembic.ini                    # Configuration
alembic/
  ├── env.py                   # Environment setup
  ├── script.py.mako           # Template
  └── versions/                # Migration scripts
      └── 001_initial_schema.py
manage_migrations.py           # CLI tool
test_migrations.py             # Tests
verify_migration_tool.py       # Verification
```

## Testing

```bash
# Run all tests
pytest test_migrations.py -v

# Run specific test
pytest test_migrations.py::TestMigrations -v
```

## Help

```bash
python manage_migrations.py --help
```

## Requirements

- Python 3.8+
- PostgreSQL
- alembic>=1.13.0
- sqlalchemy>=2.0.0
- psycopg2-binary>=2.9.0

## Environment

Set in `.env`:
```
DATABASE_URL=postgresql://user:pass@host:port/database
```

## Support

For detailed help, see DATABASE_MIGRATION_GUIDE.md

# Database Migration Quick Reference

Quick reference guide for common database migration operations.

## Quick Commands

### Setup and Status

```bash
# Test database connection
python manage_migrations.py test

# Check if database is up to date
python manage_migrations.py check

# Show current revision
python manage_migrations.py current

# Show migration history
python manage_migrations.py history
```

### Creating Migrations

```bash
# Auto-generate migration from model changes
python manage_migrations.py create "add new field"

# Create empty migration template
python manage_migrations.py create "custom migration" --no-autogenerate
```

### Applying Migrations

```bash
# Apply all pending migrations
python manage_migrations.py upgrade

# Apply to specific revision
python manage_migrations.py upgrade abc123

# Apply one migration at a time
python manage_migrations.py upgrade +1
```

### Rolling Back

```bash
# Rollback one migration
python manage_migrations.py downgrade

# Rollback to specific revision
python manage_migrations.py downgrade abc123

# Rollback all migrations
python manage_migrations.py downgrade base
```

## Quick Setup

### First Time Setup

```bash
# Windows
setup_migrations.bat

# Linux/Mac
chmod +x setup_migrations.sh
./setup_migrations.sh
```

### Manual Setup

```bash
# 1. Install dependencies
pip install alembic sqlalchemy psycopg2-binary python-dotenv

# 2. Configure database URL in .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nautilus

# 3. Test connection
python manage_migrations.py test

# 4. Apply migrations
python manage_migrations.py upgrade
```

## Common Workflows

### Adding a New Field

```bash
# 1. Edit models/database.py to add field
# 2. Create migration
python manage_migrations.py create "add priority field to tasks"

# 3. Review generated migration
cat alembic/versions/latest_migration.py

# 4. Apply migration
python manage_migrations.py upgrade

# 5. Test
pytest test_migrations.py
```

### Renaming a Column

```bash
# 1. Create migration
python manage_migrations.py create "rename task field" --no-autogenerate

# 2. Edit migration file
# Add: op.alter_column('tasks', 'old_name', new_column_name='new_name')

# 3. Apply
python manage_migrations.py upgrade

# 4. Update models/database.py
```

### Adding an Index

```bash
# 1. Create migration
python manage_migrations.py create "add index for performance"

# 2. Edit migration to add index
# Add: op.create_index('ix_tasks_field', 'tasks', ['field'])

# 3. Apply
python manage_migrations.py upgrade
```

### Creating a New Table

```bash
# 1. Add model to models/database.py
# 2. Create migration
python manage_migrations.py create "add new table"

# 3. Review and apply
python manage_migrations.py upgrade
```

## Testing

```bash
# Run all migration tests
pytest test_migrations.py -v

# Run specific test
pytest test_migrations.py::TestMigrations::test_upgrade_to_head -v

# Test with coverage
pytest test_migrations.py --cov=alembic --cov-report=html
```

## Troubleshooting

### Database Connection Failed

```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test PostgreSQL
pg_isready -h localhost -p 5432

# Verify credentials
psql -h localhost -U postgres -d nautilus
```

### Migration Failed

```bash
# Check current state
python manage_migrations.py current

# View error details
python manage_migrations.py upgrade

# If partially applied, may need to stamp
python manage_migrations.py stamp abc123
```

### Database Out of Sync

```bash
# Check status
python manage_migrations.py check

# Reset development database
python manage_migrations.py downgrade base
python manage_migrations.py upgrade head
```

### Alembic Version Conflict

```bash
# Check version table
psql nautilus -c "SELECT * FROM alembic_version"

# Manually update if needed
python manage_migrations.py stamp abc123
```

## Production Deployment

### Pre-Deployment

```bash
# 1. Backup database
pg_dump nautilus > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test in staging
python manage_migrations.py upgrade

# 3. Verify
python manage_migrations.py check
```

### Deployment

```bash
# Apply migrations
python manage_migrations.py upgrade

# Verify
python manage_migrations.py current

# Test application
curl http://localhost:8000/health
```

### Rollback

```bash
# Rollback one step
python manage_migrations.py downgrade -1

# Or restore from backup
psql nautilus < backup_20260226_120000.sql
```

## File Locations

```
backend/
├── alembic.ini                    # Main config
├── alembic/
│   ├── env.py                     # Environment setup
│   ├── script.py.mako             # Migration template
│   └── versions/                  # Migration scripts
│       ├── 001_initial_schema.py
│       └── ...
├── manage_migrations.py           # CLI tool
├── test_migrations.py             # Tests
├── setup_migrations.sh            # Quick setup (Linux/Mac)
├── setup_migrations.bat           # Quick setup (Windows)
├── DATABASE_MIGRATION_GUIDE.md    # Full guide
└── MIGRATION_QUICK_REFERENCE.md   # This file
```

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/database

# Optional (overrides alembic.ini)
ALEMBIC_CONFIG=path/to/alembic.ini
```

## Migration File Structure

```python
"""migration description

Revision ID: abc123
Revises: previous_revision
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'previous_revision'

def upgrade() -> None:
    """Apply changes."""
    pass

def downgrade() -> None:
    """Revert changes."""
    pass
```

## Common Operations

### Add Column
```python
op.add_column('table', sa.Column('name', sa.String(100)))
```

### Drop Column
```python
op.drop_column('table', 'name')
```

### Rename Column
```python
op.alter_column('table', 'old_name', new_column_name='new_name')
```

### Add Index
```python
op.create_index('ix_table_field', 'table', ['field'])
```

### Drop Index
```python
op.drop_index('ix_table_field', 'table')
```

### Add Foreign Key
```python
op.create_foreign_key('fk_name', 'source', 'target', ['col'], ['ref_col'])
```

### Drop Foreign Key
```python
op.drop_constraint('fk_name', 'table', type_='foreignkey')
```

### Create Table
```python
op.create_table(
    'table_name',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('name', sa.String(100))
)
```

### Drop Table
```python
op.drop_table('table_name')
```

### Execute SQL
```python
op.execute('UPDATE table SET field = value')
```

## Best Practices

✅ **DO**:
- Test migrations in development first
- Review auto-generated migrations
- Use descriptive migration messages
- Backup before production migrations
- One logical change per migration
- Add indexes for performance
- Document complex migrations

❌ **DON'T**:
- Skip testing migrations
- Combine unrelated changes
- Forget to handle data migrations
- Apply untested migrations to production
- Ignore downgrade functions
- Commit without reviewing

## Help and Documentation

```bash
# Command help
python manage_migrations.py --help
python manage_migrations.py create --help

# Full documentation
cat DATABASE_MIGRATION_GUIDE.md

# Tool report
cat MIGRATION_TOOL_REPORT.md
```

## Support

For detailed information, see:
- **DATABASE_MIGRATION_GUIDE.md** - Complete guide
- **MIGRATION_TOOL_REPORT.md** - Tool documentation
- **test_migrations.py** - Usage examples
- **alembic/versions/** - Migration examples

---

**Last Updated**: 2026-02-26
**Version**: 1.0.0

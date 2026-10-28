# Database Migration Guide

Complete guide for managing database migrations in Nautilus Phase 3 using Alembic.

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Creating Migrations](#creating-migrations)
4. [Applying Migrations](#applying-migrations)
5. [Rolling Back Migrations](#rolling-back-migrations)
6. [Migration History](#migration-history)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

Alembic is a database migration tool for SQLAlchemy. It allows you to:

- Track database schema changes over time
- Apply changes incrementally
- Rollback changes if needed
- Maintain consistency across environments

### Key Concepts

- **Migration**: A script that describes changes to the database schema
- **Revision**: A unique identifier for each migration
- **Upgrade**: Apply migrations to move forward
- **Downgrade**: Rollback migrations to move backward
- **Head**: The latest migration revision

## Setup

### Prerequisites

1. PostgreSQL database running
2. Python environment with dependencies installed
3. Database connection configured in `.env`

### Configuration Files

- `alembic.ini`: Main Alembic configuration
- `alembic/env.py`: Environment configuration
- `alembic/script.py.mako`: Migration template
- `alembic/versions/`: Migration scripts directory

### Environment Variables

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nautilus
```

### Verify Setup

```bash
# Test database connection
python manage_migrations.py test

# Check current status
python manage_migrations.py check
```

## Creating Migrations

### Auto-Generate Migration

Automatically detect model changes and generate migration:

```bash
python manage_migrations.py create "add new field to tasks"
```

This will:
1. Compare current database schema with models
2. Generate migration script with detected changes
3. Save to `alembic/versions/`

### Manual Migration

Create empty migration template for custom changes:

```bash
python manage_migrations.py create "custom migration" --no-autogenerate
```

Edit the generated file to add custom SQL or operations.

### Migration File Structure

```python
"""add new field to tasks

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'previous_revision'

def upgrade() -> None:
    """Apply changes."""
    op.add_column('tasks', sa.Column('new_field', sa.String(100)))

def downgrade() -> None:
    """Revert changes."""
    op.drop_column('tasks', 'new_field')
```

## Applying Migrations

### Upgrade to Latest

Apply all pending migrations:

```bash
python manage_migrations.py upgrade
```

### Upgrade to Specific Revision

```bash
python manage_migrations.py upgrade abc123def456
```

### Upgrade Step by Step

```bash
# Upgrade one migration at a time
python manage_migrations.py upgrade +1
```

### Verification

After upgrading, verify the changes:

```bash
# Check current revision
python manage_migrations.py current

# Verify database status
python manage_migrations.py check
```

## Rolling Back Migrations

### Downgrade One Step

Rollback the most recent migration:

```bash
python manage_migrations.py downgrade
```

**Warning**: This will prompt for confirmation as it may result in data loss.

### Downgrade to Specific Revision

```bash
python manage_migrations.py downgrade abc123def456
```

### Downgrade to Base

Remove all migrations (dangerous):

```bash
python manage_migrations.py downgrade base
```

### Important Notes

- Always backup data before downgrading
- Downgrade may result in data loss
- Test downgrades in development first
- Some changes cannot be automatically reversed

## Migration History

### View Current Revision

```bash
python manage_migrations.py current
```

Output:
```
Current database revision:
abc123def456 (head)
```

### View Migration History

```bash
python manage_migrations.py history
```

Output:
```
abc123def456 -> def789ghi012 (head), add new field
xyz789abc123 -> abc123def456, add gas fee fields
<base> -> xyz789abc123, initial schema
```

### Verbose History

```bash
python manage_migrations.py history -v
```

Shows detailed information including:
- Full revision IDs
- Migration messages
- Creation dates
- Dependencies

## Best Practices

### 1. Always Review Auto-Generated Migrations

```bash
# After creating migration, review the file
cat alembic/versions/latest_migration.py
```

Check for:
- Correct column types
- Proper indexes
- Foreign key constraints
- Data migrations if needed

### 2. Test Migrations in Development

```bash
# Apply migration
python manage_migrations.py upgrade

# Test application
python -m pytest

# Rollback to test downgrade
python manage_migrations.py downgrade

# Re-apply
python manage_migrations.py upgrade
```

### 3. Use Descriptive Messages

```bash
# Good
python manage_migrations.py create "add email verification to users"

# Bad
python manage_migrations.py create "update"
```

### 4. One Logical Change Per Migration

Don't combine unrelated changes:

```bash
# Good - separate migrations
python manage_migrations.py create "add user preferences table"
python manage_migrations.py create "add task priority field"

# Bad - combined
python manage_migrations.py create "add user preferences and task priority"
```

### 5. Handle Data Migrations Carefully

When renaming or transforming data:

```python
def upgrade():
    # Create new column
    op.add_column('tasks', sa.Column('new_status', sa.String(20)))

    # Migrate data
    op.execute("""
        UPDATE tasks
        SET new_status = CASE
            WHEN old_status = 'open' THEN 'OPEN'
            WHEN old_status = 'closed' THEN 'COMPLETED'
        END
    """)

    # Drop old column
    op.drop_column('tasks', 'old_status')
```

### 6. Add Indexes for Performance

```python
def upgrade():
    op.create_index('ix_tasks_status_created', 'tasks', ['status', 'created_at'])
```

### 7. Use Transactions

Migrations run in transactions by default. For operations that can't run in transactions:

```python
def upgrade():
    # Disable transaction for this operation
    op.execute('CREATE INDEX CONCURRENTLY ix_tasks_large ON tasks(field)')
```

### 8. Document Complex Migrations

```python
def upgrade():
    """
    Add composite index for task queries.

    This index improves performance for queries filtering by
    status and sorting by created_at, which is used in the
    list_tasks endpoint.
    """
    op.create_index('ix_tasks_status_created', 'tasks', ['status', 'created_at'])
```

### 9. Version Control

```bash
# Always commit migrations with code changes
git add alembic/versions/new_migration.py
git commit -m "Add migration for new feature"
```

### 10. Backup Before Production Migrations

```bash
# Backup database
pg_dump nautilus > backup_$(date +%Y%m%d_%H%M%S).sql

# Apply migration
python manage_migrations.py upgrade

# Verify
python manage_migrations.py check
```

## Troubleshooting

### Migration Fails

```bash
# Check error message
python manage_migrations.py upgrade

# If migration partially applied, check current state
python manage_migrations.py current

# May need to manually fix database and stamp revision
python manage_migrations.py stamp abc123def456
```

### Database Out of Sync

```bash
# Check status
python manage_migrations.py check

# If database has changes not in migrations
python manage_migrations.py create "sync database state" --no-autogenerate

# Manually edit migration to match current state
# Then stamp without running
python manage_migrations.py stamp head
```

### Merge Conflicts in Migrations

```bash
# If two branches created migrations with same down_revision
# Alembic will detect this

# Create merge migration
alembic merge -m "merge branches" rev1 rev2
```

### Reset Development Database

```bash
# Drop all tables
python manage_migrations.py downgrade base

# Re-apply all migrations
python manage_migrations.py upgrade head
```

### Connection Issues

```bash
# Test connection
python manage_migrations.py test

# Check DATABASE_URL
echo $DATABASE_URL

# Verify PostgreSQL is running
pg_isready -h localhost -p 5432
```

### Alembic Version Table Issues

```bash
# If alembic_version table is corrupted
# Manually fix in database
psql nautilus -c "SELECT * FROM alembic_version"

# Update to correct revision
psql nautilus -c "UPDATE alembic_version SET version_num='abc123def456'"

# Or use stamp command
python manage_migrations.py stamp abc123def456
```

## Common Operations

### Add Column

```python
def upgrade():
    op.add_column('tasks', sa.Column('priority', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('tasks', 'priority')
```

### Rename Column

```python
def upgrade():
    op.alter_column('tasks', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('tasks', 'new_name', new_column_name='old_name')
```

### Add Index

```python
def upgrade():
    op.create_index('ix_tasks_priority', 'tasks', ['priority'])

def downgrade():
    op.drop_index('ix_tasks_priority', 'tasks')
```

### Add Foreign Key

```python
def upgrade():
    op.create_foreign_key(
        'fk_tasks_agent_id',
        'tasks', 'agents',
        ['agent_id'], ['agent_id']
    )

def downgrade():
    op.drop_constraint('fk_tasks_agent_id', 'tasks', type_='foreignkey')
```

### Create Table

```python
def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False)
    )

def downgrade():
    op.drop_table('new_table')
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Test migrations in staging environment
- [ ] Backup production database
- [ ] Review migration scripts
- [ ] Plan rollback strategy
- [ ] Schedule maintenance window if needed
- [ ] Notify team of deployment

### Deployment Steps

```bash
# 1. Backup database
pg_dump nautilus > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check current status
python manage_migrations.py check

# 3. Apply migrations
python manage_migrations.py upgrade

# 4. Verify
python manage_migrations.py current

# 5. Test application
curl http://localhost:8000/health

# 6. Monitor logs
tail -f logs/app.log
```

### Rollback Plan

```bash
# If issues occur, rollback
python manage_migrations.py downgrade -1

# Restore from backup if needed
psql nautilus < backup_20260226_120000.sql
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues or questions:
1. Check this guide
2. Review migration scripts in `alembic/versions/`
3. Check application logs
4. Consult team documentation

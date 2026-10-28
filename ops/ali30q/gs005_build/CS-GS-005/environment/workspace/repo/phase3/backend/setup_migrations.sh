#!/bin/bash
# Quick Start Script for Database Migrations

echo "=================================="
echo "Database Migration Quick Start"
echo "=================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please create .env file with DATABASE_URL"
    exit 1
fi

echo "Step 1: Testing database connection..."
python manage_migrations.py test
if [ $? -ne 0 ]; then
    echo "Error: Database connection failed"
    echo "Please check your DATABASE_URL in .env"
    exit 1
fi
echo ""

echo "Step 2: Checking migration status..."
python manage_migrations.py check
echo ""

echo "Step 3: Applying migrations..."
python manage_migrations.py upgrade
if [ $? -ne 0 ]; then
    echo "Error: Migration failed"
    exit 1
fi
echo ""

echo "Step 4: Verifying current revision..."
python manage_migrations.py current
echo ""

echo "=================================="
echo "Migration setup complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  - Review DATABASE_MIGRATION_GUIDE.md for detailed usage"
echo "  - Run 'pytest test_migrations.py' to test migrations"
echo "  - Use 'python manage_migrations.py --help' for more commands"
echo ""

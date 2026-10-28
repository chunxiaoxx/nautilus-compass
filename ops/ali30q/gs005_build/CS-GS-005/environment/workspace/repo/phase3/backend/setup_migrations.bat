@echo off
REM Quick Start Script for Database Migrations (Windows)

echo ==================================
echo Database Migration Quick Start
echo ==================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo Error: .env file not found
    echo Please create .env file with DATABASE_URL
    exit /b 1
)

echo Step 1: Testing database connection...
python manage_migrations.py test
if errorlevel 1 (
    echo Error: Database connection failed
    echo Please check your DATABASE_URL in .env
    exit /b 1
)
echo.

echo Step 2: Checking migration status...
python manage_migrations.py check
echo.

echo Step 3: Applying migrations...
python manage_migrations.py upgrade
if errorlevel 1 (
    echo Error: Migration failed
    exit /b 1
)
echo.

echo Step 4: Verifying current revision...
python manage_migrations.py current
echo.

echo ==================================
echo Migration setup complete!
echo ==================================
echo.
echo Next steps:
echo   - Review DATABASE_MIGRATION_GUIDE.md for detailed usage
echo   - Run 'pytest test_migrations.py' to test migrations
echo   - Use 'python manage_migrations.py --help' for more commands
echo.

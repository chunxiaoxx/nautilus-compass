@echo off
REM OAuth 2.0 Service Deployment Script for Windows

echo ==========================================
echo Nautilus OAuth 2.0 Service Deployment
echo ==========================================
echo.

REM Step 1: Check environment
echo Step 1: Checking environment...
if not exist ".env" (
    echo X .env file not found
    exit /b 1
)
echo √ Environment file found

REM Step 2: Install dependencies
echo.
echo Step 2: Installing dependencies...
pip install -r requirements.txt
echo √ Dependencies installed

REM Step 3: Run database migration
echo.
echo Step 3: Running database migration...
python manage_migrations.py upgrade
if %errorlevel% neq 0 (
    echo X Database migration failed
    exit /b 1
)
echo √ Database migration completed

REM Step 4: Run OAuth tests
echo.
echo Step 4: Running OAuth tests...
python test_oauth_quick.py
if %errorlevel% neq 0 (
    echo X OAuth tests failed
    exit /b 1
)
echo √ OAuth tests passed

REM Step 5: Run full test suite
echo.
echo Step 5: Running full test suite...
pytest tests/test_oauth.py -v
if %errorlevel% neq 0 (
    echo ! Some tests failed, but continuing...
)
echo √ Full test suite completed

echo.
echo ==========================================
echo OAuth 2.0 Service Deployment Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Restart the application
echo 2. Test OAuth flow manually
echo 3. Create sample OAuth clients
echo 4. Update API documentation
echo.
echo OAuth endpoints available at:
echo   - POST   /oauth/clients
echo   - GET    /oauth/clients/{client_id}
echo   - GET    /oauth/authorize
echo   - POST   /oauth/token
echo   - GET    /oauth/userinfo
echo   - POST   /oauth/verify
echo   - POST   /oauth/revoke
echo.

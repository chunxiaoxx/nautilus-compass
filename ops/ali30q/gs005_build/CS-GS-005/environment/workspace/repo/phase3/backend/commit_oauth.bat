@echo off
REM Git commit script for OAuth 2.0 implementation

echo ==========================================
echo Committing OAuth 2.0 Implementation
echo ==========================================
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo X Not in a git repository
    echo Please run this from the repository root
    exit /b 1
)

REM Show status
echo Git status:
git status --short

echo.
echo Files to be committed:
echo   New files: 16
echo   Modified files: 2
echo.

REM Ask for confirmation
set /p confirm="Proceed with commit? (y/n) "
if /i not "%confirm%"=="y" (
    echo Commit cancelled
    exit /b 0
)

REM Stage all OAuth-related files
echo.
echo Staging files...

REM New files
git add models/oauth.py
git add api/oauth.py
git add migrations/002_add_oauth_tables.py
git add sdk/python/nautilus_oauth.py
git add sdk/python/examples.py
git add sdk/python/setup.py
git add sdk/python/README.md
git add tests/test_oauth.py
git add test_oauth_quick.py
git add docs/OAUTH_GUIDE.md
git add OAUTH_IMPLEMENTATION.md
git add OAUTH_README.md
git add OAUTH_FINAL_REPORT.md
git add OAUTH_FILES_SUMMARY.md
git add deploy_oauth.sh
git add deploy_oauth.bat
git add COMMIT_MESSAGE.txt

REM Modified files
git add models/database.py
git add main.py

echo √ Files staged

REM Commit with message from file
echo.
echo Creating commit...
git commit -F COMMIT_MESSAGE.txt

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo √ Commit successful!
    echo ==========================================
    echo.
    echo Next steps:
    echo 1. Review the commit: git show
    echo 2. Push to remote: git push
    echo 3. Create pull request
    echo.
) else (
    echo.
    echo X Commit failed
    exit /b 1
)

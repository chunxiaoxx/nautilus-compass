@echo off
echo Starting Nautilus Backend Service...

set DATABASE_URL=postgresql://nautilus:nautilus_staging_2024@localhost:5432/nautilus_staging
set REDIS_URL=redis://localhost:6379/0
set ENVIRONMENT=staging
set LOG_LEVEL=INFO

echo Database: %DATABASE_URL%
echo Redis: %REDIS_URL%
echo Environment: %ENVIRONMENT%

python -m uvicorn main:app --host 0.0.0.0 --port 8001

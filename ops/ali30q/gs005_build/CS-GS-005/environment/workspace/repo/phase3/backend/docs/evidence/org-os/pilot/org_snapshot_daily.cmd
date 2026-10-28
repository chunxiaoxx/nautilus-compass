@echo off
cd /d C:\Users\chunx\Projects\nautilus-core\phase3\backend
set "DATABASE_URL=postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production"
set "PY=C:\Users\chunx\Projects\nautilus-core\phase3\backend\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo PY missing - Store python upgraded? fix org_snapshot_daily.cmd
  exit /b 3
)
"%PY%" docs\evidence\org-os\pilot\frame_snapshot.py --push > C:\Users\chunx\AppData\Local\Temp\org_snap.log 2>&1

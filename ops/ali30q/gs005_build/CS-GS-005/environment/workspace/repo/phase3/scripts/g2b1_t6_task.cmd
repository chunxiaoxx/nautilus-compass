@echo off
cd /d C:\Users\chunx\Projects\nautilus-core\phase3\backend
for /f "tokens=1,* delims==" %%a in ('findstr /b "CHUNXIAO_API_KEY=" ".env"') do set "%%a=%%b"
set "T6_PROVIDER=chunxiao_k3"
C:\Users\chunx\Projects\nautilus-core\phase3\backend\.venv\Scripts\python.exe -u tools\g2_b1_t6_l2ext.py > docs\evidence\g2b1_t6_20260908\run6.log 2>&1

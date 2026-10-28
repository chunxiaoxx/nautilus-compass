@echo off
REM 飞轮 worker 引导启动器(schtasks 261 字符坑:TR 只指本文件)
cd /d C:\Users\chunx\Projects\nautilus-core\phase3\backend
set "FRAME_API_KEY=nautilus-org-flywheel-8ddfbea30ce2e68d0f5fdf239f8fa619"
set "FRAME_WORKER_FLYWHEEL_DIR=C:\Users\chunx\Projects\nautilusflywheel"
set "FRAME_API_BASE=https://www.nautilus.social"
python ops\frame_worker.py flywheel >> %USERPROFILE%\frame_worker.log 2>&1

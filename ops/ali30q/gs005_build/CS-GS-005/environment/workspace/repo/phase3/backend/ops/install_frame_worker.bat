@echo off
REM 飞轮常驻 worker 安装(本地 schtasks,同 g2b1 executor 配方;2026-09-18 方案函 403-406)
REM 用法:install_frame_worker.bat <api_key>   (org-auth:flywheel 那把)
REM 30 分钟一轮;日志 %USERPROFILE%\frame_worker.log;删除:schtasks /Delete /TN nautilus-frame-worker-flywheel /F
setlocal
if "%~1"=="" (echo usage: install_frame_worker.bat ^<api_key^> & exit /b 2)
set KEY=%~1
set DIR=C:\Users\chunx\Projects\nautilus-core\phase3\backend
set FWDIR=C:\Users\chunx\Projects\nautilusflywheel

schtasks /Create /TN nautilus-frame-worker-flywheel /SC MINUTE /MO 30 /F ^
  /TR "cmd /c cd /d %DIR% && set FRAME_API_KEY=%KEY%&& set FRAME_WORKER_FLYWHEEL_DIR=%FWDIR%&& set FRAME_API_BASE=https://www.nautilus.social&& python ops\frame_worker.py flywheel >> %USERPROFILE%\frame_worker.log 2>&1"

if %errorlevel%==0 (echo OK: worker installed, every 30min. Check: schtasks /Query /TN nautilus-frame-worker-flywheel) else (echo FAIL %errorlevel%)
endlocal

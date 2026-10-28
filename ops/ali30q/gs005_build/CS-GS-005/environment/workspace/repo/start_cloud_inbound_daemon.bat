@echo off
REM cloud_inbound_daemon launcher · Windows-side systemd equivalent
REM Used by the .service file (ExecStart), or run manually:
REM   start_cloud_inbound_daemon.bat
REM
REM Anchors #4 + #6: cross-dialog coordination daemon; restarts on crash.

cd /d C:\Users\chunx\Projects\nautilus-core
set PYTHONIOENCODING=utf-8
:loop
"C:\Users\chunx\AppData\Local\Programs\Python\Python313\python.exe" ^
  genopt_factory/tools/cloud_inbound_daemon.py --interval 300
echo [%date% %time%] daemon exited; restarting in 30s
timeout /t 30 /nobreak > nul
goto loop
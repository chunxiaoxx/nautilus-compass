@echo off
rem GOAL_SSOT 目标模式心跳 · 每小时执法(recall 探活 + 合约到期扫描),红灯自动写 obs 广播
:loop
start "" /min "C:\Users\chunx\Projects\nautilus-compass\.venv\Scripts\python.exe" "C:\Users\chunx\Projects\nautilus-compass\tools\compass_goal_heartbeat.py"
timeout /t 3600 /nobreak >nul
goto loop

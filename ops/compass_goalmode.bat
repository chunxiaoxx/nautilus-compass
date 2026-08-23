@echo off
rem GOAL_SSOT 目标模式心跳 · 每小时执法(recall 探活 + 合约到期扫描),红灯自动写 obs 广播
:loop
python "C:\Users\chunx\Projects\nautilus-compass\tools\compass_goal_heartbeat.py" >nul 2>&1
timeout /t 3600 /nobreak >nul
goto loop

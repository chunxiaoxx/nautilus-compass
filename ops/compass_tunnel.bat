@echo off
rem DOGFOOD_BRIDGE Plan A · cloud compass MCP 隧道保活(登录自启 + 每小时重启)
rem 断连自动重试。手动起:双击本文件。
:loop
ssh -N -L 9877:127.0.0.1:9877 -o ServerAliveInterval=30 -o ServerAliveCountMax=4 -o ExitOnForwardFailure=yes cloud
timeout /t 10 /nobreak >nul
goto loop

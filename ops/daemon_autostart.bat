@echo off
REM nautilus-compass daemon · Windows autostart
REM
REM 安装 (一次性):
REM   1. Win+R → 输 "shell:startup" → 回车 (打开 Startup 文件夹)
REM   2. 把这个 .bat 的快捷方式拖进去 (右键 → "创建快捷方式")
REM   3. 重启验证: 开机后 python -c "import socket;s=socket.socket();s.settimeout(2);s.connect(('127.0.0.1',9876));print('ok')"
REM
REM 或者 Task Scheduler (更稳 · 不依赖登录):
REM   schtasks /Create /TN "NautilusCompassDaemon" /TR "%~dp0daemon_autostart.bat" /SC ONLOGON /RL HIGHEST
REM
REM 卸载: 删除 startup 里的快捷方式 · 或 schtasks /Delete /TN "NautilusCompassDaemon"

setlocal

REM 防双开 · 看 9876 端口是否已监听
netstat -ano | findstr ":9876" | findstr LISTENING > nul
if %errorlevel% == 0 (
    echo [compass-autostart] daemon already running
    exit /b 0
)

REM 后台启动 · 不显示窗口
set LOG=%TEMP%\compass_daemon.log
echo [compass-autostart] launching daemon @ %DATE% %TIME% >> "%LOG%"
start "" /B pythonw "%USERPROFILE%\.claude\plugins\nautilus-compass\daemon.py" >> "%LOG%" 2>&1

echo [compass-autostart] started · log: %LOG%
endlocal

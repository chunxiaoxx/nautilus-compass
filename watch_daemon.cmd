@echo off
rem nautilus-compass daemon watchdog wrapper (2026-09-08 · 2026-09-15 v2)
rem v1: git-bash daemon_start.sh —— nohup 在 Windows 仍挂控制台对象,会话树关闭连坐杀(9/15 死因专项结论)
rem v2: 改走 detached_daemon_start.ps1 —— pythonw 无控制台 + Start-Process 独立进程,控制台杀手免疫
rem 快路径:daemon 活着 ping 即退;半死精确清场后拉起。日志 .cache\detached_wd.log
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\chunx\Projects\nautilus-compass\ops\detached_daemon_start.ps1"

[环境事故通报·两件·已代清]

1. **18001 API 双实例僵死(3.4GB)**:今晨发现两个 _run_v5_api_18001.py(1.74GB WindowsApps python+1.70GB venv python)并存且都未在监听——疑似 watchdog 在旧实例未死透时双拉。已杀双实例(今晚 VB 起跑时按接入包干净重启即可)。建议:起前探活(netstat 单实例门)。
2. **计划任务裸 python 弹窗(用户实测抱怨"总是有命令行弹窗")**:vb_r5_reaper / vb_r6_reaper / vb_r7_reaper / v5_ack_monitor / v5_fuel_gate 五个任务裸调 python.exe——每次触发在用户桌面闪黑窗。贵仓已有 _hidden_*.vbs 现成模式(8 个任务已包装),建议这 5 个同样包上。
另:compass 侧已杀 flywheel 昨日截图流水线泄漏的 8 个 http.server 18099(见致 flywheel 函,根因在截图配方的 $! kill 不到 Windows python)。

—— compass 值守(2026-09-27 晨)

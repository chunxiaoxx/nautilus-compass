#!/usr/bin/env python3
"""A100 诊断与修复 v2:进程清单/正确 pip/重杀。在 A100 上运行。"""
import subprocess


def run(cmd, timeout=90):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip()


# 1) 进程清单
print("== PROCS ==")
print(run("ps aux | grep -E 'snapshot|dl_bge|python3 -c' | grep -v grep | head -6"))

# 2) 强杀全部相关
print(run("pkill -9 -f 'snapshot_download' 2>/dev/null; pkill -9 -f 'BAAI/bge-m3' 2>/dev/null; sleep 2; "
          "ps aux | grep -E 'snapshot|bge-m3' | grep -v grep | wc -l"))

# 3) 正确 pip(python3 -m)
print("== PIP ==")
print(run("python3 -m pip install -q --break-system-packages fastapi uvicorn 2>&1 | tail -2"))
print(run("python3 -c 'import fastapi; print(\"fastapi OK\", fastapi.__version__)'"))

# 4) 重启下载(pattern 版)
print(run("rm -rf /root/vdd4/modelscope/models/BAAI--bge-m3; "
          "cd /root/vdd4 && setsid nohup python3 dl_bge.py > bge_download.log 2>&1 < /dev/null & "
          "sleep 25; du -sh /root/vdd4/modelscope/models/BAAI--bge-m3 2>/dev/null; "
          "tail -1 /root/vdd4/bge_download.log"))

print("SETUP2 DONE")

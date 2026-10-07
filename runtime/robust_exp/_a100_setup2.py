#!/usr/bin/env python3
"""A100 上执行的组织脚本(R301 续):部署嵌入服务前置检查。在 A100 上运行。"""
import subprocess
import sys


def run(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip()


# 1) 杀旧下载 + pattern 重下(跳 onnx)
print(run(
    "pkill -f snapshot_download 2>/dev/null; sleep 1; "
    "rm -rf /root/vdd4/modelscope/models/BAAI--bge-m3; "
    "cd /root/vdd4 && setsid nohup python3 dl_bge.py > bge_download.log 2>&1 < /dev/null & "
    "sleep 2; tail -1 bge_download.log; echo DL_RESTARTED"))

# 2) fastapi 安装与验证
print(run("pip install -q --break-system-packages fastapi uvicorn 2>&1 | tail -1"))
print(run("python3 -c 'import fastapi; print(\"fastapi\", fastapi.__version__)'"))

# 3) 下载进度
print(run("sleep 20; du -sh /root/vdd4/modelscope/models/BAAI--bge-m3 2>/dev/null; "
          "tail -1 /root/vdd4/bge_download.log"))

print("SETUP DONE")

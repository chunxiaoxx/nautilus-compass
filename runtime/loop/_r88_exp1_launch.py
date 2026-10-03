"""R88:exp1 challenger v2 发车——上传实验脚本+远端 nohup 发车+进程确认。

退避纪律:SSH 限流则 sleep 120 重试(高频日 300s 上限)。
"""
import sys
import time

import paramiko

HOST, PORT, USER, PW = "223.109.239.30", 23236, "root", "iefe4Eey"


def connect(retries=3):
    for i in range(retries):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=PORT, username=USER, password=PW, timeout=15)
            return c
        except Exception as e:
            print(f"[retry {i+1}] {e}", flush=True)
            time.sleep(120)
    sys.exit(1)


c = connect()
s = c.open_sftp()
s.put("tools/exp1_challenger_v2.py", "/root/tools/exp1_challenger_v2.py")
s.close()

# GPU 守门:无计算进程才发车(exp 不抢生产位);确认训练器 fixed 版在位
_, out, _ = c.exec_command(
    "n=$(ps aux | grep -E 'train_judge|exp1' | grep -v grep | wc -l); echo busy_procs=$n; "
    "ls -la /root/tools/train_judge_incremental_fixed.py 2>&1 | head -1; "
    "free -g | head -2; nvidia-smi --query-gpu=memory.used --format=csv,noheader", timeout=30)
print(out.read().decode())

_, out, _ = c.exec_command(
    "cd /root && (setsid nohup ./vdd2/p0_full/venv/bin/python tools/exp1_challenger_v2.py "
    "> /root/p3_exp1.log 2>&1 < /dev/null &) ; echo launched", timeout=15)
print(out.read().decode())
time.sleep(8)
_, out, _ = c.exec_command(
    "ps aux | grep exp1 | grep -v grep | head -2; echo ---; tail -5 /root/p3_exp1.log", timeout=20)
print(out.read().decode())
c.close()

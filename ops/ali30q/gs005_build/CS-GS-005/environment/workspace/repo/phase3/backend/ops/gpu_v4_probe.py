#!/usr/bin/env python3
"""GPU 649392 v4 蒸馏轮探针 · 平台监督用(2026-08-26)。

探: _d4_gpu.py 进程是否在跑 / gen_*.jsonl 产出行数 / adapter 状态。
凭据: 智星云 CLI connect --include-sensitive(本地 ~/.config/ai-galaxy-compute/)。
退出码: 0=仍在跑或未完成; 1=两臂 gen 产出齐(出结果了)。
"""
import json
import os
import subprocess
import sys

CONTAINER = "18510625230_lyg0191_8af0991f4f984beb82277998541941ef_u1_c3"
ENV = dict(os.environ, AI_GALAXY_CREDENTIALS_FILE=os.path.expanduser(
    "~/.config/ai-galaxy-compute/credentials.json"))


def main() -> int:
    p = subprocess.run(
        [sys.executable, "-m", "ai_galaxy_compute", "connect", CONTAINER,
         "--include-sensitive"],
        capture_output=True, text=True, cwd=os.path.expanduser(
            "~/.workbuddy/ai-galaxy-compute"), env=ENV, timeout=30)
    d = json.loads(p.stdout)
    probe = ("nvidia-smi --query-gpu=memory.used --format=csv,noheader; "
             "ps aux | grep -E '_d4_gpu|distill' | grep -v grep | head -3; "
             "for f in /root/gen_*.jsonl; do [ -f $f ] && echo $f $(wc -l < $f); done; "
             "ls /root/distill7b_out/adapter/ 2>/dev/null | head -3")
    code = ("import paramiko;c=paramiko.SSHClient();"
            "c.set_missing_host_key_policy(paramiko.AutoAddPolicy());"
            f"c.connect('js1.blockelite.cn',port=30116,username='root',password={d['initial_password']!r},timeout=12);"
            f"i,o,e=c.exec_command({probe!r},timeout=25);print(o.read().decode('utf-8','replace'))")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, timeout=45)
    out = r.stdout or r.stderr[:300]
    print(out)
    gens = [l for l in out.splitlines() if l.strip().startswith("/root/gen_")]
    arms_done = [l for l in gens if int(l.split()[-1]) > 0]
    if len(arms_done) >= 2 and "_d4_gpu" not in out:
        print("VERDICT_READY: 两臂 gen 已产出且进程退出")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

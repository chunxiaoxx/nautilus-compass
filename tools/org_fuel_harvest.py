#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL 判分收割段(2026-10-08 语料冲刺):A100 verdicts → 本地 → 管道重跑 → 站点语料数刷新。

用法:
  set -a; source ~/.claude/.cache/a100_env; set +a
  python tools/org_fuel_harvest.py          # 拉取+本地管道+刷新 corpus_stats
  python tools/org_fuel_harvest.py --check  # 只查远端进度(不写任何文件)

A100 环境锚:判分脚本必须用 /root/venv/bin/python 绝对路径启动
(nohup 非登录 shell 无 conda/python 别名,2026-10-08 rerun 空转教训)。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTE_DIR = "/root/vdd4/robust_exp"
VERDICTS = ("fuel_verdicts.jsonl", "fuel_verdicts_docs.jsonl")
LOCAL_DIR = ROOT / "runtime/org_fuel"


def ssh_run(host: str, port: str, pw: str, cmd: str, timeout: int = 30) -> str:
    import paramiko
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, port=int(port), username="root", password=pw, timeout=20)
    try:
        _, out, err = c.exec_command(cmd, timeout=timeout)
        text = out.read().decode(errors="replace")
        e = err.read().decode(errors="replace")
        return text if text.strip() else e
    finally:
        c.close()


def remote_progress(env: dict) -> str:
    return ssh_run(
        env["A100_HOST"], env["A100_PORT"], env["A100_PW"],
        f"ls {REMOTE_DIR}/judge_rerun.flag >/dev/null 2>&1 && echo FLAG_DONE || echo RUNNING; "
        f"tail -1 {REMOTE_DIR}/judge_rerun_main.log 2>/dev/null; "
        f"tail -1 {REMOTE_DIR}/judge_rerun_docs.log 2>/dev/null; "
        f"ps aux | grep 'python _fuel_judge' | grep -v grep | wc -l",
    )


def sftp_pull(env: dict):
    import paramiko
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(env["A100_HOST"], port=int(env["A100_PORT"]), username="root",
              password=env["A100_PW"], timeout=20)
    s = c.open_sftp()
    try:
        for f in VERDICTS:
            s.get(f"{REMOTE_DIR}/{f}", str(LOCAL_DIR / f))
            n = sum(1 for _ in open(LOCAL_DIR / f, encoding="utf-8") if _.strip())
            print(f"PULL {f} lines={n}")
    finally:
        s.close()
        c.close()


def main() -> int:
    env = {k: v for k, v in os.environ.items() if k.startswith("A100_")}
    if not env.get("A100_HOST"):
        print("缺 A100_ 环境变量(source ~/.claude/.cache/a100_env,注意 set -a)", file=sys.stderr)
        return 1

    prog = remote_progress(env)
    print("远端进度:", prog.strip()[:300])
    if "--check" in sys.argv:
        return 0
    if "FLAG_DONE" not in prog:
        print("判分未完成,先 --check 轮询;完成后再收割", file=sys.stderr)
        return 1

    sftp_pull(env)

    # 管道重跑(qid 合并+触发器)
    r = subprocess.run([sys.executable, "tools/corpus_pipeline.py"], cwd=ROOT)
    if r.returncode != 0:
        return r.returncode
    m = json.loads((ROOT / "runtime/verdict_corpus/manifest_corpus_pipeline.json").read_text(encoding="utf-8"))
    print("merged_unique_by_qid =", m["merged_unique_by_qid"], "| train =", m["train_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

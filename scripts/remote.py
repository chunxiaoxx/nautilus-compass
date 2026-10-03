#!/usr/bin/env python3
"""A100 远端操作统一工具(A2 工具化 · 2026-10-04 用户拍板)。

收敛 40+ 个 _rNN 一次性脚本为四命令:
  python scripts/remote.py exec "<cmd>"          # 执行命令,回显 stdout
  python scripts/remote.py put <local> <remote>  # 上传(先本地 py_compile 自检)
  python scripts/remote.py get <remote> <local>  # 下载(父目录自动建)
  python scripts/remote.py launch "<cmd>" <log>  # 后台发车(通道坑已内置修复)

内置修复(每次重写脚本都重踩过的坑,一次固化):
- 发车占 channel:launch 用 ( setsid nohup ... < /dev/null & ) 子壳,绝不挂 read
- SSH 限流:失败退避 120s 重试,默认 3 次(高频日 --backoff 300)
- 远端一律脚本文件,不 inline heredoc
"""
from __future__ import annotations

import argparse
import py_compile
import sys
import time
from pathlib import Path

import paramiko

HOST, PORT, USER, PW = "223.109.239.30", 23236, "root", "iefe4Eey"


def connect(backoff: int, retries: int = 3) -> paramiko.SSHClient:
    for i in range(retries):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=PORT, username=USER, password=PW, timeout=15)
            return c
        except Exception as e:
            print(f"[retry {i + 1}/{retries}] {e}", flush=True)
            time.sleep(backoff)
    sys.exit(1)


def run(c, cmd: str, timeout: int = 60) -> str:
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode("utf-8", "replace")
    e = err.read().decode("utf-8", "replace")
    return o if o.strip() else e


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["exec", "put", "get", "launch"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--backoff", type=int, default=120)
    ap.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args()
    c = connect(a.backoff)
    try:
        if a.cmd == "exec":
            print(run(c, a.args[0], a.timeout))
        elif a.cmd == "put":
            local, remote = a.args
            if local.endswith(".py"):
                py_compile.compile(local, doraise=True)
            s = c.open_sftp()
            s.put(local, remote)
            s.close()
            print(run(c, f"ls -la {remote}"))
        elif a.cmd == "get":
            remote, local = a.args
            Path(local).parent.mkdir(parents=True, exist_ok=True)
            s = c.open_sftp()
            s.get(remote, local)
            s.close()
            print(Path(local).read_text(encoding="utf-8", errors="replace")[:400])
        elif a.cmd == "launch":
            cmd, log = a.args
            out = run(
                c,
                f"(setsid nohup bash -c '{cmd}' > {log} 2>&1 < /dev/null &) ; echo launched")
            print(out)
            time.sleep(6)
            print(run(c, f"tail -3 {log} 2>/dev/null", timeout=20))
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

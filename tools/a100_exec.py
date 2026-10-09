#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A100 执行通道(paramiko,密码认证走 a100_env,凭据不落仓不打印)。"""
import sys
import time
from pathlib import Path

import paramiko

ENV = Path.home() / ".claude" / ".cache" / "a100_env"


def load_env() -> dict:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def client() -> paramiko.SSHClient:
    env = load_env()
    last = None
    for attempt in range(3):  # R451: A100 banner 间歇断连实测频发,3 次退避重试
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            c.connect(env["A100_HOST"], port=int(env["A100_PORT"]), username=env["A100_USER"],
                      password=env["A100_PW"], timeout=25, banner_timeout=35,
                      auth_timeout=25)
            return c
        except Exception as e:
            last = e
            c.close()
            time.sleep(2 ** attempt)
    raise last


def run(cmd: str, timeout: int = 120) -> tuple:
    c = client()
    try:
        _, out, err = c.exec_command(cmd, timeout=timeout)
        o, e = out.read().decode("utf-8", "replace"), err.read().decode("utf-8", "replace")
        rc = out.channel.recv_exit_status()
        return rc, o, e
    finally:
        c.close()


def put(local: str, remote: str) -> None:
    """base64-over-exec 通道(SFTP 在该机不稳:put size 误报/write Failure)。"""
    import base64
    data = Path(local).read_bytes()
    b64 = base64.b64encode(data).decode()
    rc, o, e = run(f"echo '{b64}' | base64 -d > {remote} && wc -c < {remote}", timeout=120)
    if rc != 0 or not o.strip().isdigit() or int(o.strip()) != len(data):
        raise IOError(f"put_via_b64 mismatch: rc={rc} out={o.strip()[:40]} want={len(data)}")
    print(f"PUT ok {len(data)}B -> {remote}")


if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:])
    rc, o, e = run(cmd, timeout=300)
    print(o)
    if e:
        print("[stderr]", e[:500], file=sys.stderr)
    sys.exit(rc)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A100 执行通道(paramiko,密码认证走 a100_env,凭据不落仓不打印)。"""
import sys
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
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(env["A100_HOST"], port=int(env["A100_PORT"]), username=env["A100_USER"],
              password=env["A100_PW"], timeout=25, banner_timeout=25)
    return c


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
    c = client()
    try:
        s = c.open_sftp()
        s.put(local, remote)
        s.close()
    finally:
        c.close()


if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:])
    rc, o, e = run(cmd, timeout=300)
    print(o)
    if e:
        print("[stderr]", e[:500], file=sys.stderr)
    sys.exit(rc)

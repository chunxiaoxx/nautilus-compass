#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NAS(QNAP TS-532X @192.168.5.25)SSH 执行器——paramiko 密码通道包装。

QTS sshd 拒 pubkey(admin authorized_keys 已装仍 403),密码通道稳定,故包装此 helper。
凭据: ~/.claude/.cache/nas_creds.env(NAS_HOST/NAS_USER/NAS_PASS,0600,永不入仓)。
用法:
  python tools/nas_ssh.py "df -h /share/CACHEDEV1_DATA"     # 单命令
  echo "cmd1; cmd2" | python tools/nas_ssh.py -             # stdin 多命令
"""
import os
import sys

import paramiko

CREDS = os.path.expanduser("~/.claude/.cache/nas_creds.env")


def load_creds() -> dict:
    env = {}
    with open(CREDS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    return env


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "-":
        cmd = sys.stdin.read()
    elif argv:
        cmd = argv[0]
    else:
        print(__doc__)
        return 2
    c = load_creds()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(c["NAS_HOST"], port=22, username=c["NAS_USER"], password=c["NAS_PASS"],
                   timeout=15, allow_agent=False, look_for_keys=False)
    _, out, err = client.exec_command(cmd, timeout=120)
    stdout, stderr = out.read().decode(errors="replace"), err.read().decode(errors="replace")
    print(stdout, end="")
    if stderr.strip():
        print("[stderr]", stderr[:2000], file=sys.stderr)
    rc = out.channel.recv_exit_status()
    client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())

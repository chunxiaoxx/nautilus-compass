#!/usr/bin/env python3
"""A100 隧道前置:生成/复用 SSH key 并打印公钥。在 A100 上运行。"""
import os
import subprocess

key = "/root/.ssh/id_ed25519"
if not os.path.exists(key):
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-f", key, "-q"], check=True)
    print("KEY_GENERATED")
else:
    print("KEY_EXISTS")
with open(key + ".pub") as f:
    print("PUBKEY:", f.read().strip())

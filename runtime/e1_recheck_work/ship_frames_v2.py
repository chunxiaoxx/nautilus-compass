#!/usr/bin/env python3
"""E1 帧包直传 v2:单 SSH 连接循环分块 exec(绕 banner 限流),块 384KB。"""
import base64
import hashlib
import sys
import time
from pathlib import Path

import paramiko

HERE = Path(__file__).parent
REMOTE_DIR = "/root/vdd4/e1_recheck"
HOST, PORT, USER, PW = "223.109.239.30", 23236, "root", "A100_PW_ENV"
TARGETS = {"goldpack_frames.tgz": "634a3f7266942657", "ood_frames.tgz": "2a705d4922e0104f"}
CHUNK = 96 * 1024


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)
    for attempt in range(3):  # 整体限流重试(重连)
        try:
            def run(cmd, t=60):
                _, out, err = c.exec_command(cmd, timeout=t)
                o = out.read().decode("utf-8", "replace")
                return o if o.strip() else err.read().decode("utf-8", "replace")

            print(run(f"mkdir -p {REMOTE_DIR}/parts {REMOTE_DIR}/unpack").strip(), flush=True)
            for fname, sha in TARGETS.items():
                src = HERE / fname
                data = src.read_bytes()
                parts = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
                print(f"{fname}: {len(data)}B -> {len(parts)} chunks", flush=True)
                for i, p in enumerate(parts):
                    b64 = base64.b64encode(p).decode()
                    run(f"echo '{b64}' | base64 -d > {REMOTE_DIR}/parts/{fname}.{i:03d}", t=90)
                    if (i + 1) % 4 == 0:
                        print(f"  {i+1}/{len(parts)}", flush=True)
                run(f"cat {REMOTE_DIR}/parts/{fname}.* > {REMOTE_DIR}/{fname}")
                got = run(f"sha256sum {REMOTE_DIR}/{fname} | cut -c1-16").strip()
                ok = got == sha
                print(f"  merged sha16={got} expect={sha} {'OK' if ok else 'MISMATCH'}", flush=True)
                if not ok:
                    return 1
            print(run(f"cd {REMOTE_DIR}/unpack && tar xzf ../goldpack_frames.tgz && tar xzf ../ood_frames.tgz && "
                      f"echo main_frames=\$(ls mainpack/frames | wc -l) ood_frames=\$(ls judge_pack/frames | wc -l)").strip(), flush=True)
            print("TRANSFER-V2-DONE", flush=True)
            return 0
        except (paramiko.SSHException, ConnectionResetError, EOFError) as e:
            print(f"[conn retry {attempt+1}] {e}", flush=True)
            time.sleep(130)
            try:
                c.close()
            except Exception:
                pass
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)
    return 1


if __name__ == "__main__":
    sys.exit(main())

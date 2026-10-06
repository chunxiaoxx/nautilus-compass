#!/usr/bin/env python3
"""E1 直传 v3:逐块 wc 校验,只补坏块;合并后 sha 复验。"""
import base64
import sys
import time
from pathlib import Path

import paramiko

HERE = Path(__file__).parent
REMOTE_DIR = "/root/vdd4/e1_recheck"
HOST, PORT, USER, PW = "223.109.239.30", 23236, "root", "REDACTED_A100_PW"
TARGETS = {"goldpack_frames.tgz": "634a3f7266942657", "ood_frames.tgz": "2a705d4922e0104f"}
CHUNK = 96 * 1024


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)

    def run(cmd, t=90):
        _, out, err = c.exec_command(cmd, timeout=t)
        o = out.read().decode("utf-8", "replace")
        return o if o.strip() else err.read().decode("utf-8", "replace")

    for fname, sha in TARGETS.items():
        data = (HERE / fname).read_bytes()
        chunks = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
        bad = []
        for i, p in enumerate(chunks):
            remote_p = f"{REMOTE_DIR}/parts/{fname}.{i:03d}"
            sz = run(f"wc -c < {remote_p} 2>/dev/null || echo -1").strip()
            if sz != str(len(p)):
                bad.append(i)
        print(f"{fname}: {len(chunks)} chunks, bad/missing={len(bad)}", flush=True)
        fixed = 0
        for i in bad:
            for att in range(3):
                b64 = base64.b64encode(chunks[i]).decode()
                run(f"echo '{b64}' | base64 -d > {REMOTE_DIR}/parts/{fname}.{i:03d}")
                sz = run(f"wc -c < {REMOTE_DIR}/parts/{fname}.{i:03d}").strip()
                if sz == str(len(chunks[i])):
                    fixed += 1
                    break
                time.sleep(2)
            else:
                print(f"  chunk {i} UNFIXABLE", flush=True)
                return 1
        if bad:
            print(f"  refixed {fixed}/{len(bad)}", flush=True)
        run(f"cat {REMOTE_DIR}/parts/{fname}.* > {REMOTE_DIR}/{fname}")
        got = run(f"sha256sum {REMOTE_DIR}/{fname} | cut -c1-16").strip()
        print(f"  merged {got} vs {sha} {'OK' if got == sha else 'STILL-BAD'}", flush=True)
        if got != sha:
            # 兜底:二分定位坏块(合并 sha 仍坏=有块内容坏但大小对)
            print("  size-ok-but-content-bad: retransmit ALL chunks", flush=True)
            for i, p in enumerate(chunks):
                b64 = base64.b64encode(p).decode()
                run(f"echo '{b64}' | base64 -d > {REMOTE_DIR}/parts/{fname}.{i:03d}")
                if (i + 1) % 20 == 0:
                    print(f"    re-all {i+1}/{len(chunks)}", flush=True)
            run(f"cat {REMOTE_DIR}/parts/{fname}.* > {REMOTE_DIR}/{fname}")
            got = run(f"sha256sum {REMOTE_DIR}/{fname} | cut -c1-16").strip()
            print(f"  re-merged {got} {'OK' if got == sha else 'GIVE-UP'}", flush=True)
            if got != sha:
                return 1
    print(run(f"cd {REMOTE_DIR}/unpack && tar xzf ../goldpack_frames.tgz && tar xzf ../ood_frames.tgz && "
              f"bash -c 'echo main=\$(ls mainpack/frames | wc -l) ood=\$(ls judge_pack/frames | wc -l)'").strip(), flush=True)
    print("TRANSFER-V3-DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

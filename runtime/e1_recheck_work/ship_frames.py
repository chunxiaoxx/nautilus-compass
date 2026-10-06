#!/usr/bin/env python3
"""E1 复考传输:7 块帧包分块上传 A100→合并→sha 校验→解压。带限流退避重试。"""
import hashlib
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
REMOTE_DIR = "/root/vdd4/e1_recheck"
BLOCKS = sorted(HERE.glob("gf.part-*")) + sorted(HERE.glob("od.part-*"))
TARGETS = {"goldpack_frames.tgz": "634a3f7266942657", "ood_frames.tgz": "2a705d4922e0104f"}


def run(cmd: str, timeout=110):
    r = subprocess.run(["python", "scripts/remote.py", "exec", cmd],
                       capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return (r.stdout or "") + (r.stderr or "")


def main() -> int:
    print(run(f"mkdir -p {REMOTE_DIR}/parts {REMOTE_DIR}/unpack"))
    for i, blk in enumerate(BLOCKS):
        target = "goldpack_frames.tgz" if blk.name.startswith("gf") else "ood_frames.tgz"
        remote_part = f"{REMOTE_DIR}/parts/{blk.name}"
        for attempt in range(4):
            r = subprocess.run(["python", "scripts/remote.py", "put", str(blk), remote_part],
                               capture_output=True, text=True, timeout=110, encoding="utf-8", errors="replace")
            out = (r.stdout or "") + (r.stderr or "")
            if "wc -c" in out or "[got]" in out or out.strip():
                # 校验块大小
                chk = run(f"wc -c {remote_part}")
                expect = blk.stat().st_size
                if str(expect) in chk:
                    print(f"[{i+1}/{len(BLOCKS)}] {blk.name} OK ({expect}B)", flush=True)
                    break
            print(f"[{i+1}] retry {attempt+1}: {out[-100:]}", flush=True)
            time.sleep(125)
        else:
            print(f"FAIL {blk.name}", flush=True)
            return 1
    # 合并+校验+解压
    r = run(f"cd {REMOTE_DIR} && cat parts/gf.part-* > goldpack_frames.tgz && cat parts/od.part-* > ood_frames.tgz && "
            f"python3 -c \"import hashlib;\n"
            f"print('gf', hashlib.sha256(open('goldpack_frames.tgz','rb').read()).hexdigest()[:16]);\n"
            f"print('od', hashlib.sha256(open('ood_frames.tgz','rb').read()).hexdigest()[:16])\"")
    print("SHA-CHECK:", r[-200:], flush=True)
    if "634a3f7266942657" not in r or "2a705d4922e0104f" not in r:
        print("SHA MISMATCH", flush=True)
        return 1
    print(run(f"cd {REMOTE_DIR}/unpack && tar xzf ../goldpack_frames.tgz && tar xzf ../ood_frames.tgz && "
              f"ls mainpack/frames | wc -l && ls judge_pack/frames | wc -l")[-200:], flush=True)
    print("TRANSFER-ALL-DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

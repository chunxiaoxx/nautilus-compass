#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate0 判据锁预检——任何出题/判分/打包动作开工前强制调用。

纪律来源:CLAUDE.md「判据原文未取回前不出题」(9月教训,二进宫于10月)——
散文纪律无执行器,本脚本即执行器。判据锁=criteria_lock.json(sha16冻结·LF口径)。

用法:
  python3 ops/ali30q/verify_criteria_lock.py          # 人读输出
  python3 ops/ali30q/verify_criteria_lock.py --json   # 机读输出
退出码: 0=全件匹配可开工 / 1=锁缺失或判据漂移,按纪律拒开工
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

COMPASS_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = Path.home() / "Projects" / "nautilus-core"
LOCK_PATH = COMPASS_ROOT / "runtime" / "pipeline_state" / "criteria_lock.json"


def sha16_lf(p: Path) -> str:
    """sha256 前16位·LF 口径(去 \\r 后哈希·sha锚autocrlf陷阱 10/8 纪律)。"""
    return hashlib.sha256(p.read_bytes().replace(b"\r", b"")).hexdigest()[:16]


def resolve(a: dict) -> Path:
    if a["host"].startswith("~/Projects/nautilus-core"):
        return CORE_ROOT / a["path"].removeprefix("nautilus-core/")
    return COMPASS_ROOT / a["path"]


def main() -> int:
    ap = argparse.ArgumentParser(description="gate0 判据锁预检")
    ap.add_argument("--json", action="store_true", help="输出机读 JSON")
    args = ap.parse_args()

    if not LOCK_PATH.exists():
        msg = "判据锁不存在(runtime/pipeline_state/criteria_lock.json)——判据未锁死不得开工"
        print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False) if args.json else f"FAIL {msg}")
        return 1

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    rows = []
    ok = True
    for a in lock["artifacts"]:
        p = resolve(a)
        if not p.exists():
            ok = False
            rows.append({"path": a["path"], "status": "MISSING", "locked": a["sha16"]})
            continue
        h = sha16_lf(p)
        match = h == a["sha16"]
        ok &= match
        rows.append({
            "path": a["path"],
            "status": "PASS" if match else "DRIFT",
            "sha16": h,
            "locked": a["sha16"],
        })

    if args.json:
        print(json.dumps({"ok": ok, "rows": rows}, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"{r['status']:8} {r['path']}")
        print("GATE0 PASS" if ok else "GATE0 FAIL——判据漂移,拒开工(变更须新版本锁重发,禁放宽)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

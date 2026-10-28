#!/usr/bin/env python3
"""把已转过飞轮的真 verdict 批量落生产 verdict-bus(免鉴权·幂等).

读 flywheel_batch_result.json 的 verdicts → POST {PROD}/api/platform/fde/verdict.
verdict 表免鉴权(ingest_verdict 无 require_platform_key)·verdict_id 幂等→可重跑.
落地后生产 live 看板 /api/platform/rsi-fde/dashboard 的 🔁RSI飞轮卡 + PoI 显示这批.

用法(网络恢复后): PYTHONPATH=. python scripts/post_verdicts_to_prod.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

BATCH = Path(__file__).resolve().parent / "flywheel_batch_result.json"
PROD = os.environ.get("PROD_BASE", "https://nautilus.social")


def main():
    verdicts = json.loads(BATCH.read_text(encoding="utf-8")).get("verdicts") or []
    if not verdicts:
        print("no verdicts in batch result")
        return 1
    url = PROD.rstrip("/") + "/api/platform/fde/verdict"
    ok = fail = 0
    for vb in verdicts:
        data = json.dumps(vb).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.loads(r.read().decode())
            idem = res.get("data", {}).get("idempotent")
            print(f"  ✅ {vb['task_uid']:48s} ok={res.get('success')} idempotent={idem}")
            ok += 1
        except Exception as ex:
            print(f"  ❌ {vb['task_uid']:48s} {str(ex)[:60]}")
            fail += 1
    print(f"\n[prod] {ok} posted / {fail} failed → {url}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

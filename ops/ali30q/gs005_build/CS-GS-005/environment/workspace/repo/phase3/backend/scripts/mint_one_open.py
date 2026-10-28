#!/usr/bin/env python3
"""Mint 一道 open code-fix 题到生产 marketplace · 留 open 不 claim/produce。

≠ flywheel_prod_turn(那个自己 produce 一整圈)。本脚本只走 mint 一步,
把题留在 open 态给消费者(V5)自动 claim→produce→verify→settle。

燃料 = 一个 compass_bench 目录(task_spec.md + buggy_*.py + bench_eval.py)。
desc 内联 starter_inline + verifier_inline(dispatch 不依赖文件)。
dispatch key 从 .env 读(PLATFORM_DISPATCH_KEY)· POST 到 BASE(默认 localhost·cloud 上跑最稳)。

用法:
  PYTHONUTF8=1 python3 mint_one_open.py <fuel_dir> <task_uid> "<title>" [BASE]
  # BASE 默认 http://localhost:8000(在 cloud 上跑);.env 默认同目录或 backend .env
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from pathlib import Path


def load_env_value(key: str, env_paths: list[str]) -> str | None:
    for p in env_paths:
        if not os.path.exists(p):
            continue
        for ln in Path(p).read_text(encoding="utf-8", errors="ignore").splitlines():
            ln = ln.strip()
            if ln.startswith(key + "="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key)


def curl(method: str, url: str, body=None, headers=None):
    cmd = ["curl", "-s", "--max-time", "40", "-X", method, url,
           "-H", "Content-Type: application/json"]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if body is not None:
        cmd += ["--data", json.dumps(body, ensure_ascii=False)]
    for _ in range(3):
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if p.returncode == 0 and p.stdout.strip():
            try:
                return json.loads(p.stdout)
            except json.JSONDecodeError:
                return {"_raw": p.stdout[:200]}
    return {"_error": f"curl failed rc={p.returncode}"}


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__); return 2
    fuel = Path(sys.argv[1])
    uid = sys.argv[2]
    title = sys.argv[3]
    base = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("BASE", "http://localhost:8000")

    spec = (fuel / "task_spec.md").read_text(encoding="utf-8")
    buggy_files = [p for p in glob.glob(str(fuel / "buggy_*.py"))]
    if not buggy_files:
        print(f"no buggy_*.py in {fuel}"); return 1
    buggy = Path(buggy_files[0]).read_text(encoding="utf-8")
    bench = (fuel / "bench_eval.py").read_text(encoding="utf-8")

    desc = json.dumps({
        "fde_class": 3,
        "kind": "code-fix-with-deterministic-verifier",
        "任务概括": spec[:300],
        "starter_inline": buggy,
        "verifier_inline": bench,
    }, ensure_ascii=False)

    pdkey = load_env_value("PLATFORM_DISPATCH_KEY", [
        os.path.expanduser("~/nautilus-mvp/phase3/backend/.env"),
        ".env",
    ])
    if not pdkey:
        print("missing PLATFORM_DISPATCH_KEY"); return 1

    r = curl("POST", f"{base}/api/platform/fde/dispatch",
             {"task_uid": uid, "title": title, "description": desc},
             {"X-Platform-Key": pdkey})
    data = r.get("data") or {}
    st = data.get("status")
    print(f"[mint] {uid} status={st} idempotent={data.get('idempotent')}")
    if st is None:
        print("  mint FAILED:", json.dumps(r, ensure_ascii=False)[:300]); return 1

    # 验证留 open
    r = curl("GET", f"{base}/api/platform/fde/tasks?status=open")
    rows = (r.get("data") or {}).get("tasks", [])
    mine = next((t for t in rows if t["task_uid"] == uid), None)
    print(f"[verify] open tasks={len(rows)} · 本题 status={(mine or {}).get('status')}")
    print(f"[done] 题已 open · 等消费者(V5)自动 claim→produce→verify→settle")
    return 0 if mine else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Mint 一道 SWE 甜点题作 bucket-A 蒸馏燃料进 dispatch(P1.3a·2026-06-20)。

SWE = 纯 RSI substrate(非买方交付·charter §1.3)。题由 instance_id 全描述
(SWE-bench_Lite 数据集·V5 producer + soul verify 都按 id 从数据集加载)。
desc 走 fde_fuel_router.build_fuel_desc(SWE 分支):task_family=distillation_fuel
(V5 W1/W2 claim 键)+ bench_family=repo(W3 peer 记忆键·族级)+ rsi_proof(gate B=N=3 已证)。

fresh-uid 后缀(防 verdict-join 遮蔽)。POST cloud dispatch(PLATFORM_DISPATCH_KEY)。

用法(cloud·~/fde-double-gate 或 backend·带 dispatch key 的 .env):
  python scripts/mint_swe_fuel.py psf__requests-2148 requests \
     --turn1 2 --turn2 6 --n-f2p 10 --model qwen3.7-max --spec "..." [--base http://localhost:8000]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.fde_fuel_router import build_fuel_desc  # noqa: E402


def _dispatch_key() -> str | None:
    for p in (os.path.expanduser("~/nautilus-mvp/phase3/backend/.env"), ".env",
              os.path.expanduser("~/fde-double-gate/.env")):
        if os.path.exists(p):
            for ln in Path(p).read_text(encoding="utf-8", errors="ignore").splitlines():
                if ln.startswith("PLATFORM_DISPATCH_KEY="):
                    return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("PLATFORM_DISPATCH_KEY")


def _curl(method, url, body=None, headers=None):
    cmd = ["curl", "-s", "--max-time", "40", "-X", method, url,
           "-H", "Content-Type: application/json"]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if body is not None:
        cmd += ["--data", json.dumps(body, ensure_ascii=False)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(p.stdout)
    except Exception:  # noqa: BLE001
        return {"_raw": p.stdout[:200], "_rc": p.returncode}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")               # e.g. psf__requests-2148
    ap.add_argument("repo")                       # bench_family 族级·e.g. requests
    ap.add_argument("--swe-repo", default=None)   # e.g. psf/requests(缺省=repo)
    ap.add_argument("--turn1", type=int, required=True)
    ap.add_argument("--turn2", type=int, required=True)
    ap.add_argument("--n-f2p", type=int, required=True)
    ap.add_argument("--model", default="qwen3.7-max")
    ap.add_argument("--proof-source", default="session_20260619 path B N=3")
    ap.add_argument("--spec", default="")         # 简述(prep-file 缺时用)
    ap.add_argument("--prep-file", default=None,  # 契约 B:swe_fuel_prep.py 产的 JSON
                    help="GPU box swe_fuel_prep 产的 {edit_paths,original_files,problem_statement,n_f2p}")
    ap.add_argument("--base", default=os.environ.get("BASE", "http://localhost:8000"))
    a = ap.parse_args()

    prep = {}
    if a.prep_file:
        prep = json.loads(Path(a.prep_file).read_text(encoding="utf-8"))

    candidate = {
        "task_uid": a.instance_id, "track": "swe",
        "bench_family": a.repo, "swe_instance_id": a.instance_id,
        "swe_repo": a.swe_repo or a.instance_id.replace("__", "/", 1),
        "title": f"SWE-RSI 燃料 {a.instance_id}",
        "spec": prep.get("problem_statement") or a.spec
        or f"SWE-bench_Lite 实例 {a.instance_id}",
        "rsi_proof": {"turn1": a.turn1, "turn2": a.turn2,
                      "n_f2p": prep.get("n_f2p", a.n_f2p),
                      "model": a.model, "source": a.proof_source,
                      "rsi_improved": a.turn2 > a.turn1},
    }
    # 契约 B:内嵌 buggy 原文 + edit_paths(V5 daemon 零依赖出 diff)
    if prep.get("original_files"):
        candidate["edit_paths"] = prep.get("edit_paths")
        candidate["original_files"] = prep["original_files"]
    desc = build_fuel_desc(candidate)
    j = json.loads(desc)
    assert j["task_family"] == "distillation_fuel" and j["bench_family"] == a.repo

    pdkey = _dispatch_key()
    if not pdkey:
        print("missing PLATFORM_DISPATCH_KEY"); return 1

    fresh = "%s_fuel_%d" % (a.instance_id, int(time.time()))  # fresh-uid 防遮蔽
    r = _curl("POST", f"{a.base}/api/platform/fde/dispatch",
              {"task_uid": fresh, "title": candidate["title"], "description": desc},
              {"X-Platform-Key": pdkey})
    st = (r.get("data") or {}).get("status")
    print(f"[mint-swe] {fresh} status={st} family={j['task_family']} bench={j['bench_family']} "
          f"rsi={j['rsi_proof']['turn1']}->{j['rsi_proof']['turn2']} "
          f"original_files={len(j.get('original_files') or {})} edit_paths={j.get('edit_paths')}")
    if st is None:
        print("  FAILED:", json.dumps(r, ensure_ascii=False)[:300]); return 1

    # 验证落 open + 带 family
    chk = _curl("GET", f"{a.base}/api/platform/fde/tasks?status=open")
    rows = (chk.get("data") or {}).get("tasks", [])
    mine = next((t for t in rows if t["task_uid"] == fresh), None)
    has_family = mine and "distillation_fuel" in (mine.get("description") or "")
    print(f"[verify] open={len(rows)} 本题在={'Y' if mine else 'N'} 带family={'Y' if has_family else 'N'}")
    return 0 if has_family else 1


if __name__ == "__main__":
    sys.exit(main())

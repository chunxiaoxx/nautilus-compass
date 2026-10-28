#!/usr/bin/env python3
"""生产飞轮一圈 · 真 marketplace lifecycle(mint→claim→produce→verify→settle).

≠ 本地 in-process demo:这次 dispatch/claim/report/verdict 全打 **生产 nautilus.social**,
任务在真 /tasks 生命周期上走一遍。HTTP 走 curl(避 urllib SSL 抖动)。全新 task_uid
(避 verdict-join 遮蔽)。produce=deepseek-v4-pro 真解·verify=compass bench_eval 确定性门。

用法: PDKEY=<dispatch key> PYTHONUTF8=1 PYTHONPATH=. python scripts/flywheel_prod_turn.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from services.fde_bench_runner import make_verify_fn

BASE = "https://nautilus.social"
FUEL = Path(os.path.expanduser("~/fde_t3_scratch/compass_bench/c2d_utf8_byte_truncation"))
SECRETS = Path(os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env"))
TASK_UID = os.environ.get("TASK_UID", "compass_exp_c2d_prod_lifecycle_20260616")
AGENT = "platform-prod-turn"
PRODUCE_MODEL = "deepseek-v4-pro"


def curl(method, path, body=None, headers=None):
    cmd = ["curl", "-s", "--max-time", "40", "-X", method, f"{BASE}{path}",
           "-H", "Content-Type: application/json"]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if body is not None:
        cmd += ["--data", json.dumps(body)]
    for attempt in range(3):
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if p.returncode == 0 and p.stdout.strip():
            try:
                return json.loads(p.stdout)
            except json.JSONDecodeError:
                return {"_raw": p.stdout[:200]}
    return {"_error": f"curl failed after retries: rc={p.returncode}"}


def load_secrets():
    env = {}
    for ln in SECRETS.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1); env[k] = v
    return env


def produce(spec, buggy, env):
    key = env.get("BAILIAN_API_KEY")
    base = env.get("BAILIAN_OPENAI_BASE")
    prompt = ("你是代码修复专家。修复下面有 bug 的 Python 命令行脚本,只输出修复后的完整脚本"
              "(纯代码·保持 stdin/stdout 协议·无解释无围栏)。\n\n## 规格\n" + spec + "\n\n## 待修复\n" + buggy)
    body = {"model": PRODUCE_MODEL, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0, "max_tokens": 4000}
    cmd = ["curl", "-s", "--max-time", "120", "-X", "POST", base.rstrip("/") + "/chat/completions",
           "-H", "Authorization: Bearer " + (key or ""), "-H", "Content-Type: application/json",
           "--data", json.dumps(body)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(p.stdout)["choices"][0]["message"]["content"]


def main():
    pdkey = os.environ.get("PDKEY")
    if not pdkey:
        print("missing PDKEY env"); return 1
    env = load_secrets()
    spec = (FUEL / "task_spec.md").read_text(encoding="utf-8")
    buggy = (FUEL / "buggy_truncate.py").read_text(encoding="utf-8")
    bench = (FUEL / "bench_eval.py").read_text(encoding="utf-8")
    desc = json.dumps({"fde_class": 3, "kind": "code-fix-with-deterministic-verifier",
                       "任务概括": spec[:300], "starter_inline": buggy, "verifier_inline": bench},
                      ensure_ascii=False)

    # 1. mint(需 dispatch key)
    r = curl("POST", "/api/platform/fde/dispatch",
             {"task_uid": TASK_UID, "title": "C2d 生产lifecycle(compass燃料)", "description": desc},
             {"X-Platform-Key": pdkey})
    st = (r.get("data") or {}).get("status")
    print(f"[1 mint]    {TASK_UID} status={st} idempotent={(r.get('data') or {}).get('idempotent')}")
    if st is None:
        print("  mint failed:", json.dumps(r, ensure_ascii=False)[:200]); return 1

    # 2. claim(我立即认领·防自动消费者抢去做错口径)
    r = curl("POST", "/api/platform/fde/claim", {"task_uid": TASK_UID, "agent_id": AGENT})
    print(f"[2 claim]   status={(r.get('data') or {}).get('status')} by={AGENT}")

    # 3. produce(真模型)
    print(f"[3 produce] {PRODUCE_MODEL} solving…")
    sol = produce(spec, buggy, env)
    r = curl("POST", "/api/platform/fde/report",
             {"task_uid": TASK_UID, "agent_id": AGENT, "output": {"code": sol, "produced_by": PRODUCE_MODEL}})
    print(f"[3 produce] {len(sol)} chars · report status={(r.get('data') or {}).get('status')}")

    if os.environ.get("SKIP_VERIFY"):
        print("[skip] SKIP_VERIFY set · 留 produced 态给 fde-bench timer 自动验")
        return 0

    # 4. verify(确定性 bench_eval)→ 5. verdict
    verify_fn = make_verify_fn()
    task = {"task_uid": TASK_UID, "description": desc, "output": {"code": sol}}
    res = verify_fn(task)
    print(f"[4 verify]  reward={res.get('reward')} passed={res.get('passed')} ok={res.get('ok')} ({res.get('n_pass')}/{res.get('n_total')})")
    from services.fde_bench_poll import build_bench_verdict_body
    vbody = build_bench_verdict_body(task, res)
    r = curl("POST", "/api/platform/fde/verdict", vbody)
    print(f"[5 verdict] {vbody['verdict_id']} → ok={r.get('success')} source={vbody['source']}")

    # 6. 验证 settled(独立 GET 生产 /tasks)
    r = curl("GET", "/api/platform/fde/tasks")
    row = next((t for t in r.get("data", {}).get("tasks", []) if t["task_uid"] == TASK_UID), None)
    v = (row or {}).get("verdict")
    print(f"[6 verify]  生产 /tasks: status={(row or {}).get('status')} verdict={json.dumps(v, ensure_ascii=False) if v else None}")

    ok = row and row.get("status") == "settled" and v and v.get("source") == "compass/bench_eval"
    print(f"\n{'✅ 生产飞轮完整一圈(真 marketplace lifecycle·确定性 verify)' if ok else '❌ 未闭环'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

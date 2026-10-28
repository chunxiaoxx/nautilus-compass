#!/usr/bin/env python3
"""端到端飞轮 demo · 真燃料 c2d 转一圈(mint→claim→produce→verify→settle).

证 RSI 飞轮闭环的平台 wiring 全活·全真数据:
  1. mint   : compass 燃料 c2d(内联 bench_eval + 起点 + spec)→ POST /dispatch (open)
  2. claim  : consumer agent 认领 (open → claimed)
  3. produce: 真模型(百炼 deepseek-v4-pro)读 buggy + spec → 产出修复代码 (claimed → produced)
  4. verify : fde_bench_poll + fde_bench_runner.make_verify_fn → compass bench_eval
              确定性门(非 LLM judge)→ reward 1.0/0.0
  5. settle : verdict source=compass/bench_eval → /tasks 视为 settled → PoI eligible

跑真 endpoint 代码(api.fde_dispatch + api.fde_verdict·in-process sqlite)+ 真子进程
bench_eval + 真模型 produce. 输出 evidence + flywheel_demo_result.json(喂可见看板).

用法: PYTHONUTF8=1 python -m scripts.flywheel_demo_c2d
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register relationship target
from models.fde_dispatch import FdeDispatch  # noqa: F401
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from api.fde_dispatch import router as dispatch_router
from api.fde_verdict import router as verdict_router
from services.fde_bench_poll import poll_and_verify
from services.fde_bench_runner import make_verify_fn

FUEL_DIR = Path(os.path.expanduser("~/fde_t3_scratch/compass_bench/c2d_utf8_byte_truncation"))
SECRETS = Path(os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env"))
TASK_UID = "compass_exp_c2d_utf8_byte_truncation_001"
PRODUCE_MODEL = os.environ.get("PRODUCE_MODEL", "deepseek-v4-pro")


def _load_secrets():
    env = {}
    if SECRETS.exists():
        for ln in SECRETS.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                env[k] = v
    return env


def produce_with_model(spec: str, buggy: str, env: dict) -> str:
    """真模型 produce: 读 buggy + spec → 修复后的完整脚本(consumer 角色)."""
    key = env.get("BAILIAN_API_KEY")
    base = env.get("BAILIAN_OPENAI_BASE", "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
    prompt = (
        "你是代码修复专家。下面是一个有 bug 的 Python 命令行脚本和它的规格说明。"
        "脚本从 stdin 读取(第1行=字节预算 N,其后每行一个值),把每个值按规格处理后逐行写 stdout。"
        "请修复 bug,只输出修复后的【完整 Python 脚本】(纯代码,保持 stdin/stdout 协议不变,不要任何解释或 markdown 围栏)。\n\n"
        f"## 规格说明\n{spec}\n\n## 待修复脚本\n{buggy}"
    )
    body = json.dumps({
        "model": PRODUCE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 4000,
    }).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body, headers={
        "Authorization": "Bearer " + (key or ""), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read().decode())
    return j["choices"][0]["message"]["content"]


def main():
    env = _load_secrets()
    spec = (FUEL_DIR / "task_spec.md").read_text(encoding="utf-8")
    buggy = (FUEL_DIR / "buggy_truncate.py").read_text(encoding="utf-8")
    bench_eval = (FUEL_DIR / "bench_eval.py").read_text(encoding="utf-8")

    # ── dispatch description = 自包含打包 JSON(consumer 解出即可做题·settle 解出即可验) ──
    description = json.dumps({
        "fde_class": 3,
        "kind": "code-fix-with-deterministic-verifier",
        "任务概括": spec[:400],
        "starter_inline": buggy,
        "verifier_inline": bench_eval,
        "reward_signal": "passed:true => reward 1.0",
    }, ensure_ascii=False)

    # ── in-process app: 真 endpoint 代码 + sqlite ──
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(dispatch_router)
    app.include_router(verdict_router)
    app.dependency_overrides[get_db] = override_get_db
    c = TestClient(app)
    ev = {"task_uid": TASK_UID, "stages": {}}

    # 1. mint
    r = c.post("/api/platform/fde/dispatch", json={
        "task_uid": TASK_UID, "title": "C2d · UTF-8 字节安全截断(compass 燃料)", "description": description})
    assert r.status_code == 200, r.text
    ev["stages"]["1_mint"] = {"status": r.json()["data"]["status"]}
    print(f"[1/5 mint]    task={TASK_UID} status={r.json()['data']['status']}")

    # 2. claim
    agent = "bailian-deepseek-consumer"
    r = c.post("/api/platform/fde/claim", json={"task_uid": TASK_UID, "agent_id": agent})
    assert r.status_code == 200, r.text
    ev["stages"]["2_claim"] = {"claimed_by": agent, "status": r.json()["data"]["status"]}
    print(f"[2/5 claim]   agent={agent} status={r.json()['data']['status']}")

    # 3. produce (真模型)
    print(f"[3/5 produce] calling {PRODUCE_MODEL} (consumer solve)…")
    raw_solution = produce_with_model(spec, buggy, env)
    r = c.post("/api/platform/fde/report", json={
        "task_uid": TASK_UID, "agent_id": agent, "output": {"code": raw_solution, "produced_by": PRODUCE_MODEL}})
    assert r.status_code == 200, r.text
    ev["stages"]["3_produce"] = {"produced_by": PRODUCE_MODEL, "status": r.json()["data"]["status"],
                                 "solution_chars": len(raw_solution)}
    print(f"[3/5 produce] {PRODUCE_MODEL} produced {len(raw_solution)} chars · status={r.json()['data']['status']}")

    # 4+5. verify (确定性 bench_eval) → verdict (source=compass/bench_eval) → settled
    class _Src:
        def list_produced_tasks(self):
            body = c.get("/api/platform/fde/tasks", params={"status": "produced"}).json()
            return body["data"]["tasks"]

    captured = {}

    def verdict_fn(vbody):
        captured["body"] = vbody
        rr = c.post("/api/platform/fde/verdict", json=vbody)
        assert rr.status_code == 200, rr.text
        return rr.json()["data"]

    verify_fn = make_verify_fn()
    result = poll_and_verify(_Src(), verify_fn, verdict_fn)
    ev["stages"]["4_verify_5_settle"] = result
    ev["verdict_body"] = captured.get("body")
    print(f"[4-5 verify]  poll → verified={result['verified']} errored={result['errored']} failed={result['failed']}")

    # 验证 settled + verdict
    tasks = c.get("/api/platform/fde/tasks").json()["data"]["tasks"]
    row = next(t for t in tasks if t["task_uid"] == TASK_UID)
    verdict = row.get("verdict")
    ev["final"] = {"effective_status": row["status"], "verdict": verdict}
    print(f"[final]       status={row['status']} verdict={json.dumps(verdict, ensure_ascii=False)}")

    # ── 可选: 把这道真 verdict 落生产 verdict-bus(免鉴权)→ live 看板可见 ──
    if os.environ.get("POST_PROD") == "1" and captured.get("body"):
        prod = os.environ.get("PROD_BASE", "https://nautilus.social")
        url = prod.rstrip("/") + "/api/platform/fde/verdict"
        data = json.dumps(captured["body"]).encode()
        rq = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(rq, timeout=30) as rr:
                pres = json.loads(rr.read().decode())
            ev["prod_post"] = {"verdict_id": captured["body"]["verdict_id"],
                               "idempotent": pres.get("data", {}).get("idempotent"), "ok": pres.get("success")}
            print(f"[prod] POST verdict {captured['body']['verdict_id']} → live verdict-bus ok={pres.get('success')}")
        except Exception as ex:
            ev["prod_post"] = {"verdict_id": captured["body"]["verdict_id"], "ok": False, "error": str(ex)[:120]}
            print(f"[prod] POST failed (fail-soft): {str(ex)[:120]} · verdict_body saved to result json for curl")

    out_path = Path(__file__).resolve().parent / "flywheel_demo_result.json"
    out_path.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[evidence] {out_path}")

    ok = (verdict is not None and row["status"] == "settled" and verdict["source"] == "compass/bench_eval")
    print(f"\n{'✅ 飞轮转完整一圈(确定性 verify·source=compass/bench_eval)' if ok else '❌ 未闭环'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

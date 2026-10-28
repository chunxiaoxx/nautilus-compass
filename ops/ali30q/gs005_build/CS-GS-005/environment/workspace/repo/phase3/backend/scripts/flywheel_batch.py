#!/usr/bin/env python3
"""批量飞轮 · compass 全燃料集转多圈(mint→claim→produce→确定性verify→settle).

把 ~/fde_t3_scratch/compass_bench/ 全部 code-fix 燃料(c2/c2b/c2c/c2d/c3/d1/f1/f2)
依次过飞轮:真模型(deepseek-v4-pro)produce → compass bench_eval 机器判 reward →
verdict source=compass/bench_eval → settled. 显示真实 pass/fail 分布(棘轮也需 0 信号).

跑真 endpoint 代码(in-process sqlite)+ 真子进程 bench_eval + 真模型 produce.
输出 flywheel_batch_result.json(喂 render_flywheel_snapshot 的可见看板).

用法: PYTHONUTF8=1 PYTHONPATH=. python scripts/flywheel_batch.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from glob import glob
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401
from models.fde_dispatch import FdeDispatch  # noqa: F401
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from api.fde_dispatch import router as dispatch_router
from api.fde_verdict import router as verdict_router
from services.fde_bench_poll import poll_and_verify
from services.fde_bench_runner import make_verify_fn

FUEL_ROOT = Path(os.path.expanduser("~/fde_t3_scratch/compass_bench"))
SECRETS = Path(os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env"))
PRODUCE_MODEL = os.environ.get("PRODUCE_MODEL", "deepseek-v4-pro")
AGENT = "bailian-deepseek-consumer"


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
    key = env.get("BAILIAN_API_KEY")
    base = env.get("BAILIAN_OPENAI_BASE", "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
    prompt = (
        "你是代码修复专家。下面是一个有 bug 的 Python 命令行脚本和它的规格说明。"
        "请修复 bug,只输出修复后的【完整 Python 脚本】(纯代码,保持 stdin/stdout 协议不变,不要解释或 markdown 围栏)。\n\n"
        f"## 规格说明\n{spec}\n\n## 待修复脚本\n{buggy}"
    )
    body = json.dumps({"model": PRODUCE_MODEL, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.0, "max_tokens": 4000}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body, headers={
        "Authorization": "Bearer " + (key or ""), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        j = json.loads(r.read().decode())
    return j["choices"][0]["message"]["content"]


def _make_app():
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
    return TestClient(app)


def main():
    env = _load_secrets()
    c = _make_app()
    verify_fn = make_verify_fn()
    fuel_dirs = sorted(d for d in FUEL_ROOT.iterdir() if d.is_dir())
    rows = []

    for fdir in fuel_dirs:
        buggy_files = glob(str(fdir / "buggy_*.py"))
        bench = fdir / "bench_eval.py"
        spec_f = fdir / "task_spec.md"
        if not buggy_files or not bench.exists() or not spec_f.exists():
            continue
        name = fdir.name
        uid = f"compass_exp_{name}_001"
        buggy = Path(buggy_files[0]).read_text(encoding="utf-8")
        spec = spec_f.read_text(encoding="utf-8")
        bench_src = bench.read_text(encoding="utf-8")
        description = json.dumps({
            "fde_class": 3, "kind": "code-fix-with-deterministic-verifier",
            "任务概括": spec[:300], "starter_inline": buggy, "verifier_inline": bench_src,
        }, ensure_ascii=False)

        c.post("/api/platform/fde/dispatch", json={"task_uid": uid, "title": name, "description": description})
        c.post("/api/platform/fde/claim", json={"task_uid": uid, "agent_id": AGENT})
        try:
            sol = produce_with_model(spec, buggy, env)
        except Exception as ex:
            print(f"  {name:32s} produce FAILED: {str(ex)[:60]}")
            continue
        c.post("/api/platform/fde/report", json={"task_uid": uid, "agent_id": AGENT,
                                                 "output": {"code": sol, "produced_by": PRODUCE_MODEL}})
        print(f"  {name:32s} produced {len(sol)} chars · verifying…")

    captured = []

    def verdict_fn(vbody):
        captured.append(vbody)
        c.post("/api/platform/fde/verdict", json=vbody)
        return {"verdict_id": vbody["verdict_id"]}

    class _Src:
        def list_produced_tasks(self):
            return c.get("/api/platform/fde/tasks", params={"status": "produced"}).json()["data"]["tasks"]

    result = poll_and_verify(_Src(), verify_fn, verdict_fn)

    # 汇总
    tasks = c.get("/api/platform/fde/tasks").json()["data"]["tasks"]
    passed = sum(1 for t in tasks if (t.get("verdict") or {}).get("overall_pass"))
    print(f"\n[batch] {len(captured)} 题确定性判定 · {passed} 过 / {len(captured)} (真实 pass/fail 分布)")
    for vb in captured:
        mark = "✅ 1.0" if vb["overall_pass"] else "⬜ 0.0"
        print(f"   {mark}  {vb['task_uid']}")

    out = Path(__file__).resolve().parent / "flywheel_batch_result.json"
    out.write_text(json.dumps({"verdicts": captured, "poll": result,
                               "passed": passed, "total": len(captured)},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[evidence] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

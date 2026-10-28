"""T6 分布近邻定律检验:L2-ext(外部陌生矿的 diff 注入增益)· 预注册 2026-09-08。

假设(T6,理论总账):组织记忆注入增益与知识到模型训练分布的距离成正比;
自家矿(模型分布近邻)注入无增益(L2 已证 B=C<A)。预测:**外部陌生仓(click)
的 winning_diff 注入有增益:B>A 且 B>C**。

预注册判据(冻结,跑前写定):
- Step1 攒池:click 矿前 10 题(文件序)单臂 A 跑,PASS 的 winning_diff 入池
- Step2 三臂:第 11-16 题×{A 无注入 / B 池内最高分注入 / C 池内随机不同文件}
- 主门:B 首轮通过 > A 且 > C;次门:token 均值
- 停机:池 <3 → 报"外部矿可解性"降级结论;总停机 2026-09-15
- 判分:首轮(turns[0].test_passed),同模型 chunxiao_k3 单臂

环境:外部 src 布局仓,两处 pytest 入口(runner._default_run_test 与
ex._find_red_test)patch 为 PYTHONPATH=<worktree>/src 注入版——否则 pytest
import site-packages 安装版,GREEN 与 patch 无关(9/8 click/requests 双实测)。
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import g2_b1_agentic_runner as runner  # noqa: E402
import g2_b1_executor_agent as ex  # noqa: E402
from g2_b1_l2_memory_experiment import (  # noqa: E402
    build_injection, score_memory, sign_test_p,
)

BACKEND = TOOLS.parent
EXT_DIR = BACKEND / "docs/evidence/g2b1_t6_20260908"
QUEUE = BACKEND / "docs/evidence/g2b1_ext_mine_20260908/click.jsonl"
REPO = Path("C:/Users/chunx/ext_mine")
PROVIDER = os.environ.get("T6_PROVIDER", "chunxiao_k3")
POOL_N, HOLDOUT_N = 10, 6
PLACEBO_SEED = 4242


def _patch_pytest_paths() -> None:
    """Both pytest entrypoints get PYTHONPATH=<tree>/src (external src layout)."""
    def _env(cwd: Path) -> dict:
        return {**os.environ, "PYTHONPATH": str(cwd / "src")}

    def _run_test(test_id: str, cwd: Path):
        conf = "tests"
        for i, part in enumerate(Path(test_id.split("::")[0]).parts):
            if part == "tests" and i > 0:
                conf = str(Path(*Path(test_id.split("::")[0]).parts[:i]))
                break
        return subprocess.run(
            ["python", "-m", "pytest", test_id, "-q", f"--confcutdir={conf}"],
            cwd=cwd, env=_env(cwd), capture_output=True, timeout=600)

    import re as _re

    def _find_red_test(backend: Path, test_file: str):
        parts = Path(test_file.replace("\\", "/")).parts
        conf = "tests"
        for i, part in enumerate(parts):
            if part == "tests" and i > 0:
                conf = str(Path(*parts[:i]))
                break
        run = subprocess.run(
            ["python", "-m", "pytest", test_file, "-q", f"--confcutdir={conf}"],
            cwd=backend, env=_env(backend), capture_output=True, timeout=900)
        out = run.stdout.decode("utf-8", "replace")
        if run.returncode == 0 or "no tests ran" in out:
            return None
        m = _re.search(r"FAILED (\S+?::\w+)", out)
        if m:
            return m.group(1)
        m = _re.search(r"ERROR (\S+?\.py)", out)
        return m.group(1) if m else None

    runner._default_run_test = _run_test
    ex._find_red_test = _find_red_test


def _load_queue() -> list[dict]:
    return [json.loads(l) for l in
            QUEUE.read_text(encoding="utf-8").splitlines() if l.strip()]


def _first_pass(ev: dict) -> bool | None:
    turns = ev.get("turns") or []
    return bool(turns[0].get("test_passed")) if turns else None


def _arm_injector(mem: dict | None):
    orig = runner.build_prompt

    def wrapped(test_id, red_tail, source_rel, source_text, feedback):
        base = orig(test_id, red_tail, source_rel, source_text, feedback)
        return (build_injection(mem) + base) if mem else base

    return wrapped if mem else orig


def _run_task_retry(repo, task, completer, tag, tries: int = 3):
    """k3 网关偶发 5xx(9/8 一日两次):退避重试,幂等 evidence 兜底。"""
    for attempt in range(1, tries + 1):
        try:
            return ex.run_task(repo, task, completer, tag, EXT_DIR)
        except Exception as exc:
            print(f"  [retry {attempt}/{tries}] {exc}", flush=True)
            if attempt < tries:
                time.sleep(90)
    return None


def main() -> int:
    queue = _load_queue()
    completer = ex.make_completer(PROVIDER)
    _patch_pytest_paths()

    # ---- Step1: build the PASS pool (arm A only, idempotent evidence) ----
    print(f"provider={PROVIDER} (full-chain single model; pool+arms)", flush=True)
    for i, task in enumerate(queue[:POOL_N], 1):
        ev = _run_task_retry(REPO, task, completer, f"t6pool-{PROVIDER}")
        if ev is None:
            print(f"[pool {i}/{POOL_N}] skipped after retries", flush=True)
            continue
        print(f"[pool {i}/{POOL_N}] passed={ev.get('test_passed')} "
              f"skip={ev.get('skipped_reason')} "
              f"tokens={ev.get('total_tokens')}", flush=True)
    pool = []
    for f in EXT_DIR.glob(f"g2b1-exec-*-t6pool-{PROVIDER}.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("test_passed") and d.get("winning_diff") and d.get("task"):
            t = d["task"]
            pool.append({"source_rel": d.get("source_rel"),
                         "reference_fix_commit": t["reference_fix_commit"],
                         "winning_diff": d["winning_diff"],
                         "task": t})
    print(f"pool size: {len(pool)}", flush=True)
    if len(pool) < 3:
        print("STOP (preregistered): pool<3 -> downgrade to external-mining "
              "solvability report", flush=True)
        return 0

    # ---- Step2: three arms on fresh tasks (preregistered slice) ----
    rng = random.Random(PLACEBO_SEED)
    rows = []
    for task in queue[POOL_N:POOL_N + HOLDOUT_N]:
        mem_b, best = None, -1
        for m in pool:
            if m["reference_fix_commit"] == task["reference_fix_commit"]:
                continue
            s = score_memory(task, m)
            if s > best:
                mem_b, best = m, s
        others = [m for m in pool
                  if m["source_rel"] != (mem_b["source_rel"] if mem_b else None)]
        mem_c = rng.choice(others) if others else None
        rows.append((task, mem_b, mem_c))
        print(f"[pick] {task['subject'][:50]} B={mem_b['source_rel'] if mem_b else None} "
              f"score={best} C={'ok' if mem_c else 'NONE'}", flush=True)

    results = {a: [] for a in "ABC"}
    for i, (task, mem_b, mem_c) in enumerate(rows, 1):
        for arm, mem in (("A", None), ("B", mem_b), ("C", mem_c)):
            runner.build_prompt = _arm_injector(mem)
            ev = _run_task_retry(REPO, task, completer, f"t6{arm}-{PROVIDER}")
            if ev is None:
                print(f"[{i}/{len(rows)}] {arm} ERROR after retries", flush=True)
                continue
            fp = _first_pass(ev)
            results[arm].append(fp)
            print(f"[{i}/{len(rows)}] {arm} first_pass={fp} "
                  f"tokens={ev.get('total_tokens')}", flush=True)

    # ---- report (preregistered gates) ----
    print("=== T6 L2-ext 读数(首轮判据)===", flush=True)
    for arm in "ABC":
        vals = [v for v in results[arm] if v is not None]
        print(f"  {arm}: first_pass={sum(vals)}/{len(vals)}", flush=True)
    b = sum(1 for v in results["B"] if v)
    a = sum(1 for v in results["A"] if v)
    c = sum(1 for v in results["C"] if v)
    print(f"主门:B({b})>A({a}) 且 B({b})>C({c}) -> "
          f"{'PASS: 外部矿注入有增益,T6 获支持' if b > a and b > c else 'FAIL/方向读数'}",
          flush=True)
    print("对照(自家矿 L2):A 5/8 B 3/8 C 3/8(B=C<A)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

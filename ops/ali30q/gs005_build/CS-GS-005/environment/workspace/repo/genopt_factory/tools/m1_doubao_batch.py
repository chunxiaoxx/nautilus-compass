"""M1 · 10 题 JobShop doubao 难倒测试批量驱动(Task 0.1 · 本机 ARK)。

每题三步,任一步不过就跳过该题(防烧错料):
  1. 再生 data/instances(fetch_orlib_jssp.py · 用题内 .orlib_jobshop1.txt 缓存 + metrics.json 的 per_instance 名单)
  2. pre-flight:baseline 得分 == 该题 v7 轨迹 seed_score(容差 0.01)
  3. doubao 5 轮:gpt55_local_runner --rounds 5 --model doubao-seed-2-0-pro-260215

产出:<task>/gpt55_trajectory_doubao_5r_<date>.json(完整解 · 可复现契约)。
pass@5 判读在批后汇总(难倒口径 = buyer §2 ②)。

Usage: python m1_doubao_batch.py [--tasks t1 t2 ...] [--skip-produce]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JOBSHOP = os.path.normpath(os.path.join(
    HERE, "..", "tasks", "operations_research_and_decision_science", "JobShop"))

DEFAULT_TASKS = [
    "JobShop_ft06_v2_v1_001", "JobShop_ft10_v2_v1_001", "JobShop_la01_v2_v1_001",
    "JobShop_la16_v2_v1_001", "JobShop_la21_v2_v1_001",
    "JobShop_orlib_instance_pack_a_v1_001", "JobShop_orlib_instance_pack_b_v1_001",
    "JobShop_orlib_instance_pack_c_v1_001", "JobShop_orlib_instance_pack_d_v1_001",
    "JobShop_orlib_instance_pack_e_v1_001",
]
MODEL = "doubao-seed-2-0-pro-260215"


def instances_of(task_dir: str) -> list[str]:
    m = json.load(open(os.path.join(task_dir, "metrics.json"), encoding="utf-8"))
    return [e["instance"] for e in m["per_instance"]]


def v7_seed(task_dir: str):
    for name in ("gpt55_trajectory_h800_v7.json", "gpt55_trajectory.json"):
        p = os.path.join(task_dir, name)
        if os.path.isfile(p):
            t = json.load(open(p, encoding="utf-8"))
            return t.get("seed_score", t.get("start_score"))
    return None


def regen_data(task_dir: str, names: list[str]) -> bool:
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "fetch_orlib_jssp.py"),
         "--out", "data", "--names", *names],
        capture_output=True, text=True, cwd=task_dir, timeout=300)
    ok = r.returncode == 0 and os.path.isdir(os.path.join(task_dir, "data", "instances"))
    if not ok:
        print(f"  [data] FAIL: {r.stderr[-200:]}", flush=True)
    return ok


def preflight(task_dir: str, want) -> bool:
    sys.path.insert(0, HERE)
    from gpt55_local_runner import run_eval  # noqa: E402
    baseline = open(os.path.join(task_dir, "baseline", "init.py"), encoding="utf-8").read()
    m = run_eval(task_dir, baseline)
    got = m.get("combined_score")
    print(f"  [preflight] baseline={got} v7seed={want}", flush=True)
    if want is None:
        return bool(m.get("valid"))
    return got is not None and abs(float(got) - float(want)) <= 0.01


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="*", default=DEFAULT_TASKS)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--out-suffix", default="doubao_5r_20260707")
    args = ap.parse_args()

    results = {}
    for t in args.tasks:
        td = os.path.join(JOBSHOP, t)
        print(f"=== [{t}]", flush=True)
        if not os.path.isdir(td):
            results[t] = "NO_DIR"
            continue
        out = os.path.join(td, f"gpt55_trajectory_{args.out_suffix}.json")
        if os.path.isfile(out):
            print("  [skip] trajectory exists", flush=True)
            results[t] = "EXISTS"
            continue
        try:
            names = instances_of(td)
        except Exception as e:  # noqa: BLE001
            print(f"  [metrics] FAIL {e}", flush=True)
            results[t] = "NO_METRICS"
            continue
        if not os.path.isdir(os.path.join(td, "data", "instances")):
            if not regen_data(td, names):
                results[t] = "DATA_FAIL"
                continue
        if not preflight(td, v7_seed(td)):
            results[t] = "PREFLIGHT_DIFF"
            continue
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "gpt55_local_runner.py"),
             "--task-dir", td, "--rounds", str(args.rounds),
             "--model", MODEL, "--out", out],
            timeout=7200)
        results[t] = "DONE" if r.returncode == 0 else f"RUN_EXIT_{r.returncode}"
        print(f"  [{t}] {results[t]}", flush=True)

    print("=== SUMMARY ===", flush=True)
    for t, s in results.items():
        line = f"{t}: {s}"
        out = os.path.join(JOBSHOP, t, f"gpt55_trajectory_{args.out_suffix}.json")
        if os.path.isfile(out):
            d = json.load(open(out, encoding="utf-8"))
            valid_rounds = sum(1 for r in d.get("rounds", [])
                               if (r.get("metrics") or {}).get("valid", 0))
            line += (f"  seed={d.get('seed_score')} best={d.get('best_score')} "
                     f"gap={d.get('gap_closed')} valid_rounds={valid_rounds}/{d.get('n')}")
        print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

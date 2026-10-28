"""2D path-planning verifier (per buyer §5: continuous, valid gate, deterministic)."""

import argparse
import json
import os
import subprocess
import sys
import tempfile


PER_INSTANCE_TIMEOUT_S = 60


def _run(candidate_path, instance_path, python_exe, timeout_s):
    # Run in cwd so result.json is recoverable after the subprocess exits
    # (no race with tempfile.TemporaryDirectory cleanup on Windows).
    out_path = os.path.join(os.getcwd(), "result.json")
    if os.path.exists(out_path):
        try: os.remove(out_path)
        except OSError: pass
    try:
        proc = subprocess.run(
            [python_exe, os.path.join(os.path.dirname(__file__) or ".", "_run_one.py"),
             "--candidate", candidate_path, "--instance", instance_path],
            capture_output=True, text=True, timeout=timeout_s, cwd=os.getcwd(),
        )
    except subprocess.TimeoutExpired:
        return {"error": f"hard timeout after {timeout_s}s"}, -1
    if not os.path.exists(out_path):
        return {"error": (proc.stderr or proc.stdout)[-500:]}, proc.returncode
    with open(out_path, encoding="utf-8") as f:
        return json.load(f), proc.returncode


def _validate_path(path, instance):
    h, w = instance["height"], instance["width"]
    grid = instance["grid"]
    start = instance["start"]
    goal = instance["goal"]
    start_list = list(start) if not isinstance(start, list) else start
    goal_list = list(goal) if not isinstance(goal, list) else goal
    if not path:
        return False, "empty path"
    if path[0] != start_list:
        return False, f"path start {path[0]} != instance start {start_list}"
    if path[-1] != goal_list:
        return False, f"path end {path[-1]} != instance goal {goal_list}"
    for i, (r, c) in enumerate(path):
        if r < 0 or r >= h or c < 0 or c >= w:
            return False, f"step {i} out of bounds"
        is_start = (r, c) == tuple(start_list)
        is_goal = (r, c) == tuple(goal_list)
        if grid[r][c] == 1 and not is_start and not is_goal:
            return False, f"step {i} on obstacle"
        if i > 0:
            pr, pc = path[i - 1]
            if abs(r - pr) + abs(c - pc) != 1:
                return False, f"step {i} not 4-connected to step {i-1}"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", required=True)
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args()
    benchmark_dir = os.path.abspath(args.benchmark_dir)
    candidate = os.path.abspath(args.candidate)
    python_exe = sys.executable

    inst_dir = os.path.join(benchmark_dir, "data", "instances")
    opt_path = os.path.join(benchmark_dir, "data", "optima.json")
    optima = {}
    if os.path.isfile(opt_path):
        with open(opt_path, encoding="utf-8") as f:
            optima = json.load(f)
    instances = sorted(f for f in os.listdir(inst_dir) if f.endswith(".json"))

    per_instance = []
    for fname in instances:
        ipath = os.path.join(inst_dir, fname)
        with open(ipath, encoding="utf-8") as f:
            inst = json.load(f)
        # Prefer optima.json; fall back to instance.opt_cost baked in.
        opt = optima.get(fname[:-5], 0) or inst.get("opt_cost", 0)
        if opt < 0:
            opt = 0
        result, rc = _run(candidate, ipath, python_exe, PER_INSTANCE_TIMEOUT_S + 10)
        if "error" in result:
            per_instance.append({"instance": fname[:-5], "feasible": False,
                                 "reason": result["error"], "score": 0.0,
                                 "cost": 0, "opt_cost": opt})
            continue
        path = result.get("path", [])
        cost = int(result.get("cost", 0))
        ok, why = _validate_path(path, inst)
        if not ok:
            per_instance.append({"instance": fname[:-5], "feasible": False,
                                 "reason": why, "score": 0.0,
                                 "cost": cost, "opt_cost": opt})
            continue
        if opt <= 0:
            score = 100.0
        else:
            score = max(0.0, min(100.0, 100.0 * opt / max(cost, 1)))
        per_instance.append({
            "instance": fname[:-5], "feasible": True,
            "reason": "ok", "score": round(score, 4),
            "cost": cost, "opt_cost": opt,
        })

    failures = sum(1 for p in per_instance if not p["feasible"])
    valid = 0 if failures > 0 else 1
    combined = round(sum(p["score"] for p in per_instance) / max(1, len(per_instance)), 4) \
        if valid else 0.0

    metrics = {
        "combined_score": combined,
        "valid": valid,
        "instances": len(per_instance),
        "failures": failures,
        "per_instance": per_instance,
    }
    out_path = os.path.join(os.getcwd(), "metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=1, ensure_ascii=False)
    print(f"metrics -> {out_path}")
    print(json.dumps(metrics, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
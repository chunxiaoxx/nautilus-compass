"""Bin-packing verifier (per buyer §5: continuous score, validity gate).

Scoring (per instance):
  opt = ceil(sum_sizes)  (lower bound, tight for uniform)
  FF  = number of bins used by First-Fit (items in given order) — computed inline
  score = max(0, 100 * (1 - (you - opt) / max(1, FF - opt)))
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile


PER_INSTANCE_TIMEOUT_S = 60


def _ff_bins(items, cap=1.0):
    remain = []
    for sz in items:
        for b in range(len(remain)):
            if remain[b] >= sz - 1e-9:
                remain[b] -= sz
                break
        else:
            remain.append(cap - sz)
    return len(remain)


def _run(candidate_path, instance_path, python_exe, timeout_s):
    with tempfile.TemporaryDirectory() as td:
        proc = subprocess.run(
            [python_exe, os.path.join(os.path.dirname(__file__) or ".", "_run_one.py"),
             "--candidate", candidate_path, "--instance", instance_path],
            capture_output=True, text=True, timeout=timeout_s, cwd=td,
        )
        out_path = os.path.join(td, "result.json")
        if os.path.exists(out_path):
            with open(out_path, encoding="utf-8") as f:
                return json.load(f), proc.returncode
        return {"error": (proc.stderr or proc.stdout)[-500:]}, proc.returncode


def _check_feasible(items, assignment, num_bins, cap=1.0):
    if len(assignment) != len(items):
        return False, "assignment length != items length"
    if num_bins <= 0:
        return False, "num_bins must be > 0"
    for a in assignment:
        if a < 0 or a >= num_bins:
            return False, f"assignment {a} out of range"
    bin_loads = [0.0] * num_bins
    for sz, b in zip(items, assignment):
        bin_loads[b] += sz
    for b, load in enumerate(bin_loads):
        if load > cap + 1e-6:
            return False, f"bin {b} overloaded: {load:.4f} > {cap}"
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
        items = inst["items"]
        cap = inst.get("bin_capacity", 1.0)
        opt = optima.get(fname[:-5]) or max(math.ceil(sum(items)), 1)
        ff_bins = _ff_bins(items, cap)

        result, rc = _run(candidate, ipath, python_exe, PER_INSTANCE_TIMEOUT_S + 10)
        if "error" in result:
            per_instance.append({"instance": fname[:-5], "feasible": False,
                                 "reason": result["error"], "score": 0.0,
                                 "num_bins": 0, "opt": opt, "ff_bins": ff_bins})
            continue
        nb = int(result.get("num_bins", 0))
        assignment = result.get("assignment", [])
        feasible, why = _check_feasible(items, assignment, nb, cap)
        if not feasible:
            per_instance.append({"instance": fname[:-5], "feasible": False,
                                 "reason": why, "score": 0.0,
                                 "num_bins": nb, "opt": opt, "ff_bins": ff_bins})
            continue
        gap = max(1, ff_bins - opt)
        score = max(0.0, min(100.0, 100.0 * (1 - (nb - opt) / gap)))
        per_instance.append({
            "instance": fname[:-5], "feasible": True,
            "reason": "ok", "score": round(score, 4),
            "num_bins": nb, "opt": opt, "ff_bins": ff_bins,
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
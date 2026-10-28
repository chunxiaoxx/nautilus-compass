"""Cache verifier (per buyer §5: continuous score, validity gate)."""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile


PER_INSTANCE_TIMEOUT_S = 30


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


def _fifo_miss_count(instance_path, baseline_path, python_exe):
    """Run the explicit FIFO baseline init.py to get its miss count as the divisor.

    Caller MUST pass the real baseline path, not a candidate path. The H800 harness
    overwrites benchmark_dir/baseline/init.py with each round's candidate, so deriving
    from benchmark_dir will silently re-run the candidate.
    """
    with tempfile.TemporaryDirectory() as td:
        proc = subprocess.run(
            [python_exe, os.path.join(os.path.dirname(__file__) or ".", "_run_one.py"),
             "--candidate", baseline_path, "--instance", instance_path],
            capture_output=True, text=True, timeout=PER_INSTANCE_TIMEOUT_S + 10, cwd=td,
        )
        out_path = os.path.join(td, "result.json")
        if os.path.exists(out_path):
            with open(out_path, encoding="utf-8") as f:
                return json.load(f).get("misses")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--baseline", default=None,
                    help="Path to the FIFO baseline init.py. If omitted, derive from "
                         "<benchmark-dir>/baseline/init.py. (The H800 harness "
                         "replaces baseline/init.py with the candidate per round, "
                         "so ALWAYS pass an explicit --baseline path to score "
                         "against the real FIFO divisor — otherwise fifo_misses "
                         "== candidate_misses and the score is 0.)")
    args = ap.parse_args()
    benchmark_dir = os.path.abspath(args.benchmark_dir)
    candidate = os.path.abspath(args.candidate)
    if args.baseline:
        baseline_path = os.path.abspath(args.baseline)
    else:
        baseline_path = os.path.join(benchmark_dir, "baseline", "init.py")
    python_exe = sys.executable

    inst_dir = os.path.join(benchmark_dir, "data", "instances")
    instances = sorted(f for f in os.listdir(inst_dir) if f.endswith(".json"))

    # Pre-compute FIFO miss count per instance.
    fifo_misses = {}
    for fname in instances:
        ipath = os.path.join(inst_dir, fname)
        fifo_misses[fname] = _fifo_miss_count(ipath, baseline_path, python_exe)

    per_instance = []
    for fname in instances:
        ipath = os.path.join(inst_dir, fname)
        result, rc = _run(candidate, ipath, python_exe, PER_INSTANCE_TIMEOUT_S + 10)
        if "error" in result:
            per_instance.append({"instance": fname[:-5], "feasible": False,
                                 "reason": result["error"], "score": 0.0,
                                 "misses": 0})
            continue
        misses = int(result.get("misses", 0))
        fifo = fifo_misses.get(fname) or 1
        # score: 100 * (1 - miss_you / miss_FIFO), clipped 0..100
        score = max(0.0, min(100.0, 100.0 * (1.0 - misses / max(fifo, 1))))
        per_instance.append({
            "instance": fname[:-5], "feasible": True,
            "reason": "ok", "score": round(score, 4),
            "misses": misses, "fifo_misses": fifo,
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
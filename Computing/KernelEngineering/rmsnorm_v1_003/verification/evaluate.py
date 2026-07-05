"""Honest timed verifier for RMSNorm (read-only).

Imports `rmsnorm` from `baseline/init.py` under numpy-import-lock, runs on
data/instances.json, compares against reference/reference.py naive 3-pass.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "reference"))
from _core import import_lock_no_numpy, max_abs_diff_2d, gflops_rmsnorm  # noqa: E402
import reference as ref_mod  # noqa: E402

TARGET_GFLOPS = 0.500
TOL_MAX_ABS = 1e-3


def load_instance(inst):
    random.seed(inst["seed"])
    N = inst["N"]
    D = inst["D"]
    eps = inst["eps"]
    weight = [random.uniform(0.5, 1.5) for _ in range(D)]
    x = [[random.uniform(-2.0, 2.0) for _ in range(D)] for _ in range(N)]
    return x, weight, eps


def evaluate_instance(instance, candidate_path):
    x, weight, eps = load_instance(instance)

    inserted_path = str(Path(candidate_path).resolve().parent)
    sys.path.insert(0, inserted_path)
    try:
        mod = import_lock_no_numpy(str(candidate_path), "candidate")
    finally:
        if sys.path and sys.path[0] == inserted_path:
            sys.path.pop(0)

    C_ref = ref_mod.rmsnorm_naive(x, weight, eps=eps)

    N = len(x)
    D = len(weight)

    try:
        best = None
        best_output = None
        for _ in range(3):
            res = mod.rmsnorm(x, weight, eps=eps)
            elapsed = res["elapsed_s"]
            if best is None or elapsed < best:
                best = elapsed
                best_output = res["output"]
        elapsed_s = best

        achieved = gflops_rmsnorm(N, D, elapsed_s)
        diff = max_abs_diff_2d(best_output, C_ref)
        numerical_ok = diff <= TOL_MAX_ABS
        score = min(100.0, 100.0 * max(achieved, 1e-9) / TARGET_GFLOPS) if numerical_ok else 0.0
        return {
            "instance_id": instance["instance_id"],
            "valid": 1 if numerical_ok else 0,
            "achieved_gflops": float(achieved),
            "elapsed_s": float(elapsed_s),
            "max_abs_diff": float(diff),
            "score": float(score),
        }
    except Exception as e:
        return {
            "instance_id": instance["instance_id"],
            "valid": 0,
            "achieved_gflops": None,
            "score": 0.0,
            "error": f"{type(e).__name__}: {str(e)[:200]}",
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--instances", default=str(Path(__file__).parent.parent / "data" / "instances.json"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.instances, "r", encoding="utf-8") as f:
        instances = json.load(f)

    per_instance = [evaluate_instance(i, args.candidate) for i in instances]
    valid_flags = [r["valid"] for r in per_instance]
    scores = [r["score"] for r in per_instance]
    combined = float(sum(scores) / len(scores)) if all(valid_flags) and scores else 0.0
    valid = 1 if all(valid_flags) else 0

    metrics = {
        "task_id": "rmsnorm_v1_003",
        "domain": "Computing and Quantum Information",
        "sub_domain": "KernelEngineering",
        "valid": valid,
        "combined_score": combined,
        "per_instance": per_instance,
        "n_instances": len(instances),
        "baseline_failures": sum(1 for f in valid_flags if f == 0),
        "target_gflops_oracle": TARGET_GFLOPS,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"valid={valid} combined_score={combined:.4f} instances={len(instances)}")
    for r in per_instance:
        print(
            f"  {r['instance_id']}: valid={r['valid']} "
            f"gflops={r.get('achieved_gflops')} score={r.get('score', 0.0):.4f}"
        )


if __name__ == "__main__":
    main()

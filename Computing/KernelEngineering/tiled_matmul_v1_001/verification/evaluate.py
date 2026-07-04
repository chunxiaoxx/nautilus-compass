"""Honest timed verifier for tiled matrix multiplication.

Imports `matmul` from `baseline/init.py` under numpy-import-lock, runs on
data/instances.json, compares against reference/reference.py naive matmul.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "reference"))
from _core import import_lock_no_numpy, max_abs_diff, gflops  # noqa: E402
import reference as ref_mod  # noqa: E402

TARGET_GFLOPS = 1.500  # oracle convergence bound for this hardware
TOL_MAX_ABS = 1e-3  # tolerance for numerical equivalence


def load_instance(inst):
    """Build deterministic A, B for an instance config."""
    import random
    M = inst["M"]
    K = inst["K"]
    N = inst["N"]
    seed = inst["seed"]
    rnd = random.Random(seed)
    A = [[rnd.uniform(-1.0, 1.0) for _ in range(K)] for _ in range(M)]
    B = [[rnd.uniform(-1.0, 1.0) for _ in range(N)] for _ in range(K)]
    return A, B


def evaluate_instance(instance, candidate_path):
    A, B = load_instance(instance)

    # Import candidate under no-numpy lock
    inserted_path = str(Path(candidate_path).resolve().parent)
    sys.path.insert(0, inserted_path)
    try:
        mod = import_lock_no_numpy(str(candidate_path), "candidate")
    finally:
        if sys.path and sys.path[0] == inserted_path:
            sys.path.pop(0)

    # Reference solution
    C_ref = ref_mod.naive_matmul(A, B)

    try:
        # Warm-up + 3 timed runs; keep best
        best = None
        for _ in range(3):
            res = mod.matmul(A, B)
            elapsed = res["elapsed_s"]
            if best is None or elapsed < best:
                best = elapsed
                C = res["C"]
        elapsed_s = best

        M = len(A)
        K = len(A[0])
        N = len(B[0])
        achieved = gflops(M, K, N, elapsed_s)
        diff = max_abs_diff(C, C_ref)
        numerical_ok = diff <= TOL_MAX_ABS
        score = min(100.0, 100.0 * max(achieved, 1e-9) / TARGET_GFLOPS)
        return {
            "instance_id": instance["instance_id"],
            "valid": 1 if numerical_ok else 0,
            "achieved_gflops": float(achieved),
            "elapsed_s": float(elapsed_s),
            "max_abs_diff": float(diff),
            "score": float(score) if numerical_ok else 0.0,
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
        "task_id": "tiled_matmul_v1_001",
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

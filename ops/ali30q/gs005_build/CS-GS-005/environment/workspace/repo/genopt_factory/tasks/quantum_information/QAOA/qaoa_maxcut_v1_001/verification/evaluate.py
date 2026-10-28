"""QAOA Max-Cut verifier (per buyer §5: continuous, valid gate, deterministic)."""

import argparse
import json
import os
import subprocess
import sys
import tempfile


PER_INSTANCE_TIMEOUT_S = 60


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
    with open(opt_path, encoding="utf-8") as f:
        optima = json.load(f)
    instances = sorted(f for f in os.listdir(inst_dir) if f.endswith(".json"))

    per_instance = []
    for fname in instances:
        ipath = os.path.join(inst_dir, fname)
        with open(ipath, encoding="utf-8") as f:
            inst = json.load(f)
        n = inst["n"]
        opt = optima.get(fname[:-5]) or inst.get("opt_cut") or 1
        result, rc = _run(candidate, ipath, python_exe, PER_INSTANCE_TIMEOUT_S + 10)
        if "error" in result:
            per_instance.append({"instance": fname[:-5], "feasible": False,
                                 "reason": result["error"], "score": 0.0,
                                 "cut_size": 0, "opt_cut": opt})
            continue
        bs = result.get("bitstring", [])
        cut = int(result.get("cut_size", 0))
        # Validate bitstring shape
        if len(bs) != n or any(b not in (0, 1) for b in bs):
            per_instance.append({"instance": fname[:-5], "feasible": False,
                                 "reason": f"bitstring shape wrong: len={len(bs)} != n={n}",
                                 "score": 0.0, "cut_size": cut, "opt_cut": opt})
            continue
        score = max(0.0, min(100.0, 100.0 * cut / max(opt, 1)))
        per_instance.append({
            "instance": fname[:-5], "feasible": True,
            "reason": "ok", "score": round(score, 4),
            "cut_size": cut, "opt_cut": opt,
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
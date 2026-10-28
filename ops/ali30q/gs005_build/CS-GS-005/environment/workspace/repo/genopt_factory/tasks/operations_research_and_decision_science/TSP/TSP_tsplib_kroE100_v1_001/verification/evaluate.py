"""TSP verifier (per buyer §5: continuous score, validity gate, deterministic)."""

import argparse
import json
import math
import multiprocessing as mp
import os
import sys
import tempfile
import time
import traceback


PER_INSTANCE_TIMEOUT_S = 120


def _tour_length(tour, coords):
    total = 0.0
    n = len(tour)
    for i in range(n):
        a = coords[tour[i]]
        b = coords[tour[(i + 1) % n]]
        total += math.hypot(a[0] - b[0], a[1] - b[1])
    return total


def _check_feasible(tour, dimension):
    if len(tour) != dimension:
        return False, f"tour length {len(tour)} != dimension {dimension}"
    if set(tour) != set(range(dimension)):
        return False, "tour is not a permutation of [0..dimension-1]"
    return True, "ok"


def _score_instance(instance, optimum):
    """Worker target. Imports candidate and runs it. Returns metrics dict or error."""
    # `instance` here is (name, coords, optimum) tuple (picklable).
    name, coords, optimum = instance
    dimension = len(coords)
    out = {
        "instance": name,
        "feasible": False,
        "reason": "",
        "tour_length": None,
        "optimum": optimum,
        "score": 0.0,
        "elapsed_s": 0.0,
    }
    try:
        # candidate module is at known path passed via sys.argv
        sys.path.insert(0, os.path.dirname(sys.argv[1]))
        import importlib.util
        spec = importlib.util.spec_from_file_location("candidate", sys.argv[1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        t0 = time.monotonic()
        result = mod.solve_instance({
            "name": name,
            "dimension": dimension,
            "node_coords": coords,
        })
        elapsed = time.monotonic() - t0
        out["elapsed_s"] = round(elapsed, 3)
        if elapsed > PER_INSTANCE_TIMEOUT_S:
            out["reason"] = f"timeout ({elapsed:.1f}s > {PER_INSTANCE_TIMEOUT_S}s)"
            return out
        tour = result["tour"]
        feasible, why = _check_feasible(tour, dimension)
        if not feasible:
            out["reason"] = why
            return out
        length = _tour_length(tour, coords)
        out["feasible"] = True
        out["tour_length"] = round(length, 4)
        out["score"] = round(min(100.0, 100.0 * optimum / length), 4)
        out["reason"] = "ok"
        return out
    except Exception:
        out["reason"] = "exception: " + traceback.format_exc(limit=2)
        return out


def _worker_entry(instance, q):
    try:
        q.put(_score_instance(instance, optimum=instance[2]))
    except Exception as exc:
        q.put({"instance": instance[0], "feasible": False,
               "reason": f"worker exception: {exc}", "score": 0.0})


def _run_with_timeout(instance, candidate_path, timeout_s):
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_worker_entry, args=(instance, q))
    p.start()
    p.join(timeout_s)
    if p.is_alive():
        p.terminate()
        p.join(5)
        return {
            "instance": instance[0],
            "feasible": False,
            "reason": f"hard timeout after {timeout_s}s",
            "score": 0.0,
            "tour_length": None,
            "optimum": instance[2],
            "elapsed_s": timeout_s,
        }
    if not q.empty():
        return q.get_nowait()
    return {
        "instance": instance[0],
        "feasible": False,
        "reason": "worker died with no result",
        "score": 0.0,
        "tour_length": None,
        "optimum": instance[2],
        "elapsed_s": 0.0,
    }


def _load_instances(benchmark_dir):
    inst_dir = os.path.join(benchmark_dir, "data", "instances")
    opt_path = os.path.join(benchmark_dir, "data", "optima.json")
    with open(opt_path, encoding="utf-8") as f:
        optima = json.load(f)
    instances = []
    for fname in sorted(os.listdir(inst_dir)):
        if not fname.endswith(".json"):
            continue
        name = fname[:-5]
        with open(os.path.join(inst_dir, fname), encoding="utf-8") as f:
            d = json.load(f)
        coords = d["node_coords"]
        opt = optima.get(name)
        if opt is None:
            print(f"  WARNING: {name} has no optimum in optima.json — skipping",
                  file=sys.stderr)
            continue
        instances.append((name, coords, float(opt)))
    return instances


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", required=True)
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args()

    benchmark_dir = os.path.abspath(args.benchmark_dir)
    candidate = os.path.abspath(args.candidate)
    if not os.path.isfile(candidate):
        print(f"candidate not found: {candidate}", file=sys.stderr)
        sys.exit(1)

    instances = _load_instances(benchmark_dir)
    if not instances:
        print("no instances loaded", file=sys.stderr)
        sys.exit(1)

    # sys.argv[1] is consumed inside the worker; set it before any fork.
    sys.argv = [sys.argv[0], candidate]

    per_instance = []
    for instance in instances:
        m = _run_with_timeout(instance, candidate, PER_INSTANCE_TIMEOUT_S + 5)
        per_instance.append(m)
        print(f"  {m['instance']}: feasible={m['feasible']} "
              f"length={m.get('tour_length')} score={m['score']:.2f} "
              f"reason={m['reason']!r}", flush=True)

    failures = sum(1 for m in per_instance if not m["feasible"])
    valid = 0 if failures > 0 else 1
    combined_score = round(sum(m["score"] for m in per_instance) / len(per_instance), 4) \
        if valid else 0.0

    summary = {
        "combined_score": combined_score,
        "valid": valid,
        "instances": len(per_instance),
        "failures": failures,
        "per_instance": per_instance,
    }

    # Write to CWD (controllable by caller via subprocess.run(cwd=...)).
    out_path = os.path.join(os.getcwd(), "metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f"metrics -> {out_path}")


if __name__ == "__main__":
    main()
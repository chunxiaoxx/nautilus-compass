"""Verifier for the JobShop generative-optimization task.

Read-only, deterministic. Scores a candidate solver on every instance in
data/instances/. Per instance:

    score_i = min(100.0, 100.0 * optimum_i / makespan_i)

Feasibility gating: any infeasible / crashed / timed-out instance sets
valid = 0 and combined_score = 0 for the whole submission.

Usage:
    python verification/evaluate.py --benchmark-dir <task_root> --candidate <solver.py>

Writes metrics.json into the current working directory.
"""

import argparse
import json
import multiprocessing
import os
import sys
import time

PER_INSTANCE_TIMEOUT_S = 60


def _run_candidate(candidate_path, instance, queue):
    """Executed in a child process: import candidate, solve one instance."""
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("candidate_solver", candidate_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.solve_instance(instance)
        queue.put({"ok": True, "result": result})
    except Exception as exc:  # noqa: BLE001 - report any candidate failure
        queue.put({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def check_feasible(instance, starts):
    """Return (feasible: bool, makespan: int|None, reason: str)."""
    num_jobs = instance["num_jobs"]
    num_machines = instance["num_machines"]
    jobs = instance["jobs"]

    if not isinstance(starts, list) or len(starts) != num_jobs:
        return False, None, "starts must be a list with one entry per job"

    machine_intervals = [[] for _ in range(num_machines)]
    makespan = 0
    for j in range(num_jobs):
        ops = jobs[j]
        job_starts = starts[j]
        if not isinstance(job_starts, list) or len(job_starts) != len(ops):
            return False, None, f"job {j}: wrong number of start times"
        prev_end = 0
        for k, ((machine_id, duration), s) in enumerate(zip(ops, job_starts)):
            if not isinstance(s, int) or isinstance(s, bool):
                return False, None, f"job {j} op {k}: start time must be int"
            if s < 0:
                return False, None, f"job {j} op {k}: negative start time"
            if s < prev_end:
                return False, None, f"job {j} op {k}: violates job precedence"
            end = s + duration
            prev_end = end
            machine_intervals[machine_id].append((s, end, j, k))
            makespan = max(makespan, end)

    for m, intervals in enumerate(machine_intervals):
        intervals.sort()
        for (s1, e1, j1, k1), (s2, e2, j2, k2) in zip(intervals, intervals[1:]):
            if s2 < e1:
                return False, None, (
                    f"machine {m}: overlap between job {j1} op {k1} "
                    f"and job {j2} op {k2}"
                )

    return True, makespan, "ok"


def score_instance(optimum, makespan):
    if optimum is None or makespan is None or makespan <= 0:
        return None
    return min(100.0, 100.0 * float(optimum) / float(makespan))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()

    bench = os.path.abspath(args.benchmark_dir)
    candidate = os.path.abspath(args.candidate)
    inst_dir = os.path.join(bench, "data", "instances")
    with open(os.path.join(bench, "data", "optima.json"), encoding="utf-8") as f:
        optima = json.load(f)

    instance_files = sorted(
        fn for fn in os.listdir(inst_dir) if fn.endswith(".json")
    )
    per_instance = []
    failures = 0

    for fn in instance_files:
        with open(os.path.join(inst_dir, fn), encoding="utf-8") as f:
            instance = json.load(f)
        name = instance["name"]

        queue = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=_run_candidate, args=(candidate, instance, queue)
        )
        t0 = time.monotonic()
        proc.start()
        proc.join(PER_INSTANCE_TIMEOUT_S)
        elapsed = time.monotonic() - t0

        entry = {"instance": name, "elapsed_s": round(elapsed, 2)}
        if proc.is_alive():
            proc.terminate()
            proc.join()
            entry.update(feasible=False, reason="timeout", makespan=None, score=None)
            failures += 1
        else:
            payload = queue.get() if not queue.empty() else {
                "ok": False,
                "error": "candidate produced no result",
            }
            if not payload.get("ok"):
                entry.update(
                    feasible=False,
                    reason=payload.get("error", "unknown error"),
                    makespan=None,
                    score=None,
                )
                failures += 1
            else:
                starts = (payload["result"] or {}).get("starts")
                feasible, makespan, reason = check_feasible(instance, starts)
                score = score_instance(optima.get(name), makespan) if feasible else None
                entry.update(
                    feasible=feasible,
                    reason=reason,
                    makespan=makespan,
                    optimum=optima.get(name),
                    score=score,
                )
                if not feasible:
                    failures += 1
        per_instance.append(entry)

    instances = len(per_instance)
    valid = 1.0 if instances > 0 and failures == 0 else 0.0
    scores = [e["score"] for e in per_instance if e.get("score") is not None]
    mean_score = sum(scores) / len(scores) if scores else 0.0
    combined = mean_score if valid > 0.0 else 0.0

    metrics = {
        "combined_score": round(combined, 4),
        "valid": valid,
        "instances": instances,
        "failures": failures,
        "per_instance": per_instance,
    }
    with open("metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()

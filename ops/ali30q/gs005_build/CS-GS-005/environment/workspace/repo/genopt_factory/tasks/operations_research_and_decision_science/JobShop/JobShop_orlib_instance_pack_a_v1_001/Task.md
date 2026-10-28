# Job-Shop Scheduling: Minimize Makespan on Classic OR-Library Instances

## Problem Background

You are given a set of classic Job-Shop Scheduling Problem (JSSP) instances from the
OR-Library (Fisher & Thompson 1963, Lawrence 1984). Each instance consists of `n` jobs
and `m` machines. Every job is an ordered sequence of exactly `m` operations; each
operation must run on a specific machine for a fixed (integer) duration. Constraints:

1. **Precedence**: operations of a job must execute in their given order — operation
   `k+1` of a job may only start after operation `k` of the same job has finished.
2. **Capacity**: a machine processes at most one operation at a time (no overlap).
3. **No preemption**: once started, an operation runs to completion.

Your goal is to produce, for every instance, a feasible schedule that **minimizes the
makespan** (the completion time of the last operation).

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def solve_instance(instance: dict) -> dict:
    """
    instance = {
      "name":         str,              # e.g. "ft06"
      "num_jobs":     int,
      "num_machines": int,
      "jobs": [                         # one list per job, in operation order
          [[machine_id, duration], ...],   # machine_id in [0, num_machines-1]
          ...
      ]
    }
    returns = {
      "starts": [                       # one list per job, same order as input
          [start_time_op0, start_time_op1, ...],   # int start times
          ...
      ]
    }
    """
```

The current implementation is a naive sequential dispatcher — it is feasible but far
from optimal. Improve it (priority dispatching rules, Giffler-Thompson, local search,
simulated annealing, shifting bottleneck, ... your choice).

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no third-party imports in `baseline/init.py`.
- Deterministic output: if you use randomness, seed it with a fixed constant so that
  two consecutive runs produce identical schedules.
- Preserve the `solve_instance` signature and return-dict fields exactly.
- Per-instance time budget: **60 seconds** on the evaluation machine. Exceeding it
  marks that instance infeasible.
- Do not read, modify, or monkey-patch anything under `verification/`, `data/`, or
  `frontier_eval/`.

## How Your Score Is Computed (and how to check it yourself)

Run from the task root:

```bash
python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py
```

This prints a JSON summary and writes `metrics.json`. Per instance:

```
score_i = min(100.0, 100.0 * optimum_i / makespan_i)      # 100 ⇔ proven optimum reached
```

- Any infeasible/errored/timeout instance sets `valid = 0` and `combined_score = 0`
  for the whole submission ("infeasible high scores" count as 0).
- Otherwise `combined_score = mean(score_i)` over all instances in `data/instances/`.

The baseline currently scores ≈ 25 on the bundled instance set (all instances
feasible). The known optima are stored in `data/optima.json`; reaching them on every
instance gives 100. A strong classical heuristic portfolio reaches ≈ 90.

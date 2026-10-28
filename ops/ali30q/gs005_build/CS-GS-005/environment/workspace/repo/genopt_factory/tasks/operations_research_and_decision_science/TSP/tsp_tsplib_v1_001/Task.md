# Traveling Salesman Problem: Minimize Tour Length on TSPLIB Symmetric Instances

## Problem Background

You are given classic symmetric Traveling Salesman Problem (TSP) instances from the
TSPLIB benchmark library (Reinelt 1991). Each instance defines `n` cities with 2-D
Euclidean coordinates. The goal is to produce a **Hamiltonian cycle** (a tour visiting
every city exactly once and returning to the start) that minimizes total Euclidean tour
length.

Constraints:
1. **Visit each city exactly once** (no repeats, no skips).
2. **Return to start** (cycle, not path).
3. **Tour length** = sum of Euclidean distances along edges.

Your goal is to produce, for every instance, a feasible tour with **minimum total
length**. The TSPLIB instances ship with **known optimal tour lengths** in
`data/optima.json`, so the verifier computes a clean `(optimum / your_length)` ratio.

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def solve_instance(instance: dict) -> dict:
    """
    instance = {
      "name":     str,            # e.g. "ts225"
      "dimension": int,           # number of cities
      "node_coords": [(x_i, y_i), ...]   # i in [0, dimension-1]
    }
    returns = {
      "tour": [int, ...]         # permutation of [0..dimension-1], length == dimension
    }
    """
```

The current implementation is a naive **nearest-neighbor heuristic** — it is feasible
but far from optimal. Improve it (2-opt, 3-opt, Lin-Kernighan, simulated annealing,
Christofides, ... your choice).

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no third-party imports in `baseline/init.py`.
- Deterministic output: if you use randomness, seed it with a fixed constant so that
  two consecutive runs produce identical tours.
- Preserve the `solve_instance` signature and return-dict fields exactly.
- Per-instance time budget: **120 seconds** on the evaluation machine. Exceeding it
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
score_i = min(100.0, 100.0 * optimum_i / your_length_i)      # 100 ⇔ proven optimum reached
```

- Any infeasible/errored/timeout instance sets `valid = 0` and `combined_score = 0`
  for the whole submission ("infeasible high scores" count as 0).
- Otherwise `combined_score = mean(score_i)` over all instances in `data/instances/`.

The baseline currently scores ≈ 89.5 on the bundled instance set (all instances
feasible, weak single-start NN). The known optima are stored in `data/optima.json`;
reaching them on every instance gives 100. A strong multi-restart 2-opt heuristic
reaches ≈ 99.8 — leaving GPT5.5 a real gap to close over 3 rounds.
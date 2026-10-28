# 2D Grid Path Planning · Minimize Path Cost on Synthetic Grids

## Problem Background

You are given classic **2D grid path planning**: a grid world with empty cells
and obstacles, start and goal cells, and a 4-connected movement model (up/down/
left/right) with unit cost per move. The goal is to find a path from start to
goal that **minimizes total movement cost**.

Algorithms in scope:
- **BFS** (breadth-first search, unit edge cost) — finds any shortest path
- **Dijkstra** (with weighted edges) — finds lowest-cost shortest path
- **A*** (BFS + heuristic) — finds optimal path with admissible heuristic
- **Jump Point Search (JPS)** (Harabor & Grastien 2011) — A* with symmetry
  pruning, dramatically faster on uniform-cost grids

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def find_path(instance: dict) -> dict:
    """
    instance = {
      "name":     str,            # e.g. "open20"
      "height":   int,            # grid rows
      "width":    int,            # grid cols
      "grid":     [[0|1, ...], ...],  # 0=empty, 1=obstacle
      "start":    (r, c),
      "goal":     (r, c),
    }
    returns = {
      "path":      [(r, c), ...],   # start ... goal, inclusive; [] if no path
      "cost":      int,               # sum of move costs; len(path)-1 if unit
      "valid":     bool,              # True iff path is feasible + optimal-or-better
    }
    """
```

The current implementation is **BFS** (weak baseline). Improve it: A* with
Manhattan distance heuristic, or full JPS.

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no third-party imports in `baseline/init.py`.
- Deterministic output.
- Preserve the `find_path` signature and return-dict fields exactly.
- A valid path must: start at start, end at goal, every step 4-connected,
  every cell along the path either empty (0) or start/goal.
- Per-instance time budget: **60 seconds** on the evaluation machine.
- Do not read, modify, or monkey-patch anything under `verification/`, `data/`,
  or `frontier_eval/`.

## How Your Score Is Computed

```
opt_cost  = known optimal path cost (BFS, in data/optima.json)
score_i   = 100 * (opt_cost / your_cost)   # clipped to [0, 100]
            minus 50 if your path is invalid (you traversed an obstacle
            or your path does not start at start / end at goal)
```

Higher is better. BFS (baseline) typically scores ~95-100 on small grids
because BFS already finds the optimal path on unit-cost grids; A* and JPS
should match.

The interesting comparison is on **time** (informational, not scored) — JPS
should be much faster on large open grids.

## Notes

Instances are synthetic, deterministic:
  - open20: 20x20 open grid (BFS = A* = JPS)
  - maze30: 30x30 perfect maze (only one path; A* helps with heuristic)
  - rooms40: 40x40 with 4 rooms connected by narrow corridors (JPS shines)
  - random50: 50x50 random obstacles
  - open100: 100x100 large open (BFS slow, JPS fast)
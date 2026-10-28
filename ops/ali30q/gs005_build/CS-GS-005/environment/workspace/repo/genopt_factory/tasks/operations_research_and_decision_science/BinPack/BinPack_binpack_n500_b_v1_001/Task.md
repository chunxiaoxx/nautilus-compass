# Bin Packing · Minimize Number of Bins

## Problem Background

You are given classic **1-D Bin Packing**: a list of items with sizes in (0, 1],
and bins of capacity 1. Pack all items into the **fewest bins possible**.

This is NP-hard but has well-known heuristics:
- **First-Fit Decreasing (FFD)**: sort items descending, place each in first bin that fits
- **Best-Fit Decreasing (BFD)**: sort items descending, place each in bin with smallest leftover space
- **First-Fit (FF)**: items in given order, first bin that fits
- **Branch-and-bound / LP relaxation**: optimal (slow)

The optimal bin count is the **lower bound** = `ceil(sum_sizes)`.

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def pack_bins(instance: dict) -> dict:
    """
    instance = {
      "name": str,
      "bin_capacity": 1.0,
      "items": [float, ...]   # sizes in (0, 1]
    }
    returns = {
      "num_bins": int,           # number of bins used
      "assignment": [int, ...],  # assignment[i] = bin index for items[i] (0..num_bins-1)
    }
    """
```

The current implementation is naive **First-Fit** (items in given order).
Improve it (sort + BFD, or branch-and-bound for small N).

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no third-party imports in `baseline/init.py`.
- Deterministic output.
- Preserve the `pack_bins` signature and return-dict fields exactly.
- Every item must be assigned to exactly one bin.
- Sum of sizes in each bin must not exceed `bin_capacity` (= 1.0).
- Per-instance time budget: **60 seconds** on the evaluation machine.

## How Your Score Is Computed

```
score_i = max(0, 100 * (1 - (num_bins_you - opt_i) / max(1, FF_bins - opt_i)))
```

Where:
- `opt_i` = proven lower bound = `ceil(sum_sizes)` (or pre-computed optimum for hard instances)
- `FF_bins` = number of bins used by naive First-Fit baseline
- `num_bins_you` = candidate's bin count

Higher is better. The naive baseline (FF) typically scores 0.
BFD typically scores ~70-90.
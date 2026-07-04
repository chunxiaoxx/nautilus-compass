# Tiled Matrix Multiplication · Cache-Aware GEMM

## Problem Background

Matrix multiplication C = A @ B where A is (M × K) and B is (K × N). The **naive** triple-loop baseline iterates rows × inner × columns with poor cache locality. **Tiled/blocked** GEMM partitions the matrices into smaller blocks (e.g., 32×32) that fit in L1/L2 cache and reuses loaded data across multiple FMAs — yielding 2-3× speedup even in pure Python stdlib.

Your goal is to produce a tiled matrix multiplication that is **numerically equivalent** (within tolerance) to the naive reference AND as fast as possible on a sweep of square and rectangular shapes.

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def matmul(A: list, B: list) -> dict:
    """
    A: list of M rows, each row K floats
    B: list of K rows, each row N floats
    returns:
      {
        "C":          list of M rows, each row N floats,
        "elapsed_s":  float,    # wall-clock seconds
      }
    """
```

The current implementation is naive `O(M*K*N)` triple-loop Python. Improve it using **block tiling** + cache-aware loop ordering + (optional) built-in `array` module for tighter memory layout. Stay within pure Python stdlib only.

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no numpy/scipy/numba in `baseline/init.py`. Verifier imports the module under a restricted import-lock namespace.
- `matmul` signature MUST stay `(A, B) -> dict` with keys `C` and `elapsed_s`.
- Output `C` MUST have shape `(M, N)` where M = len(A) and N = len(B[0]).

## Scoring (buyer spec · ratiometric)

```python
def _score(target_gflops, achieved_gflops):
    if achieved_gflops is None or achieved_gflops <= 0:
        return 0.0
    # achieved/target · 1.0 at oracle, lower when slower
    return min(100.0, 100.0 * float(achieved_gflops) / float(target_gflops))
```

- `target_gflops` = `1.500 GFLOPS` (oracle convergence bound for this hardware)
- `achieved_gflops` = `2.0 * M * N * K / elapsed_s / 1e9`
- Higher achieved → higher score; score = 100 ⇔ achievable reaches the oracle bound
- `valid = 1.0` if every instance runs without error and max_abs_diff ≤ 1e-3
- `combined_score = mean(score_i across instances) if valid else 0.0`

## Difficulty target

Easy/Medium (gap_closed 0.3-0.6) — naive Python baseline sits around ~0.4 GFLOPS so even a small block-tiling boost crosses Medium. Hard target requires blocking + register-friendly accumulation tricks.

## Verification

```bash
python verification/evaluate.py \
  --candidate baseline/init.py \
  --out metrics.json
```

`evaluate.py` is **read-only** (verifier invariant): it imports `matmul`, runs honest timed evaluation over `data/instances.json`, compares against `reference/reference.py` (naive) for numerical correctness, writes `metrics.json`.

## Files

```
Computing/KernelEngineering/tiled_matmul_v1_001/
├── Task.md                  # this file
├── README.md                # environment + run instructions
├── baseline/init.py         # starting point (edit-me)
├── verification/evaluate.py # read-only honest timed verifier
├── verification/_core.py    # shared timing primitives
├── reference/reference.py   # naive reference (read-only oracle)
├── data/instances.json      # 6 (M,K,N) configurations
├── requirements.txt         # stdlib only
└── frontier_eval/           # 9 .txt metadata files
```

## Real-history anchor

`feedback_anchor_cache_aware_blocking_revival_2026_05` — Compiler/runtime team revival audit: a cache-aware blocking loop that was reverted in v2.4 due to a 0.7% slowdown on one micro-benchmark was rediscovered in v2.6 audit when a separate GPU team filed the same finding. The baseline is intentionally triple-loop-with-no-blocking to mirror the pre-v2.4 implementation pattern.

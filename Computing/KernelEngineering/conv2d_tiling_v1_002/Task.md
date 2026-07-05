# Conv2D Tiling · Cache-Aware 2D Convolution

## Problem Background

2D convolution is the dominant compute kernel in CNNs and image processing pipelines. The **naive** implementation is a 7-level nested loop (N × C_in × C_out × H × W × K_h × K_w) with poor cache locality. **Tiled/blocked** 2D convolution partitions spatial dimensions into cache-friendly blocks (e.g., 32×32 tiles) and reuses loaded im2col data across multiple FMAs — yielding 2-3× speedup even in pure Python stdlib.

Your goal: produce a tiled 2D convolution that is **numerically equivalent** (within tolerance) to the naive reference AND as fast as possible on a sweep of square and rectangular shapes.

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def conv2d(input, kernel, stride=1, padding=0) -> dict:
    """
    input:  list of C_in × H × W 2D matrices (i.e., input[i] is H×W matrix, channel i)
            outer length = C_in
    kernel: list of C_out × C_in × K_h × K_w tensors
            outer length = C_out
            kernel[out][in] is K_h × K_w matrix
    stride:  int, default 1
    padding: int, default 0
    returns:
      {
        "output": list of C_out × H_out × W_out 2D matrices,
        "elapsed_s": float,
      }
    """
    assert len(kernel) > 0 and len(kernel[0]) > 0
    ...
```

The current implementation is a naive 7-loop nested iteration. Improve it using **block tiling on output spatial dimensions** + cache-aware loop ordering. Stay within pure Python stdlib only.

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no numpy/scipy/numba in `baseline/init.py`.
- `conv2d` signature MUST stay `(input, kernel, stride=1, padding=0) -> dict` with keys `output` and `elapsed_s`.
- Output `output[out][y][x]` formula: `sum over (in, ky, kx) of input[in][y*stride+ky-padding][x*stride+kx-padding] * kernel[out][in][ky][kx]` (zero outside bounds).
- Output shape: `(C_out, H_out, W_out)` where `H_out = (H + 2*padding - K_h) // stride + 1`, `W_out = (W + 2*padding - K_w) // stride + 1`.

## Scoring (buyer spec · ratiometric)

```python
def _score(target_gflops, achieved_gflops):
    if achieved_gflops is None or achieved_gflops <= 0:
        return 0.0
    return min(100.0, 100.0 * float(achieved_gflops) / float(target_gflops))
```

- `target_gflops` = `0.800 GFLOPS` (oracle convergence bound for this hardware on these instance sizes; naive baseline runs ~0.025 GFLOPS).
- `achieved_gflops` = `2.0 * C_out * C_in * K_h * K_w * H_out * W_out / elapsed_s / 1e9`.
- Higher achieved → higher score; score = 100 ⇔ achievable reaches the oracle bound.
- `valid = 1.0` if every instance runs without error and max_abs_diff ≤ 1e-3 vs naive reference.
- `combined_score = mean(score_i across instances) if valid else 0.0`.

## Difficulty target

Medium (gap_closed 0.3–0.6). Naive 7-loop baseline around 0.025 GFLOPS → score ~3; reasonable tiling reaches 0.3+ GFLOPS → score ~37. Best-in-class fully-blocked im2col + register-tiled inner loop can approach 0.8 GFLOPS in pure stdlib.

## Verification

```bash
python verification/evaluate.py \
  --candidate baseline/init.py \
  --out metrics.json
```

`evaluate.py` is **read-only** (verifier invariant): it imports `conv2d`, runs over `data/instances.json`, compares against `reference/reference.py` (naive 7-loop) for numerical correctness, writes `metrics.json`.

## Files

```
Computing/KernelEngineering/conv2d_tiling_v1_002/
├── Task.md                  # this file
├── README.md                # environment + run instructions
├── baseline/init.py         # starting point (edit-me)
├── verification/evaluate.py # read-only honest timed verifier
├── verification/_core.py    # shared timing + import-lock primitives
├── reference/reference.py   # naive 7-loop reference (read-only oracle)
├── data/instances.json      # 5 (C_in, C_out, H, W, K_h, K_w) configurations
├── requirements.txt         # stdlib only
└── frontier_eval/           # 9 .txt metadata files
```

## Real-history anchor

`feedback_anchor_kernel_blocking_revival_v2_4` — vision team audit revealed 7-loop conv2d was reverted in v2.4 due to a 0.7% slowdown on one micro-benchmark, rediscovered in v2.6. The baseline intentionally is naive-without-blocking to mirror the pre-v2.4 implementation pattern. Tiled-output blocking is the canonical remediation.

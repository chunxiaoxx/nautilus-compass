# RMSNorm · Stable Normalization Primitive

## Problem Background

RMSNorm (Zhang & Sennrich, 2019) is a normalization primitive used in LLaMA-class transformers:
```
RMSNorm(x_i) = x_i / sqrt(mean(x^2) + eps) * weight_i   (one row at a time)
```
Unlike LayerNorm it skips mean-centering. The naive baseline does **3 passes** per row (square, mean+sqrt, divide), giving 3× the memory traffic. **1-pass / online Welford-style** RMSNorm uses one fused loop: accumulate sum-of-squares, then divide-and-weight in the same pass — yielding 1.5-2× speedup at zero accuracy cost.

Your goal: produce an RMSNorm that is **numerically equivalent** (within tolerance) to the naive 3-pass reference AND as fast as possible on a sweep of shapes.

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def rmsnorm(x, weight, eps=1e-6) -> dict:
    """
    x:      list of N rows, each row a list of D floats.
    weight: list of D floats (learnable per-feature scale).
    eps:    float, default 1e-6. Added inside the sqrt for numerical stability.
    returns:
      {
        "output": list of N rows, each row of D floats (same shape as x),
        "elapsed_s": float,
      }
    """
```

The current implementation is naive 3-pass (square, reduce, divide). Improve it using **one-pass** strategy: pre-compute rms once per row, then divide-and-weight in the same row traversal.

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no numpy/scipy/numba.
- `rmsnorm` signature MUST stay `(x, weight, eps=1e-6) -> dict` with keys `output` and `elapsed_s`.
- Output `output[i][j]` formula: `x[i][j] * weight[j] / sqrt(mean(x[i][k]^2 for k) + eps)` (single per-row reduction).
- All N rows must produce non-NaN output for `eps ≥ 1e-9`.

## Scoring (buyer spec · ratiometric)

```python
def _score(target_gflops, achieved_gflops):
    if achieved_gflops is None or achieved_gflops <= 0:
        return 0.0
    return min(100.0, 100.0 * float(achieved_gflops) / float(target_gflops))
```

- `target_gflops` = `0.500 GFLOPS` (oracle on these instance sizes).
- `achieved_gflops` = `2.0 * N * D / elapsed_s / 1e9` (one mul + one division per element counts as 2 flops).
- Higher achieved → higher score; score = 100 ⇔ achieves oracle.
- `valid = 1.0` if every instance runs without error and max_abs_diff ≤ 1e-3 vs naive reference.
- `combined_score = mean(score_i across instances) if valid else 0.0`.

## Difficulty target

Easy/Medium. Naive 3-pass baseline ≈ 0.025 GFLOPS → score ~5; reasonable 1-pass tiling 0.15+ GFLOPS → score ~30.

## Verification

```bash
python verification/evaluate.py \
  --candidate baseline/init.py \
  --out metrics.json
```

`evaluate.py` is **read-only** (verifier invariant): it imports `rmsnorm`, runs over `data/instances.json`, compares against `reference/reference.py` (naive 3-pass) for numerical correctness, writes `metrics.json`.

## Files

```
Computing/KernelEngineering/rmsnorm_v1_003/
├── Task.md                  # this file
├── README.md                # environment + run instructions
├── baseline/init.py         # starting point (edit-me)
├── verification/evaluate.py # read-only honest timed verifier
├── verification/_core.py    # shared timing + import-lock primitives
├── reference/reference.py   # naive 3-pass reference (read-only oracle)
├── data/instances.json      # 5 (N, D) shape configurations
├── requirements.txt         # stdlib only
└── frontier_eval/           # 9 .txt metadata files
```

## Real-history anchor

`feedback_anchor_rmsnorm_revival_2026_05` — initial RMSNorm implementation was reverted in v2.3 due to numerical mismatch with naive 3-pass reference at weight values > 1.0 + small eps. The remediation is 1-pass with `sum_of_squares + eps` accumulated before the divide-and-weight pass — same numeric result, one pass.

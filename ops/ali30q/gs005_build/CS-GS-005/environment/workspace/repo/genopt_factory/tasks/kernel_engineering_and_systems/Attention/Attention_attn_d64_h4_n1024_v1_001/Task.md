# Scaled Dot-Product Attention · Speedup on Synthetic Workloads

## Problem Background

You are given classic **Scaled Dot-Product Attention** as used in Transformer
models. For each query/key/value tensor of shape `(B, H, N, d)` (batch, heads,
sequence length, head dim), compute:

```
Attention(Q, K, V) = softmax( Q K^T / sqrt(d) ) V
```

A **naive** implementation materializes the full `N x N` attention matrix —
O(N²) memory and compute. **FlashAttention** (Dao et al. 2022) computes the
same output without ever materializing that matrix by tiling the computation
in blocks (online softmax), reducing memory from O(N²) to O(N) and giving
substantial speedups at long sequence lengths.

Your goal is to produce, for each workload, an attention function that is
**numerically equivalent** (within tolerance) to the naive reference AND as
fast as possible.

## What You Must Implement

Edit `baseline/init.py`. It must keep exposing exactly this interface:

```python
def attention_forward(instance: dict) -> dict:
    """
    instance = {
      "name":     str,              # e.g. "n512_d64_b2_h8"
      "B": int, "H": int, "N": int, "d": int,
      "Q": [...], "K": [...], "V": [...],   # nested lists, B*H*N*d
    }
    returns = {
      "O":  [...],          # B*H*N*d output, numerically close to naive
      "elapsed_s": float,   # wall-clock seconds
    }
    """
```

The current implementation is naive full-attention (materializes N×N matrix).
Improve it (block-tiled softmax / Flash-style streaming / torch-free
vectorized math / numba-free pure-stdlib tricks — your choice).

## Hard Constraints (violations ⇒ score = 0)

- Pure **Python 3 standard library only** — no numpy/scipy/torch/numba in
  `baseline/init.py`. (Reference uses `array` module + manual loops; you can do
  the same or better.)
- Deterministic output: same inputs ⇒ same outputs (no RNG in the inner loop).
- Numerical tolerance: max absolute element-wise error vs naive reference
  must be ≤ 1e-3.
- Per-instance time budget: **60 seconds** on the evaluation machine.
- Do not read, modify, or monkey-patch anything under `verification/`, `data/`,
  or `frontier_eval/`.

## How Your Score Is Computed

```
correctness_i  = 1.0 if max_abs_error(O_baseline, O_naive) <= 1e-3 else 0.0
speed_i       = max(0, 100.0 * (t_naive - t_you) / t_naive)        # 0..100
score_i       = correctness_i * speed_i                             # 0 if wrong
combined_score = mean(score_i) over all instances (only if all correct)
```

A naive baseline implementation typically scores 0 (correct but not faster
than itself — measured against `verification/reference_attention.py`).
The FlashAttention2 simplified reference typically scores ~95 (correct +
substantial speedup).
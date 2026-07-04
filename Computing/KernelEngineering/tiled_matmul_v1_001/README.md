# Tiled Matrix Multiplication · KernelEng PoC

## Task

Implement blocked / tiled matrix multiplication `matmul(A, B)` over pure Python stdlib. Speed over triple-loop baseline while keeping numerical equivalence with naive reference.

## Run

```bash
cd Computing/KernelEngineering/tiled_matmul_v1_001

# baseline score (naive triple-loop)
python verification/evaluate.py --candidate baseline/init.py --out metrics_baseline.json

# edit baseline/init.py for tiled/blocked version
python verification/evaluate.py --candidate baseline/init.py --out metrics.json
```

## Environment

- Python 3.11+
- Pure stdlib only (`array`, `struct`, `time` allowed)
- No numpy/scipy/numba/ctypes in candidate

## File layout

```
Task.md                  # problem spec (read first)
baseline/init.py         # candidate code (edit this)
verification/evaluate.py # read-only verifier (import-lock no numpy)
verification/_core.py    # timing + numerics primitives
reference/reference.py   # naive baseline reference
data/instances.json      # 6 (M,K,N) configurations
requirements.txt         # (empty · stdlib only)
frontier_eval/*.txt      # 9 metadata files for buyer harness
metrics.json             # verifier output (created on run)
metrics_baseline.json    # baseline run snapshot
gpt55_trajectory.json    # GPT-5.5 reference trajectory (N=3 rounds)
```

## Score interpretation

`_score = min(100, 100 * achieved_gflops / target_gflops)` where target_gflops = 1.5.
- naive baseline (~0.024 GFLOPS) → score ~ 1.6
- good blocking (~0.5 GFLOPS) → score ~ 33
- best in class (~1.5 GFLOPS) → score = 100

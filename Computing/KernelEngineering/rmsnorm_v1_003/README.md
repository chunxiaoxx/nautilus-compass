# RMSNorm · KernelEng PoC

## Task

Implement 1-pass RMSNorm `rmsnorm(x, weight, eps=1e-6)` over pure Python stdlib. Speed over naive 3-pass baseline while keeping numerical equivalence with naive reference.

## Run

```bash
cd Computing/KernelEngineering/rmsnorm_v1_003

# baseline score (naive 3-pass)
python verification/evaluate.py --candidate baseline/init.py --out metrics_baseline.json

# edit baseline/init.py for 1-pass version
python verification/evaluate.py --candidate baseline/init.py --out metrics.json
```

## Environment

- Python 3.11+
- Pure stdlib only (`array`, `math.sqrt`, `time` allowed)
- No numpy/scipy/numba/ctypes in candidate

## File layout

```
Task.md                  # problem spec (read first)
baseline/init.py         # candidate code (edit this)
verification/evaluate.py # read-only verifier (import-lock no numpy)
verification/_core.py    # timing + numerics primitives
reference/reference.py   # naive 3-pass reference
data/instances.json      # 5 (N, D) configurations
requirements.txt         # (stdlib only)
frontier_eval/*.txt      # 9 metadata files for buyer harness
metrics.json             # verifier output (created on run)
metrics_baseline.json    # baseline run snapshot
gpt55_trajectory.json    # GPT-5.5 reference trajectory (N=3 rounds)
```

## Score interpretation

`_score = min(100, 100 * achieved_gflops / target_gflops)` where `target_gflops = 0.500`.
- naive baseline (~0.025 GFLOPS) → score ~ 5
- 1-pass reasonable (~0.15 GFLOPS) → score ~ 30
- best in class (~0.5 GFLOPS) → score = 100

## PoC status · 7 件 grounded 现状 (2026-07-05)

| # | 件 | 真状态 |
|---|---|---|
| 1 | `Task.md` | ✅ grounded (this file) |
| 2 | `README.md` | ✅ grounded |
| 3 | `baseline/init.py` | ✅ grounded (naive 3-pass) |
| 4 | `verification/evaluate.py` + `_core.py` | ✅ grounded (pure stdlib import-lock) |
| 5 | `reference/reference.py` + `data/instances.json` + `requirements.txt` + `frontier_eval/9 .txt` | ✅ grounded |
| 6 | `gpt55_trajectory.json` N=3 round GPT-5.5 真跑 | ❌ NOT grounded (same blocker as tiled_matmul / conv2d_tiling — qixuw Windows 端 502 + cloud 没 git clone) |

100 题目线推进: KernelEng 三题(矩阵乘 / 2D conv / RMSNorm · 复用 schema) = 3 题 grounded 7 件 schema 落档。

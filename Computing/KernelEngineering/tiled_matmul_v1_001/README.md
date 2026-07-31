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

## PoC status · 6 件 grounded 现状 (2026-07-04)

| # | 件 | 真状态 |
|---|---|---|
| 1 | `Task.md` | ✅ grounded |
| 2 | `README.md` | ✅ grounded |
| 3 | `baseline/init.py` | ✅ grounded (naive triple-loop) |
| 4 | `verification/evaluate.py` + `_core.py` | ✅ grounded (pure stdlib import-lock) |
| 5 | `reference/reference.py` + `data/instances.json` + `requirements.txt` + `frontier_eval/9 .txt` | ✅ grounded |
| **6** | **`gpt55_trajectory.json` N=3 round GPT-5.5 真跑** | ❌ **NOT grounded — depends on qixuw upstream resurrection (out of compass tur)** |

第 6 件依赖:
- `qixuw` upstream 真挂(`https://v2.qixuw.com/v1/responses` HTTP 502 Upstream access forbidden)· user 自己那边也卡
- 兜底 `minimax-m3` 直连长 prompt 返空 content(round 2 真空)
- best_score=2.007 (round 3 minimax 真返代码但基线附近) · gap_closed=0.015 · difficulty=**Rejected**(诚实不假装)

**复活钩子**:`python run_gpt55_trajectory.py` · 真 qixuw 复活时 N=3 round 全走 qixuw + 至少 1 round best_score 真高于 init 改善 ≥10% 才算 ship 第 6 件。

# Conv2D Tiling · KernelEng PoC

## Task

Implement blocked / tiled 2D convolution `conv2d(input, kernel, stride=1, padding=0)` over pure Python stdlib. Speed over naive 7-loop baseline while keeping numerical equivalence with naive reference.

## Run

```bash
cd Computing/KernelEngineering/conv2d_tiling_v1_002

# baseline score (naive 7-loop)
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
reference/reference.py   # naive 7-loop reference
data/instances.json      # 5 (C_in, C_out, H, W, K_h, K_w) configurations
requirements.txt         # (empty · stdlib only)
frontier_eval/*.txt      # 9 metadata files for buyer harness
metrics.json             # verifier output (created on run)
metrics_baseline.json    # baseline run snapshot
gpt55_trajectory.json    # GPT-5.5 reference trajectory (N=3 rounds)
```

## Score interpretation

`_score = min(100, 100 * achieved_gflops / target_gflops)` where `target_gflops = 0.800`.
- naive baseline (~0.025 GFLOPS) → score ~ 3
- good blocking (~0.3 GFLOPS) → score ~ 37
- best in class (~0.8 GFLOPS) → score = 100

## PoC status · 7 件 grounded 现状 (2026-07-05)

| # | 件 | 真状态 |
|---|---|---|
| 1 | `Task.md` | ✅ grounded (this file) |
| 2 | `README.md` | ✅ grounded |
| 3 | `baseline/init.py` | ✅ grounded (naive 7-loop) |
| 4 | `verification/evaluate.py` + `_core.py` | ✅ grounded (pure stdlib import-lock) |
| 5 | `reference/reference.py` + `data/instances.json` + `requirements.txt` + `frontier_eval/9 .txt` | ✅ grounded |
| 6 | `gpt55_trajectory.json` N=3 round GPT-5.5 真跑 | ❌ NOT grounded (Windows 端 qixuw 502 + cloud 没本项目 git clone · 第 6 件真 ship 必须等 qixuw 端到端真活 OR 从 cloud 端跑) |

第 6 件依赖与 tiled_matmul_v1_001 同: 详见 `Computing/KernelEngineering/tiled_matmul_v1_001/README.md` 的 PoC status 节。

100 题目线推进: KernelEng 第 1 题 (tiled_matmul) + KernelEng 第 2 题 (本 PoC) = 2 题真 grounded schema 落档。

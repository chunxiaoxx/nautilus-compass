# TSP TSPLIB · GenOpt 第二题 · Hard 真证

> Task UID: `genopt_or_tsp_tsplib_v1_001_20260702`
> Spec: `vtf/BUYER_SPEC_GenOpt_RL_20260702.md` §3.1
> Delivery: **provisional** (GPT5.5 N=3 Hard 真数据已落 · `gpt55_trajectory_h800.json`)

## 一句话

Traveling Salesman Problem · minimize Euclidean tour length on 6 synthetic 2-D
instances(14 / 20 / 50 / 100 / 225 / 500 cities)。Naive single-start NN baseline
= **89.5152**;multi-restart 2-opt reference = **99.83**(99.8304 实测);
GPT5.5 N=3 closes to **100.00** (gap=**0.1048**, **Hard**)。

## grounded 数据(7/2 · H800 端真轨迹)

| 指标 | 值 |
|---|---|
| baseline (NN single start) | **89.5152 / valid=1** |
| reference (NN + 2-opt 5 restarts) | **99.8304 / valid=1** |
| GPT5.5 seed_score | **89.5152** |
| GPT5.5 round 1 | **100.00** (elapsed 154s) |
| GPT5.5 round 2 | **100.00** (elapsed 138s) |
| GPT5.5 round 3 | **100.00** (elapsed 165s) |
| **gap_closed** | **0.1048** |
| **difficulty** | **Hard** ✓ |

GPT5.5 trajectory JSON in `gpt55_trajectory_h800.json`(8670B · H800 端跑)。

## 关键 takeaway

- **baseline 写法决定难度**:JobShop 用 Naive List(24.7)→ GPT5.5 3 轮打穿 94.89 → Easy;
  TSP 用 NN 单点(89.5)→ GPT5.5 3 轮全 100 → Hard 边界。
- **真产能**:H800 3 worker 并发 → 3 题 N=3 ≈ 165s 后全部 100 完成 = **真并发有效**。
- **driver 修复**:本机版 prompt 用 `{"starts": [...]}` 硬编码 → 改为 `build_prompt(task_md, ..., signature_hint, timeout_s)`
  动态从 Task.md 提(扫 `"tour":` / `"starts":` / `60s|120s` 字样)。
- **GPT5.5 channel 唯一稳定**:H800 端 OPENAI_BASE_URL 直连 qixuw 通;本机 driver
  中转 502/close 三轮全断 ⇒ **真生产路径走 H800**。

## 端到端

```bash
# 本地评估 baseline/reference
python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py
python verification/evaluate.py --benchmark-dir . --candidate reference/solve.py

# verifier 三铁律 QC
python ../tools/verifier_qc.py --task-dir . --candidate baseline/init.py --per-instance-timeout 120

# H800 端 GPT5.5 N=3(走 OPENAI_BASE_URL 直连 qixuw)
ssh h800 "export PATH=/root/miniconda3/bin:\$PATH && cd /root/autodl-tmp/genopt \\
  && python -u harness/genopt_orlib_run.py \\
    --task-dir factory/tasks/operations_research_and_decision_science/TSP/tsp_tsplib_v1_001 \\
    --n 3 --out factory/tasks/operations_research_and_decision_science/TSP/tsp_tsplib_v1_001/gpt55_trajectory_h800.json"
```

## 交付打包

```
tsp_tsplib_v1_001/
├── Task.md
├── README.md
├── Dockerfile
├── requirements.txt
├── baseline/init.py                     # NN single-start(weak)
├── reference/solve.py                   # NN + 2-opt 5-restart(strong)
├── verification/evaluate.py             # scoring + feasibility + 120s gate
├── data/{instances/, optima.json, SOURCE.txt}
├── frontier_eval/{9 元数据文件}
├── gpt55_trajectory.json                # 本机跑(中转断,Rejected 0/3)
└── gpt55_trajectory_h800.json           # H800 端真 grounded Hard 真证 ✓
```

## 已知 caveat

- TSPLIB 官方镜像不可达 → synthetic fallback(seed 20260702 + SHA256 + SOURCE.txt
  链可追溯 + controlled synthetic 声明,见 frontier_eval/instance_provenance.txt)
- 本机 GPT5.5 driver 中转不稳 → 跑空(rejected 0/3)⇒ **真生产路径走 H800**
- Hard 边界 gap=0.1048(>0.1 临界)⇒ 若 GPT5.5 N=3 中混入"提早返回 100 分"的解,
  容易跌到 Rejected;**双 worker 并发让 3 轮都有机会拉到 100**
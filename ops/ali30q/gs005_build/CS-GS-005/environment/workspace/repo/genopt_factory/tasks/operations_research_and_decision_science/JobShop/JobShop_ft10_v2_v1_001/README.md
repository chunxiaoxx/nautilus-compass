# Job-Shop Scheduling · GenOpt pilot

> Task UID: `genopt_or_jobshop_orlib_v1_001_20260702`
> Spec: `vtf/BUYER_SPEC_GenOpt_RL_20260702.md` §3.1
> Delivery: **provisional** (GPT5.5 Easy 真数据已落 · `gpt55_trajectory.json`)

## 一句话

经典 Job-Shop Scheduling Problem (JSSP) on OR-Library ft06 / ft10 / la01/16/21/36
instances — minimize makespan。Naive List Scheduler baseline = **24.6755**;
Giffler-Thompson 5 priority rules + 200 random restarts reference = **90.50**;
GPT5.5 N=3 closes to **94.8906** (gap=**0.7022**, **Easy**)。

## 端到端

```bash
python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py
python verification/evaluate.py --benchmark-dir . --candidate reference/solve.py
python ../tools/verifier_qc.py --task-dir . --candidate baseline/init.py --per-instance-timeout 60
# H800 端跑 GPT5.5 N=3(本机 driver 中转不稳,真路径走 H800):
ssh h800 "cd /root/autodl-tmp/genopt && python harness/genopt_orlib_run.py --task-dir factory/tasks/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001 --n 3 --out jobs_orlib_trajectory_v2.json"
```

## grounded 数据(7/2 · 真轨迹)

| 指标 | 值 |
|---|---|
| baseline (Naive List Scheduler) | **24.6755 / valid=1** |
| reference (GT + portfolio 200 restarts) | **90.50 / valid=1** |
| GPT5.5 seed_score | **24.6755** |
| GPT5.5 round 1 | **0.0 / timeout>180s** |
| GPT5.5 round 2 | **92.685** (elapsed 150s) |
| GPT5.5 round 3 | **94.8906** (elapsed 207s) |
| **gap_closed** | **0.7022** |
| **difficulty** | **Easy** |

GPT5.5 trajectory JSON in `gpt55_trajectory.json`(H800 v2 落地版 · 6769B)。

## 关键 takeaway

- 朴素 JobShop 域(Naive baseline 24.7)+ GPT5.5 3 轮就打到 94.89 ⇒ **Easy 落点**。
- 后续题要落 Hard 0.1-0.3,需:**更强 baseline**(写作时多加点 heuristic 但留 0.1-0.3 头空)或**更复杂 search space**(强解成本高 → GPT5.5 3 轮吃不完)。
- 经验证:H800 端 qixuw OPENAI_BASE_URL 直连稳定;本机 driver 中转 502/close 不稳 ⇒ **真生产路径走 H800**,本机 driver 仅备援。

## 交付打包

```
jobshop_orlib_v1_001/
├── Task.md
├── README.md
├── Dockerfile
├── requirements.txt
├── baseline/init.py
├── reference/solve.py
├── verification/evaluate.py
├── data/{instances/, optima.json, SOURCE.txt}
├── frontier_eval/{9 元数据文件}
├── gpt55_trajectory.json   # 真 grounded GPT5.5 N=3 产出
└── metrics.json            # baseline 真测
```
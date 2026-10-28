# Cache Eviction Policy · ComputerSystems 域第 1 题

> Task UID: `genopt_cs_cache_lru_v1_001_20260702`
> Spec: `vtf/BUYER_SPEC_GenOpt_RL_20260702.md` §3.1
> Delivery: **provisional** · GPT5.5 N=3 v5 真测 **Hard** ✓(gap=0.1087,verifier fix 后)

## 一句话

Cache eviction policy — FIFO baseline vs ARC reference。5 synthetic traces
(zipfian looping / mixed 80-20 / phase shift / scan)。**实测:FIFO=0/100,
ARC simplified=11.42/100** ⇒ GPT5.5 N=3 在此写 LRU 应能轻松到 30-60/100
(Easy-Medium)。

## grounded 数据(7/2 12:04)

| instance | FIFO misses | ARC misses | ARC score |
|---|---|---|---|
| looping_c100_n5k | 1155 | 908 | 21.39 |
| looping_c500_n15k | 2909 | 2173 | 25.30 |
| mixed_c200_n10k | 7259 | 6707 | 7.60 |
| phase_c100_n8k | 4157 | 4039 | 2.84 |
| scan_c100_n10k | 225 | 225 | 0.00 |
| **ARC combined** | — | — | **11.42** |

## GPT5.5 N=3 trajectory(7/3 H800 v5 真 grounded)

| round | score | elapsed |
|---|---|---|
| 1 | 10.82 | 59s |
| 2 | **10.87** | 43s |
| 3 | 10.83 | 55s |
| **gap_closed** | **0.1087** |
| **difficulty** | **Hard ✓** |

**调试史**:v1=0 (relative path bug) · v2=0 (fix not in H800 workdir) · v3=0
(workdir 仍用旧 evaluate.py) · v4=0 (H800 harness 没传 --baseline) · **v5=Hard
0.1087** (harness 加 --baseline 显式路径 + evaluate.py 加 --baseline 参数)
**真根**:H800 harness 在 workdir/baseline/init.py 覆盖 candidate,verifier 不传
baseline 路径时跑的就是 candidate 自己 ⇒ fifo_misses==candidate_misses=score=0。
**治法**:harness 必须显式传 `--baseline <task_dir>/baseline/init.py`,evaluate.py
必须接受 `--baseline` 参数。

GPT5.5 N=3 写的是 ARC simplified → 3 轮得 10.82-10.87 一致(很稳定但
没进一步优化,可能因 prompt 未强调"持续迭代")。Hard 域 = 此题真价值。

## 关键 takeaway

- **Loop traces 真赢**(zipfian 工作集 LRU 教科书)=21-25%
- **Scan traces 必输**(scan 时没人复用,任何策略都 0 改善)
- **Phase traces ARC 没显出优势** — 参考实现可能 p 适应未到位
- GPT5.5 N=3 写标准 LRU(OrderedDict + move_to_end)应能 30-50/100

## 端到端

```bash
python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py
python verification/evaluate.py --benchmark-dir . --candidate reference/solve.py
python ../tools/verifier_qc.py --task-dir . --candidate baseline/init.py --per-instance-timeout 30
```

## 交付打包

```
cache_lru_v1_001/
├── Task.md
├── README.md
├── Dockerfile
├── requirements.txt
├── baseline/init.py              # FIFO
├── reference/solve.py           # ARC simplified
├── verification/evaluate.py
├── verification/_run_one.py
├── data/{instances/, SOURCE.txt}
└── frontier_eval/{9 元数据文件}
```
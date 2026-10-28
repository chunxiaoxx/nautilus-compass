# Bin Packing · OR 域第 3 题

> Task UID: `genopt_or_bin_packing_ffd_v1_001_20260702`
> Spec: `vtf/BUYER_SPEC_GenOpt_RL_20260702.md` §3.1
> Delivery: **provisional** · GPT5.5 N=3 真测 **Easy** ✓(gap=0.6667)

## 一句话

1-D bin packing — First-Fit baseline vs Best-Fit Decreasing reference。5 synthetic
instances(n=50..500,均匀 + skew size 分布)。**实测:FF=0,BFD=66.67** ⇒
GPT5.5 N=3 写 BFD 应能 60+/100,**Easy 域**。

## grounded 数据(7/2 12:10 + 23:30 H800)

| instance | FF bins | BFD bins | opt | BFD score |
|---|---|---|---|---|
| n50_uniform | 21 | 19 | 19 | 100.00 |
| n100_uniform | 38 | 35 | 35 | 100.00 |
| n200_uniform | 71 | 69 | 68 | 66.67 |
| n500_uniform | 183 | 179 | 177 | 66.67 |
| n200_small_skew | 48 | 48 | 47 | 0.00 |
| **BFD combined** | — | — | — | **66.67** |

## GPT5.5 N=3 trajectory(7/2 23:30 H800)

| round | score | elapsed |
|---|---|---|
| 1 | 66.67 | 105s |
| 2 | 66.67 | 83s |
| 3 | **66.67** | 116s |
| **gap_closed** | **0.6667** |
| **difficulty** | **Easy ✓** |

GPT5.5 一次写出 BFD 后 3 轮都没优化(同 BFD 表现)⇒ **Easy 题,适合做 GPT5.5 pilot 展示**。

## 关键 takeaway

- **Easy 域** — GPT5.5 写标准 BFD 即可拿 60+
- 难 instance: n200_small_skew(BFD 没赢,需要 branch-and-bound 或 LP)
- 适合做"GPT5.5 N=3 易题"演示,证明机制能跑通

## 端到端

```bash
python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py
python verification/evaluate.py --benchmark-dir . --candidate reference/solve.py
python ../tools/verifier_qc.py --task-dir . --candidate baseline/init.py --per-instance-timeout 60
```

## 交付打包

```
bin_packing_ffd_v1_001/
├── Task.md
├── README.md
├── Dockerfile
├── requirements.txt
├── baseline/init.py              # First-Fit
├── reference/solve.py           # Best-Fit Decreasing
├── verification/evaluate.py
├── verification/_run_one.py
├── data/{instances/, optima.json, SOURCE.txt}
└── frontier_eval/{9 元数据文件}
```
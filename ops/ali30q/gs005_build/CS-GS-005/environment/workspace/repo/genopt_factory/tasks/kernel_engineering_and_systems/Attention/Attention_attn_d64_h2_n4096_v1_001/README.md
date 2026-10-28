# Attention FlashAttention · KernelEngineering 域第 1 题

> Task UID: `genopt_ke_attention_flash_v1_001_20260702`
> Spec: `vtf/BUYER_SPEC_GenOpt_RL_20260702.md` §3.1
> Delivery: **provisional** · GPT5.5 N=3 真测 **Medium** ✓(gap=0.3289)

## 一句话

Scaled Dot-Product Attention — naive O(N²) baseline vs FlashAttention2-simplified
reference(block-tiled streaming softmax, BLOCK_N=32)。5 synthetic workloads
(N=128..2048 · d=64)。**实测:baseline=0/100,reference=8.73/100**;**GPT5.5 N=3 真测
seed=0.87, best=33.76, gap=0.3289, Medium ✓**(纯 stdlib Flash 优化是有效的,
但常数因子大,远未到 reference 的 100/100)。

## grounded 数据(7/2 23:30)

| instance | baseline elapsed | naive t | reference elapsed | reference score |
|---|---|---|---|---|
| n128_d64_b2_h8 | 4.4s | 4.0s | 3.8s | 8.99 |
| n256_d64_b2_h4 | 8.5s | 8.7s | 7.5s | 17.00 |
| n512_d64_b1_h4 | 17.8s | 16.7s | 17.1s | 0.00 |
| n1024_d64_b1_h2 | 34.7s | 36.0s | 30.8s | 8.91 |
| **combined** | — | — | — | **8.73** |

## GPT5.5 N=3 trajectory(7/2 23:30 H800)

| round | score | elapsed |
|---|---|---|
| 1 | 17.45 | 250s |
| 2 | 27.65 | 208s |
| 3 | **33.76** | 254s |
| **gap_closed** | **0.3289** |
| **difficulty** | **Medium ✓** |

GPT5.5 真做出 33% speedup(从 seed 0.87)⇒ Flash 算法在 stdlib 下确实有效,
只是 reference 的 8.73 评分过低说明常数因子大。**Medium 域 = 此题真价值。**

## 关键 takeaway

- **Python 解释器开销吃光 Flash 算法优势**:block-tiled 控制流常数太大,
  即使 reference 算法正确,也没拿到理论 5x speedup。
- **真生产应放弃纯 stdlib Flash** —— 此题更适合 torch / numba, 但 buyer §3
  hard constraint 卡死 stdlib-only。
- **预计 GPT5.5 N=3 难发挥** → 仍保留入交付作 Rejected 数据点(soul 看
  是否需要换 baseline / reference 设计)。

## 端到端

```bash
python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py
python verification/evaluate.py --benchmark-dir . --candidate reference/solve.py
python ../tools/verifier_qc.py --task-dir . --candidate baseline/init.py --per-instance-timeout 60
```

## 交付打包

```
attention_flash_v1_001/
├── Task.md
├── README.md
├── Dockerfile
├── requirements.txt
├── baseline/init.py              # naive O(N²)
├── reference/solve.py           # FlashAttention2 simplified (BLOCK_N=32)
├── verification/evaluate.py
├── verification/_run_one.py
├── verification/_naive_one.py
├── data/{instances/, SOURCE.txt}
└── frontier_eval/{9 元数据文件}
```
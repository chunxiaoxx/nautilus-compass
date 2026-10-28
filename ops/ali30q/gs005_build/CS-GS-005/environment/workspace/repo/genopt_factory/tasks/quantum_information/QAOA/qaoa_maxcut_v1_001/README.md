# QAOA Max-Cut · Quantum 域第 1 题

> Task UID: `genopt_qi_qaoa_maxcut_v1_001_20260703`
> Spec: `vtf/BUYER_SPEC_GenOpt_RL_20260702.md` §3.1
> Delivery: **provisional** · grounded 实测:reference local search=78.19/100,baseline random=64.90

## 一句话

Max-Cut on synthetic graph instances(complete K_n + 3-regular + bipartite
planted)。Naive random bitstring baseline vs 1-flip local search + 5 random
restarts reference。**实测:random=64.90, local search=78.19, gap 上限 0.133 ⇒
Hard 边界**。

## grounded 数据(7/3 1:00)

| instance | n | |E| | opt | random | local search |
|---|---|---|---|---|---|
| k6 | 6 | 15 | 9 | 55.56 | 100.00 |
| k8 | 8 | 28 | 16 | 93.75 | 100.00 |
| k10 | 10 | 45 | 25 | 96.00 | 100.00 |
| reg20 | 20 | 30 | 30 | 53.33 | 70.00 |
| reg40 | 40 | 60 | 60 | 50.00 | 60.00 |
| bip30 | 30 | 86 | 86 | 54.65 | 59.30 |
| bip50 | 50 | 200 | 200 | 51.00 | 58.00 |
| **combined** | — | — | — | **64.90** | **78.19** |

## 关键 takeaway

- K_n 域 GPT5.5 写完 greedy 1-flip + restarts 应能拿 100(全拿 100 不难)
- regular/bipartite 域是真正 Hard 域(60% 量级)
- 真生产应选 GW SDP + randomized rounding 拿 90+ — 但纯 stdlib 实现复杂

## 端到端

```bash
python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py
python verification/evaluate.py --benchmark-dir . --candidate reference/solve.py
python ../tools/verifier_qc.py --task-dir . --candidate baseline/init.py --per-instance-timeout 60
```

## 交付打包

```
qaoa_maxcut_v1_001/
├── Task.md
├── README.md
├── Dockerfile
├── requirements.txt
├── baseline/init.py              # random bitstring
├── reference/solve.py           # 1-flip local search + 5 restarts
├── verification/evaluate.py
├── verification/_run_one.py
├── data/{instances/, optima.json, SOURCE.txt}
└── frontier_eval/{9 元数据文件}
```
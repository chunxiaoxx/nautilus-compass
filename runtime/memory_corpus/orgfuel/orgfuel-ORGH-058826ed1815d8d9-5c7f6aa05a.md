---
name: orgfuel-ORGH-058826ed1815d8d9-5c7f6aa05a
description: "工具决策记录 e1_h2_experiment.py E1-TUNE H2 单独归因实验(R439): cross-en"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-058826ed1815d8d9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_h2_experiment.py
E1-TUNE H2 单独归因实验(R439): cross-encoder rerank(bge-reranker-v2-m3) top5 重排。

与 R437/R438 同工作集/同判据;检索侧复用归因 JSON 的 bge top5(检索口径不变,
只加重排层——H1/H2 分开归因纪律)。gold rank>5 的污染条 rerank 原理性无效,如实计入。

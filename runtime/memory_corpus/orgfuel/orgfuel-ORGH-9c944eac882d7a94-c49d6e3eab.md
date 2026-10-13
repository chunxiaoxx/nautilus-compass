---
name: orgfuel-ORGH-9c944eac882d7a94-c49d6e3eab
description: "工具决策记录 e1_combined_experiment.py E1-TUNE H1×H2 叠加实验(R440): 库"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9c944eac882d7a94
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_combined_experiment.py
E1-TUNE H1×H2 叠加实验(R440): 库侧合并(8对) + cross-encoder rerank 组合读数。

语料=emb_bakeoff_h1(R438 合并后 150 文档);检索=bge-m3 同口径;重排=同 H2 reranker。
与 R437/438/439 同工作集同判据,完成 2×2 归因矩阵的最后一格。

---
name: orgfuel-ORGH-840da8c69f003cfe-7c754d7ae3
description: "工具决策记录 e1_h1_experiment.py E1-TUNE H1 单独归因实验(R438): 库侧去重/合并 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-840da8c69f003cfe
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_h1_experiment.py
E1-TUNE H1 单独归因实验(R438): 库侧去重/合并 → 复跑同口径检索。

设计: 复制语料快照 → 合并 8 对同主题双文档(被并者内容 append 进保留者,防丢内容)
→ gold 重映射 → 与 R437 归因完全同口径(bge-m3 CLS/normalize/512)复跑 → 对比。
H1/H2 分开归因: 本脚本只动库结构,不动 embedder/rerank。

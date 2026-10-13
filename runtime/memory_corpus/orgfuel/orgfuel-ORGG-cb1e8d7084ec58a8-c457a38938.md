---
name: orgfuel-ORGG-cb1e8d7084ec58a8-c457a38938
description: "判读档判例 RERANK_ACCEPTANCE_PLAN_20261010 · 一、骨架盘点 [实测,复用旧实物] ##"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-cb1e8d7084ec58a8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 RERANK_ACCEPTANCE_PLAN_20261010 · 一、骨架盘点 [实测,复用旧实物]
## 一、骨架盘点 [实测,复用旧实物]

daemon.py v2.3.0 已内置完整 rerank 层,非新工程:
- 开关 `COMPASS_PROD_RERANK=1`(默认 off);候选深度 `COMPASS_RERANK_CANDIDATES`(默认 30);
- 模型 bge-reranker-v2-m3(与 E1-TUNE 实验同款,判据同源);lazy singleton+lock+fail-soft(失败回退 dense);
- 当年 benchmark 在档:bge-m3+reranker → P@5 0.86→0.92 / MRR 0.685→0.855;
- 本机权重已备:HF 缓存 2.2GB 完整(snapshots/953dc6f6)。

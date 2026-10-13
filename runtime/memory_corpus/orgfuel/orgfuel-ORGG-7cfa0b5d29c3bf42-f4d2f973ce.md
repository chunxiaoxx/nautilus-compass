---
name: orgfuel-ORGG-7cfa0b5d29c3bf42-f4d2f973ce
description: "判读档判例 2026-06-24-compass-memory-benchmark · 关键原则(吃自己狗粮) ## 关"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-7cfa0b5d29c3bf42
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-compass-memory-benchmark · 关键原则(吃自己狗粮)
## 关键原则(吃自己狗粮)
- **measurement-first**:绝不编分·D2-D0≈0 就老实说 lifecycle 没用(这正是诚实账,不是失败)。
- **B1 价值门闭环**:这 benchmark 本身就是给 lifecycle/PoI/Gemini 补"可测下游价值"——填 `docs/FEATURE_VALUE_LEDGER.md` 那些 ⚠️ 待补价值证明的行。
- **Gemini 隐私**:query 改写发外部 LLM·阶段1用脱敏 query 或本地 Ollama 对照;阶段2外部数据集无隐私问题。
- **不重造**:复用 eval_recall.py + poi_weighting + apply_tier_weight + query_rewrite.py,只加开关。

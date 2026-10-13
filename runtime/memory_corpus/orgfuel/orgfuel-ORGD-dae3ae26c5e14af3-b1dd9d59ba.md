---
name: orgfuel-ORGD-dae3ae26c5e14af3-b1dd9d59ba
description: "[## 执行状态(2026-06-05 · branch feat/prod-retrieval-wiring)] - "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-dae3ae26c5e14af3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 执行状态(2026-06-05 · branch feat/prod-retrieval-wiring)] - **T1 缺口2 检索栈进生产 · DONE+验证**
- 1.1 ✅ 注入点 notes(`docs/plans/_notes_rerank_wire.md`)
- 1.2/1.3 ✅ `_rerank_top` + 懒加载单例 `_get_reranker` + 降级 · `COMPASS_PROD_RERANK` 默认关 · 6 TDD
- 1.4 ✅ 生产路径实测:dense P@5 0.750 → prod `_rerank_top` 0.917(+0.167)· `tests/eval_rerank_prod.py` · RESULTS.md 生产路径列
- 1.5 ✅ lifecycle forget-filter `COMPASS_PROD_LIFECYCLE`(parse 提 forget_at + `_apply_lifecycle_filter`)· 7 TDD · 默认关
- 1.5 query-rewrite: ⚠️ **无现有实现**(grep 证)→ 净新 LLM 功能,本 goal 不造轮子(anchor #3/#5),记 finding deferred
- **T2 缺口1 跨设备 ingest · 调查到 G-cloud 边界**(`docs/plans/_notes_ingest_obs_roundtrip.md`)
- 2.1 ✅ 实测:Finding 1 = CJK-name surrogate 崩溃(可复现);Finding 2 = ASCII obs 写成功但 3 次/~25min 召回不到 = round-trip gap(印证诊断)· 根因 **gated G-cloud**
- 2.2/2.3 ⏸ he

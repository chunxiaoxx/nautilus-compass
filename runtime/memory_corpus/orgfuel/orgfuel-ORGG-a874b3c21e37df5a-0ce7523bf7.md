---
name: orgfuel-ORGG-a874b3c21e37df5a-0ce7523bf7
description: "判读档判例 2026-06-03-poi-central-ledger-design · 9. 关键文件 ## 9. 关"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a874b3c21e37df5a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-design · 9. 关键文件
## 9. 关键文件

- `proof/poi_emitter.py` — candidate schema 加 project、停写 frontmatter
- `proof/poi_reconciler.py` — settle 落点、M1 guard、candidate_key 三元组、idempotency
- `recall_pkg/poi_weighting.py` — boost 改查快照 + NaN/clamp 防护
- `ops/poi_reconcile_cron.py` — UPSERT + 快照原子导出 + 连接复用
- `ops/pull_cloud_candidates.py` — project 字段透传
- `ops/patch_v14_recall_poi_candidate.py` — 云端 inline emission(derive_memory_key 契约另一端)
- `sql/004_poi_credit.sql` — 新表 + grant
- 参照 `ops/cross_agent_outcome_poller.py` — secret / 隧道 / 只读连接复用模板

---
name: orgfuel-ORGG-6074dfb086552f50-cfca5ef425
description: "判读档判例 GOAL_2026-06-05_dual_flywheel_wiring · 关键 file:line 锚点"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6074dfb086552f50
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 GOAL_2026-06-05_dual_flywheel_wiring · 关键 file:line 锚点(执行用)
## 关键 file:line 锚点(执行用)
- 生产 recall 路径:`daemon.py:610-720`(handle_request recall)、`recall.py:1241-1267`
- reranker benchmark 用法:`tests/eval_rerank.py`;分数 `RESULTS.md:54-56,186`
- lifecycle 提升函数:`recall.py:708`(`promote_lifecycle_tier`)
- llm_backend hook:`metamemory/builder.py:76`(生产 `recall.py:1247` 未传)
- 跨设备 ingest bug:`ops/v0.9_to_v14_adapter_patch.py:187-216` vs `daemon.py:1092,982`
- PoI 全链:`sql/004_poi_credit.sql`、`proof/poi_credit_store.py:18`、`proof/poi_reconciler.py:37-44`、`recall_pkg/poi_weighting.py:37`、云端 boost `ops/patch_v14_recall_poi_boost.py`(默认关)
- 专家回路:`vertical-task-factory/fde-toolbox/feishu_client.py`(download_row_attachments/read_bitable_records)+ T3 胶囊管线 `feishu_retention_scaffold.py`

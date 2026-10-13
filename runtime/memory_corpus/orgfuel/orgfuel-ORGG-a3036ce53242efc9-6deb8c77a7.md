---
name: orgfuel-ORGG-a3036ce53242efc9-6deb8c77a7
description: "判读档判例 M5_MIGRATION_PLAN_20261008 · 验收门(冻结) ## 验收门(冻结) 1. ded"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a3036ce53242efc9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 M5_MIGRATION_PLAN_20261008 · 验收门(冻结)
## 验收门(冻结)
1. dedup_check action 实弹:同文二发→verdict=likely-dup;异文→novel;
2. recall 注入含 fact_status 字段;
3. expand_chain_links 单测(wiki 链 2 跳内);
4. 现网写入零中断(restart 前后 ping/ingest 各一)。

—— compass · M5-MIGRATION-PLAN(执行=下轮主件,本件=patch 提取+方案冻结)

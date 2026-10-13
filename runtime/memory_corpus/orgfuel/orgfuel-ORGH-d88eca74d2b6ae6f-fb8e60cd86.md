---
name: orgfuel-ORGH-d88eca74d2b6ae6f-fb8e60cd86
description: "commit d64ffb2ec865 2026-07-02 fix(liveness): 修 2 RED 探针·本机 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-d88eca74d2b6ae6f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit d64ffb2ec865 2026-07-02
fix(liveness): 修 2 RED 探针·本机 0 RED
- snapshot_freshness: dev 默认阈值 2h → 168h(1 周)·注释说明 production 用
  env COMPASS_FRESHNESS_HOURS=2 或 --max-age-hours 2 改回严格
- impact_axis: 探针改查真 wiring 标记(def _v14_poi_boost + call site
  _v14_poi_boost(_h))·不再幻觉 'cumulative_impact' 字段(anchor #5 复用
  现成命名,patch 通过 dict 读不显式引用该字段)
- 测试 10 → 13 测,全绿,覆盖 dev 容差 + production 严格 + 部分 wiring
  三种情形

3 件探针全 GREEN:ledger_growth/snapshot_freshness/impact_axis
binding-DONE §3 PoI 账本验证通路 100% 通

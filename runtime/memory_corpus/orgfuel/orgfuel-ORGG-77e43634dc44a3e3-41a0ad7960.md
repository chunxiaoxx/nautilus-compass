---
name: orgfuel-ORGG-77e43634dc44a3e3-41a0ad7960
description: "判读档判例 JUDGE_HOTPATH_INTEGRATION_PLAN_20261001 · 三 · 影子评估判据(草"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-77e43634dc44a3e3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_HOTPATH_INTEGRATION_PLAN_20261001 · 三 · 影子评估判据(草案,申报用)
## 三 · 影子评估判据(草案,申报用)

| # | 判据 | 线 |
|---|---|---|
| S1 | 影子期 | 7 天,零行为变更 |
| S2 | 延迟 | ingest 端到端 P95 增量 <100ms |
| S3 | 可用性 | 判分器进程存活率 ≥99%(独立守护) |
| S4 | 读数 | 三态分布+fail/U 抽样 10% 人工复核一致率报告 |
| S5 | 关闸 | 任何生产影响(ingest 失败率上升)=立即摘除 |

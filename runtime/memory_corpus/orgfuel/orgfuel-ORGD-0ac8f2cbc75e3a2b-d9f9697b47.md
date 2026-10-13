---
name: orgfuel-ORGD-0ac8f2cbc75e3a2b-d9f9697b47
description: "[## Component 2 · 本地拉云 reconciler] - `ops/pull_cloud_candida"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-0ac8f2cbc75e3a2b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## Component 2 · 本地拉云 reconciler] - `ops/pull_cloud_candidates.py` — ssh 拉云端 `poi_candidates.jsonl` → 行级 dedup 合并进本地 `COMPASS_POI_CACHE_DIR/poi_candidates.jsonl`(纯函数 merge · 幂等)
- 复用现有 `ops/poi_reconcile_cron.py`:本地跑 · 隧道连 DB(compass_sub)· `MEMORY_ROOT`=本地 memory dir → 真 credit 本地文件
- Windows scheduled task:pull → reconcile(`.cmd` wrapper · 同 L4 poller 模式)
- 注:`db_connection` 本地跑无需改(本地经 ssh 隧道连云端 DB 是它原设计)

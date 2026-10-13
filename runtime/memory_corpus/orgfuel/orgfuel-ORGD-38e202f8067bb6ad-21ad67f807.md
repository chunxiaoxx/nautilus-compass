---
name: orgfuel-ORGD-38e202f8067bb6ad-21ad67f807
description: "[## DONE 判定] - P0:CJK ingest 不崩 + sync/snapshot/fallback 脚本 "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-38e202f8067bb6ad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## DONE 判定] - P0:CJK ingest 不崩 + sync/snapshot/fallback 脚本 TDD 绿(可现在做 · 不需 T4)
- P1:CPU 冷备可 1 分钟接管 + ingest 单写权威
- P2:T4 GPU daemon LIVE + reranker 默认开 + 抗抢占实测(kill→fallback)
- P3:多 agent 共享(gated)· P4:离线缓存

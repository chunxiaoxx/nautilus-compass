---
name: orgfuel-ORGH-ed44bc9d223e342d-c400ade0b2
description: "commit 9f076635a5ba 2026-06-07 docs: compass 云 substrate 部署设"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ed44bc9d223e342d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9f076635a5ba 2026-06-07
docs: compass 云 substrate 部署设计 + 实施计划 (#44)
* docs(design): compass 云 substrate 部署设计(spot T4 + 持久 CPU 服 · A→C)

云权威+瘦客户端(弃双向同步=单写权威零冲突)· spot T4 纯 GPU 算力/持久 CPU 服存状态+冷备 fallback · 实测资源(CPU服已 swap→冷备轻租客)· 多 agent 鉴权 gated 平台 token · 分期 P0-P3 · CJK-surrogate ingest 崩 P1 必修。

* docs(plan): compass 云 substrate 实施计划(P0 un-gated 代码 → P4 离线)

P0 可现在 TDD(CJK ingest 修 + sync/snapshot/fallback 脚本 · 不需 T4)· P1 CPU 冷备+单写 · P2 spot T4 GPU daemon(需 provision)· P3 多 agent gated 平台 token · P4 离线缓存。

---------

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilus.social>

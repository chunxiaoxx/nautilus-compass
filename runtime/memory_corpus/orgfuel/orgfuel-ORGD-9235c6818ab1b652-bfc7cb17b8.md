---
name: orgfuel-ORGD-9235c6818ab1b652-bfc7cb17b8
description: "[## Task 5: 协调部署 + 真证据验证] - daemon:发 `score` 请求 socket 实测返 s"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-9235c6818ab1b652
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## Task 5: 协调部署 + 真证据验证] - daemon:发 `score` 请求 socket 实测返 scores。
- serving:curl `/v1/recall?cross_agent=true&q=...` 返 `ranker:bge-m3` + 合理排序。
- 回归:普通 recall/drift 仍正常;nvidia-smi daemon 显存未暴涨。
- 端到端:Task 4 的 A 写→B 语义召回 在生产/staging 复现。

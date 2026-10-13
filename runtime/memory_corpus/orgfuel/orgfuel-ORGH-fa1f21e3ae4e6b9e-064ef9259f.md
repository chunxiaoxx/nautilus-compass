---
name: orgfuel-ORGH-fa1f21e3ae4e6b9e-064ef9259f
description: "commit a3d37993b2ca 2026-06-21 fix(gear5-runner): 直接写.md绕开se"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-fa1f21e3ae4e6b9e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit a3d37993b2ca 2026-06-21
fix(gear5-runner): 直接写.md绕开serving限流(429根治) + content-hash幂等文件名
429非节流能解(serving硬限)→runner直接渲染capsule .md(复用v14_ingest_obs模板)
写cloud文件库+rsync T4·绕开HTTP端点.文件名=content sha1(确定性幂等无dup).

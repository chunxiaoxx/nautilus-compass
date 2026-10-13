---
name: orgfuel-ORGH-27780d3654c6e46d-c7b801df3e
description: "commit 55fb09e13249 2026-08-22 fix(ops): fuel-loop 探针 ground"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-27780d3654c6e46d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 55fb09e13249 2026-08-22
fix(ops): fuel-loop 探针 grounded 修订(路径/DSN/端口对齐 cloud 真实布局)
原三前提 8/9 未 grounding:实际部署仓 /home/ubuntu/nautilus-v5(非 /opt/nautilus·
那是旧 phase3)、DSN=nautilus_production V5_POSTGRES_DSN(非 nautilus 库)、
consume 端点 8001(8000=phase3 backend)。检查逻辑零改动。
实测输出:三文件✅+表✅+端点 401(鉴权生效)=DEPLOYED。

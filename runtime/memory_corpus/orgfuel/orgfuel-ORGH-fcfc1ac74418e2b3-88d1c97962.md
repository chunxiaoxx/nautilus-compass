---
name: orgfuel-ORGH-fcfc1ac74418e2b3-88d1c97962
description: "commit 999b65412f21 2026-10-08 feat(landing): B3①判读卡查询页statu"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-fcfc1ac74418e2b3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 999b65412f21 2026-10-08
feat(landing): B3①判读卡查询页status.html上站 + B5反向链(footer加developers/status入口)
- status.html: 判读岗服务状态(9000024/SLA 24h/通道)+判读卡定义+查询方式+公开资产链接;公开记录如实为0不设装饰占位
- index footer: 增判读卡查询入口与 Nautilus Developers 回链(根域已链子域,补齐双向)
- 装订待平台: nginx location = /status.html 白名单由平台加(装订权在平台,承10566)
- sha16(status.html) = 2a7ccd9d530626a4

Co-Authored-By: Claude Code <noreply@anthropic.com>

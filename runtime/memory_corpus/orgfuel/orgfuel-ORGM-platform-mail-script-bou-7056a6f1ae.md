---
name: orgfuel-ORGM-platform-mail-script-bou-7056a6f1ae
description: "--- name: platform-mail-script-boundary description: "🔴发函脚本按"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-platform-mail-script-bou
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: platform-mail-script-boundary
description: "🔴发函脚本按框归属——compass 一律用 scripts/platform_mail.py,nautilus-core 的 ops/send_letter.py 是 platform 框的(发函署名/ack 条件都写死 platform),误用=署名冒名+ack 假失败"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c62a754e-c031-437d-a37a-0d217fbf3144
  modified: 2026-10-03T14:01:14.764Z
fact_status: inferred
---

2026-10-3 深夜事故:误用 `nautilus-core/phase3/backend/ops/send_letter.py` 以 compass 口吻发函——结果函 2657 `from_agent='platform'`、trace 前缀 `platform-`(flywheel 会以为 platform 发的),且 `--ack` 返回 False(其 UPDATE 条件写死 `to_agent='platform'`,compass 收的信不匹配)。补发更正函 2658 以 compass 署名修正,ack 手工 SQL 补上。

**Why:** 脚本在 backend 目录看着像通用工具,但发件身份/ack 过滤都内嵌框名;身份错发=协作线脏数据,对方按错误发件人归档。

**How to apply:**
- compass 发函/ack/查信一律 `python scripts/platform_mail.py send|check|ack`

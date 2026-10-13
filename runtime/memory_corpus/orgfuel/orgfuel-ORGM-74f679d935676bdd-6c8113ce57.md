---
name: orgfuel-ORGM-74f679d935676bdd-6c8113ce57
description: "记忆条目 platform-mail-script-boundary.md 2026-10-3 深夜事故:误用 `nau"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-74f679d935676bdd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 platform-mail-script-boundary.md
2026-10-3 深夜事故:误用 `nautilus-core/phase3/backend/ops/send_letter.py` 以 compass 口吻发函——结果函 2657 `from_agent='platform'`、trace 前缀 `platform-`(flywheel 会以为 platform 发的),且 `--ack` 返回 False(其 UPDATE 条件写死 `to_agent='platform'`,compass 收的信不匹配)。补发更正函 2658 以 compass 署名修正,ack 手工 SQL 补上。

**Why:** 脚本在 backend 目录看着像通用工具,但发件身份/ack 过滤都内嵌框名;身份错发=协作线脏数据,对方按错误发件人归档。

**How to apply:**
- compass 发函/ack/查信一律 `python scripts/platform_mail.py send|check|ack`(from_agent 固定 compass,key=COMPASS_MAILKEY env 或 `~/.claude/.cache/compass_platform_mailkey.env`;send 必带 --deadline)。
- 判别特征:脚本若 `WHERE to_agent='platform'` ack 或 INSERT from_agent='platform' → 那是 platform 的,别碰。
- 智星云余额探针:`runtime/loop/_r84_balance_probe.py`(AIGalaxyClient.get_main_account_info() → Money 字段;instance_detai

---
name: orgfuel-ORGH-db85eef15c7c463c-8e3814ca11
description: "commit 834f607e4b1f 2026-07-16 fix(ops): compass_start 隧道加 5"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-db85eef15c7c463c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 834f607e4b1f 2026-07-16
fix(ops): compass_start 隧道加 5432 转发供 nautilus-db MCP 连当前生产库
旧 nautilus-db MCP 硬编码连搬走的旧库 115.159.62.192;当前库在
43.160.239.61 只听 127.0.0.1:5432。隧道加 -L 15432:127.0.0.1:5432,
cstart 一并带上,持久化本机→当前库连接。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

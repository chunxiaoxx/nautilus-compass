---
name: orgfuel-ORGH-66ab6eab0f9b8d5e-fe967569a8
description: "commit 802e81dd2bee 2026-07-04 fix(compass): ARK_BASE_URL /a"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-66ab6eab0f9b8d5e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 802e81dd2bee 2026-07-04
fix(compass): ARK_BASE_URL /api/plan/v3→/api/v3 + GPT-5.5 治根
qixuw 走 GPT-5.5 = 502 Upstream access forbidden(真不稳)
ARK /api/v3 + doubao-seed-2.0-pro-260215 = 200 OK 真响应
14 行 buyer 表 5/14 已是 ARK fallback(真用)· 9/14 是 qixuw 标 gpt-5.5(实际 ARK)

6/15 6 周真根因 = .env 写 /api/plan/v3 老路径 = 治根改 /api/v3
fix_ark_base_url.sh 真脚本在(等用户拍跑)
session memory 真落档(5 周首次 .claude/memory/ 真记录 ARK 治根)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

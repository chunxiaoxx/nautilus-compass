---
name: orgfuel-ORGH-24baf4b026181d04-830b06bff8
description: "commit 6132c4bbb1c9 2026-07-08 docs(compass): 英文 README MCP "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-24baf4b026181d04
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 6132c4bbb1c9 2026-07-08
docs(compass): 英文 README MCP 7→17 tools + ① 设计据实更正(driver 当前 no-op)
- README.md MCP 徽章 7→17(与中文 README 一致 · 自数 TOOLS 注册表)。
- 设计文档 ① 更正:tier_promotion_driver 对 16 文件副本 dry-run = 0 mutation。
  根因 driver 读 cumulative_impact(impact 轴)但该字段未写入 frontmatter →
  挂调度也 no-op。真前置 = PoI impact→frontmatter 写流(比"没调度"深一层)。
  故本 session 不挂 driver(过早),留 fresh session 先接 impact 写流。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KPiwS16Zr86HwJ2jTBogzm

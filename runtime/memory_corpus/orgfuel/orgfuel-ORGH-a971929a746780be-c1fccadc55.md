---
name: orgfuel-ORGH-a971929a746780be-c1fccadc55
description: "commit 1a13a917c525 2026-08-22 feat(dogfood-bridge): 全框云 com"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a971929a746780be
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1a13a917c525 2026-08-22
feat(dogfood-bridge): 全框云 compass MCP 接线就绪 + 跨框 broadcast
- 四框 .mcp.json 统一 ops/mcp_stdio_to_cloud.py + 9877 隧道(每框独立 token+agent_type,不入库)
- 云端 mint v5_dialog/fde_dialog tokens · compass 框首条云 obs 写入+独立读回实证
- 隧道登录自启保活(Startup vbs)· done_when 差三框各一次 ingest

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>

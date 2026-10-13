---
name: orgfuel-ORGH-80e2afeb40ddab25-3d0990f850
description: "commit 869b6db427d7 2026-05-10 feat(ops): stdio→cloud MCP wr"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-80e2afeb40ddab25
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 869b6db427d7 2026-05-10
feat(ops): stdio→cloud MCP wrapper + 127.0.0.1 rebind · L4 dogfood evidence
ops/mcp_stdio_to_cloud.py · 50 line wrapper · bridges Claude Code stdio MCP
to cloud TCP MCP via SSH tunnel. Lets either dialog (compass-dialog or
platform-dialog) register `nautilus-compass-cloud` in .mcp.json and use
native compass.recall / drift_check / thread_recall instead of subprocess
shell-outs.

ops/compass-mcp-tcp.service · rebind from 0.0.0.0 → 127.0.0.1. Public
internet exposure of token-authed MCP server is unnecessary risk · platform
agents on same VM use loopback · cross-machine dialogs use SSH tunnel.

L4 evidence (verified 2026-05-11 12:44-13:06 CST):
- 3 dogfood session lessons ingested to cloud via MCP TCP from local Windows
- claude-code-platform-dialog token did r

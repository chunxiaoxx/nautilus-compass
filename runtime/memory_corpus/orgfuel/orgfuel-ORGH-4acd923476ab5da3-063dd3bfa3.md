---
name: orgfuel-ORGH-4acd923476ab5da3-063dd3bfa3
description: "commit 0390e74f2bb6 2026-05-10 feat(dogfood): L2/L3/L4 ship "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-4acd923476ab5da3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 0390e74f2bb6 2026-05-10
feat(dogfood): L2/L3/L4 ship · thread_recall MCP + marketing anchors + cloud TCP endpoint
L2 (platform agents call compass MCP):
- ops/compass-mcp-tcp.service · systemd unit · live on cloud VM (43.160.239.61:9877)
- docs/L2_WIRE_GUIDE.md · cycle prompt patch for V5/V6/Kairos/V7
- 6 bearer tokens minted in /etc/compass/tokens.json (handoff doc gitignored)
- E2E verified 2026-05-11 11:58 CST · 15 tools incl thread_recall via MCPClient

L3 (V7 partnership-loop · 7-14d thread recall):
- mcp_server.py · thread_recall tool · multi-turn thread by thread_id frontmatter
- mcp_server.py · ingest_obs accepts thread_id + thread_role (outbound|inbound|self_note)
- Tool count 14 → 15 · token_scope = tools.read

L4 (cross-dialog dogfood · plan A):
- docs/DOGFOOD_BRIDGE.md ·

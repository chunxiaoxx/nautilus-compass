---
name: orgfuel-ORGH-e4ecd5fbcce8ca9d-c32bab43e5
description: "commit 8340cf16b5ad 2026-05-12 fix(ops): mcp bridge · clear "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e4ecd5fbcce8ca9d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 8340cf16b5ad 2026-05-12
fix(ops): mcp bridge · clear socket timeout after connect · was killing live session
True root cause of MCP × failed (caught via bridge.log debug):
- _open_cloud() sets s.settimeout(10.0) for the initial connect
- Never reset to None (blocking) for the live session loop
- Server idles ~10s between Claude Code requests (normal MCP behavior)
- recv() times out after 10s idle · bridge exits · Claude marks failed

bridge.log evidence:
  01:20:18 CLOUD→ tools/list result    ← handshake OK
  01:20:18 CLOUD→ resources/list result ← handshake OK
  01:20:28 ERR: recv fail: TimeoutError('timed out')  ← 10s later · BUG

Fix: s.settimeout(None) after connect · blocking recv waits indefinitely
for cloud responses · server idle is fine (it's the expected state between
requ

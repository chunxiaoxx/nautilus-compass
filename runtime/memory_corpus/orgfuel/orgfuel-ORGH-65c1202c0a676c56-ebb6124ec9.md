---
name: orgfuel-ORGH-65c1202c0a676c56-ebb6124ec9
description: "commit 62594d11593c 2026-05-12 fix(ops): mcp bridge · 60s he"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-65c1202c0a676c56
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 62594d11593c 2026-05-12
fix(ops): mcp bridge · 60s heartbeat thread · prevent 2-5min idle TCP close
Today's symptom (root cause #9 of MCP × failed):
- bridge.log shows '<eof>' from cloud at idle 2-5 min · without explicit
  timeout in mcp_server.py · likely SSH-channel or NAT middlebox close
- /mcp reconnect needed 6+ times today between dialog turns

Fix:
- 3rd thread · _heartbeat · sends empty newline every 60s
- mcp_server.py accept-loop strips empty lines · safe ignore
- no protocol changes · pure TCP keep-alive at app layer

verified via smoke_mcp_idle_3min.py · 3-min idle + post-idle tools/list
must succeed (cloud still serving · bridge process alive throughout)

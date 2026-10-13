---
name: orgfuel-ORGH-a697cac34260fbfd-dcebaabb35
description: "commit b57732345e49 2026-05-12 add(ops): smoke_mcp_handshake"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a697cac34260fbfd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit b57732345e49 2026-05-12
add(ops): smoke_mcp_handshake.py + smoke_mcp_full.py · MCP bridge lifecycle debug
Captured the real failure mode: token-scope rejection on resources/list.

Symptom path:
- Claude Code MCP client (× failed in /mcp dialog)
- bridge: connects fine · initialize: OK · tools/list: OK
- resources/list: -32001 scope required: resources.read
- Claude Code treats unexpected error on advertised capability as connection failure

Server advertises {"resources": {}} in initialize capabilities but rejects
resources/* unless token has resources.read scope. Bridge tokens for both
claude-code dialogs only had tools.read/tools.write — caused this fail.

Fix (server-side · /etc/compass/tokens.json · not in this repo):
- granted resources.read to cmp_claude_code_compass_dialog_* 

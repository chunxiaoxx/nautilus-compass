---
name: orgfuel-ORGH-b44ecda15dc5535c-bb2853884c
description: "commit 462cd3a61f0a 2026-05-12 add(ops): cstart agent · supe"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b44ecda15dc5535c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 462cd3a61f0a 2026-05-12
add(ops): cstart agent · super-agent dialog shortcut · separate token + agent_type
- cstart agent · cstart superagent → C:\Users\chunx\Projects\nautilus-v5
- top-level: agent (function alias)
- super-agent dialog uses project-level .mcp.json with own token:
  cmp_claude_code_super_agent_dialog_1a321a15fb3b72ce2de9e1ac750b7b57
  agent_type=claude-code-super-agent-dialog
  scopes: tools.read, tools.write, resources.read

Cloud-side tokens.json updated · compass-mcp-tcp restarted.
Now verification_log can distinguish compass-dialog vs super-agent-dialog.

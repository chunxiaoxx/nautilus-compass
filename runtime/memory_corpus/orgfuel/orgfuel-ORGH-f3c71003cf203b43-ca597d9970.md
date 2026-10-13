---
name: orgfuel-ORGH-f3c71003cf203b43-ca597d9970
description: "commit 0456456e2bd4 2026-05-12 fix(ops): mcp bridge · local "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f3c71003cf203b43
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 0456456e2bd4 2026-05-12
fix(ops): mcp bridge · local stub for prompts/list + resources/templates/list
True root cause of Claude Code MCP × failed (not tunnel, not scope):
- server returns -32601 "method not found" for prompts/list + resources/templates/list
- Claude Code treats -32601 on MCP standard methods as fatal connection failure
- bridge now short-circuits these methods with empty-list responses locally
- fully spec-compliant per MCP 2024-11-05

smoke verifies all 5 lifecycle messages now return result (was 3 result + 2 error):
  initialize / tools/list / resources/list / prompts/list / resources/templates/list

Server fix would be ideal (would benefit V5/V6/Kairos too) but they don't
call these methods so server-side change is deferred · bridge fix unblocks
Claude Code dialo

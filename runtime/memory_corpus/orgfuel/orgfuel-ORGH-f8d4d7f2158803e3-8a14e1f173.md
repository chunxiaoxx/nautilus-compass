---
name: orgfuel-ORGH-f8d4d7f2158803e3-8a14e1f173
description: "commit 9f7f80a7a3ad 2026-05-08 mcp_configs: ship the missing"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f8d4d7f2158803e3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9f7f80a7a3ad 2026-05-08
mcp_configs: ship the missing 3 (claude_code/continue_dev/zed) for v1.0 launch
v1.0 launch articles promise "6 clients, paste-ready". Only 3 configs
existed. Adding the missing 3 + updating the README so the promise is
real on launch day.

- claude_code.json   · ~/.claude.json or project .mcp.json
- continue_dev.json  · experimental.modelContextProtocolServers schema
- zed.json           · context_servers schema (Zed 0.150+)

README: "3 个 client" → "6 个 client" · table reordered Claude Code first
since it's the primary OSS install path.

All 6 JSONs validated. compass-mcp binary path unchanged. user_id
placeholder convention preserved.

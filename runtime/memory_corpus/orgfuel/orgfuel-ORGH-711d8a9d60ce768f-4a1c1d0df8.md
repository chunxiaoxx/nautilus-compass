---
name: orgfuel-ORGH-711d8a9d60ce768f-4a1c1d0df8
description: "commit 7f6c8822f3e8 2026-05-09 fix(ci): commit untracked pro"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-711d8a9d60ce768f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 7f6c8822f3e8 2026-05-09
fix(ci): commit untracked production modules + tests · lint cleanup
Three production modules referenced by demos and tests were never tracked:
mcp_client.py (343 LOC, MCP client with auto-reconnect · Task #46), merkle_chain.py
(362 LOC, tamper-evident audit · Task #31), compass_verify.py (115 LOC,
slash command · Task #62). Demos and CI jobs that import them were silently
broken on every CI run since v1.0.

Three CI-referenced test files also untracked: tests/test_mcp_server.py,
test_a2a_adapter.py, test_merkle_chain.py · v10-protocol-tests job was
failing with "file or directory not found".

tests/test_compass_v09.py: relax exact-tool-set assertion to "no v0.9 tools
missing" so v1.0+ additions don't trip it.

ruff: 8 unused imports auto-fixed (output_drift, 

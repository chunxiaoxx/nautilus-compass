---
name: orgfuel-ORGH-dbfc0b5fc5b6924e-81f45f84ba
description: "commit e6a605209378 2026-05-09 fix(ci): V7 audit no-mem-dir "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-dbfc0b5fc5b6924e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit e6a605209378 2026-05-09
fix(ci): V7 audit no-mem-dir edge case + ship 2 untracked deps
- mcp_server.py · governance_audit no longer errs when memory dir absent
  (CI runner / fresh install) · returns audit_id with files_scanned=0 so
  output shape is unconditional. Demos and downstream tools can trust it.

- scripts/mcp_smoke_rpc.py · referenced by tests/test_mcp_server.py
  (smoke_keepalive_succeeds_against_live_server + dies tests). Was untracked.

- sdk/a2a_adapter.py · adds DISCOVER_CAPABILITIES message type and
  capability entry · referenced by tests/test_a2a_adapter.py. Health-check
  + feature-detection use case.

---
name: orgfuel-ORGG-4dd69f2649d3e768-bc1b0f8237
description: "判读档判例 2026-06-24-durable-mcp-transport · Task 6: E2E no-mess"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-4dd69f2649d3e768
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-durable-mcp-transport · Task 6: E2E no-message-loss (the closed-loop proof)
## Task 6: E2E no-message-loss (the closed-loop proof)

**Files:**
- Test: `tests/mcp_durable/test_e2e_no_loss.py`

**Behaviour:** end-to-end — server (EventStore) + bridge (resume), inject a mid-stream socket drop while the server is emitting a burst of notifications, assert the Claude-Code-facing output is a complete contiguous sequence (0 lost, 0 duplicated). **This is the verification that "MCP 总断" is now durable, not just auto-recovered** — the thing v1.8 alone cannot pass.

**Acceptance:** Task 6 green = MCP durable loop closed. Then: bump CHANGELOG v2.3.0 with the durable-MCP entry (+ v1.8), deploy watchdog timer on box (gated), `git push origin v2.3.0` (PyPI · gated · user go).

---

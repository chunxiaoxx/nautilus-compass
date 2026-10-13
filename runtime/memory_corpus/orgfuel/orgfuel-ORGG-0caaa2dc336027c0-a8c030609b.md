---
name: orgfuel-ORGG-0caaa2dc336027c0-a8c030609b
description: "判读档判例 2026-06-24-durable-mcp-transport · Task 3: Last-Event-"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-0caaa2dc336027c0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-durable-mcp-transport · Task 3: Last-Event-ID resume handshake (server)
## Task 3: Last-Event-ID resume handshake (server)

**Files:**
- Modify: `mcp_server.py` (`_serve` initialize handling)
- Test: `tests/mcp_durable/test_resume_handshake.py`

**Behaviour:** `initialize` (or a reconnect) MAY carry `params.lastEventId`. On present:
- `replay = es.replay_since(lastEventId)`; if `None` → reply initialize with `result.resumed=false` (client must full-resync) ; else write each replayed frame then `resumed=true`.
- Absent → fresh session (today's behaviour · `resumed` omitted).

**TDD:** connect, capture frames + last `_eid`, drop, reconnect with `lastEventId=<that>`, assert the missed frames replay in order and `resumed=true`; reconnect with a stale id → `resumed=false` no cr

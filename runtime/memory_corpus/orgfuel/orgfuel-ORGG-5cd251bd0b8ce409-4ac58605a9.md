---
name: orgfuel-ORGG-5cd251bd0b8ce409-4ac58605a9
description: "判读档判例 2026-06-24-durable-mcp-transport · Task 2: Wire EventS"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5cd251bd0b8ce409
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-durable-mcp-transport · Task 2: Wire EventStore into the server outbound path
## Task 2: Wire EventStore into the server outbound path

**Files:**
- Modify: `mcp_server.py` (`_tcp_loop._serve` outbound writes + `handle_message` notification emit)
- Test: `tests/mcp_durable/test_server_tags_events.py`

**Approach:** Each connection owns an `EventStore`. Every outbound frame (response + notification) goes through a `send(frame)` helper that calls `es.append(frame)`, stamps `frame["_eid"]=id`, then writes. Replays bypass re-append. Keep stdio loop unchanged (single-process, no drop surface).

**TDD:** spin a `_tcp_loop` on an ephemeral port (reuse pattern in `tests/test_mcp_*`), connect, send `initialize` + a tool call, assert every server frame carries a strictly increasing 

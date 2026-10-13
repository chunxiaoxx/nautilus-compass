---
name: orgfuel-ORGG-13d3bae25f1d1416-2d7539a5e0
description: "判读档判例 2026-06-24-durable-mcp-transport · Task 4: Bridge inte"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-13d3bae25f1d1416
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-durable-mcp-transport · Task 4: Bridge integration (client replay)
## Task 4: Bridge integration (client replay)

**Files:**
- Modify: `ops/mcp_stdio_to_cloud.py` (CloudLink `:146` · `_cloud_to_out_pump` `:513`)
- Test: `tests/mcp_durable/test_bridge_resume.py`

**Behaviour:** CloudLink records the highest `_eid` seen from cloud→out. On reconnect, after replaying cached `initialize`, it sends `params.lastEventId=<highest>` so the server replays the gap. Strip `_eid` before forwarding to Claude Code stdout (internal field). Preserve v1.8 invariant: any failure → degrade to local-only, never crash, never block stdin.

**TDD:** fake cloud socket that drops after N frames; assert bridge reconnects, requests `lastEventId`, and Claude-Code-facing stdout sees a contiguous no-gap 

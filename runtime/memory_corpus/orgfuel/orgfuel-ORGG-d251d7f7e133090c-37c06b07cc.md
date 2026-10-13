---
name: orgfuel-ORGG-d251d7f7e133090c-37c06b07cc
description: "判读档判例 2026-06-24-durable-mcp-transport · Notes / discipline "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d251d7f7e133090c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-durable-mcp-transport · Notes / discipline
## Notes / discipline
- **measurement-first:** Task 6 is the real verification — don't claim "durable" until it passes (verification-before-completion). v1.8 alone fails Task 6 by design.
- **never-breaks-recall posture:** bridge changes keep v1.8's degrade-to-local-only invariant — durable resume is best-effort on top, never a new crash surface.
- **scope guard:** layers 3 (staggered health-check auto-evict) + 5 (agentgateway multiplexer) from research §A are OUT of this plan (heavier · defer) — this plan = layers 2 (EventStore/Last-Event-ID) + 4 (watchdog) = the durable core.
- Relates: memory `reference_architecture_fusion_research_20260623` §A · `gotcha_compass_mcp_bridge_no_reconnect_fixed_v18` (v1.8 root cause).

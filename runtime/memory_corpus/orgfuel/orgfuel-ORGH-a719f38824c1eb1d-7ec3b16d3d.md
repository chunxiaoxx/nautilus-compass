---
name: orgfuel-ORGH-a719f38824c1eb1d-7ec3b16d3d
description: "commit 69ce42dd3570 2026-05-08 docs+demo: README §Platform i"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a719f38824c1eb1d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 69ce42dd3570 2026-05-08
docs+demo: README §Platform integration · examples/platform_flywheel_demo.py
(d) README new section "Platform integration · BP1 + BP3 contract":
- 2-row tool table covering submit_platform_task / ingest_platform_task_result
- 1-line direction + storage-mode-on/off-by-env summary per row
- runnable demo invocation with annotated 5-step trace
- pointer to handshake doc §7 for the full wire spec

(e) examples/platform_flywheel_demo.py · 235 lines · plays both halves:
- spawns mcp_server on a free TCP port (no daemon dependency)
- step 1 · MCPClient as compass-dialog · submit_platform_task
- step 2 · raw filesystem read of _platform_queue/<id>.json + status flip
- step 3 · simulate platform agent (fabricates channel URLs)
- step 4 · MCPClient as platform-agent · 

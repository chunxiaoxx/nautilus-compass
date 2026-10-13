---
name: orgfuel-ORGH-996c9acbe33240b9-390b4bd725
description: "commit 210e05c7f73e 2026-05-09 ci: relax MCP smoke from "exa"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-996c9acbe33240b9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 210e05c7f73e 2026-05-09
ci: relax MCP smoke from "exactly 7 tools" to "all 7 stable + extras OK"
CI was hardcoded to assert len(tools) == 7 from the v0.9 era. v1.0
added long_task (notifications/progress demo) and v1.0+ added the
two BP1/BP3 flywheel stubs (submit_platform_task /
ingest_platform_task_result), so the count is now 10. The fixed-
count assertion was failing on every push since bba08db.

Switch to a stable-set check: assert the 7 v0.9 tools are all
present, allow any number of extras. Future tool additions don't
break CI; missing core tools still fail loud.

Job name updated v0.9 → v1.0 for accuracy.

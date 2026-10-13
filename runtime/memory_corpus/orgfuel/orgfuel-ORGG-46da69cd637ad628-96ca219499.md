---
name: orgfuel-ORGG-46da69cd637ad628-96ca219499
description: "判读档判例 2026-06-04-poi-writer-role-tightening-design · 3. Secr"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-46da69cd637ad628
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-04-poi-writer-role-tightening-design · 3. Secret provisioning (user-provided)
## 3. Secret provisioning (user-provided)

- New file `~/.claude/plugins/nautilus-compass/.cache/.poi_writer_db_secret`,
  same `key: value` format as `.soul_db_secret` (`password: xxx`; host/port/
  dbname optional, default-inherited from the soul secret / module defaults).
- New env `COMPASS_POI_WRITER_SECRET` (defaults to the path above); reuses
  `parse_secret`.
- **Missing file = honest skip** (same as the current no-secret behavior) — not
  an error. This keeps hosts without the writer credential from crashing.

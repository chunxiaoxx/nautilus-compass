---
name: orgfuel-ORGG-24ddd3117010da74-072e39fb56
description: "判读档判例 2026-06-04-poi-writer-role-tightening-design · Files t"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-24ddd3117010da74
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-04-poi-writer-role-tightening-design · Files touched (anticipated)
## Files touched (anticipated)

- `sql/005_poi_writer_role.sql` (new, additive)
- `sql/006_poi_writer_revoke_compass_sub.sql` (new, run after e2e verify)
- `ops/cross_agent_outcome_poller.py` (refactor db_connection → tunnel + connect)
- `ops/poi_reconcile_cron.py` (two-connection reconcile; poi_writer secret load)
- `tests/test_poi_reconcile_cron_roles.py` (new)

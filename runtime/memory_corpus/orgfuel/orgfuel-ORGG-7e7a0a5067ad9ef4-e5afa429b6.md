---
name: orgfuel-ORGG-7e7a0a5067ad9ef4-e5afa429b6
description: "判读档判例 2026-06-03-p5-v14-poi-emission · Task 6: Reconciler dr"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-7e7a0a5067ad9ef4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission · Task 6: Reconciler dry-run verify + schedule (@verification-before-completion)
## Task 6: Reconciler dry-run verify + schedule (@verification-before-completion)

**Step 1: Pick a python with psycopg2 + run the pull against cloud**

```bash
py -3 -c "import psycopg2; print('psycopg2 ok')"   # if fails, find the venv that has it
py -3 ops/pull_cloud_candidates.py
```
Expected: "pulled N cloud lines · +K new" (N>0 once Task 3 e2e left a test candidate).

**Step 2: Dry-run reconcile (no settle expected — actor=test/unknown ≠ platform agent)**

```bash
set COMPASS_POI_CACHE_DIR=%USERPROFILE%\.claude\plugins\nautilus-compass\.cache
set COMPASS_POI_MEMORY_ROOT=%USERPROFILE%\.claude\projects\C--Users-chunx\memory
py -3 ops/poi_reconcile_cron.py --dry-run
```


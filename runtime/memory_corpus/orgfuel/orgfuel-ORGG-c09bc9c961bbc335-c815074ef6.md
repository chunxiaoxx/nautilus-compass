---
name: orgfuel-ORGG-c09bc9c961bbc335-c815074ef6
description: "判读档判例 2026-06-03-p5-v14-poi-emission · Task 2: Patch script "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c09bc9c961bbc335
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission · Task 2: Patch script body (idempotent 3-edit injection) + test
## Task 2: Patch script body (idempotent 3-edit injection) + test

**Files:**
- Modify: `ops/patch_v14_recall_poi_candidate.py` (add `main()` + edit logic below `EMIT_HELPER`)
- Test: `tests/test_v14_poi_emission_patch.py` (add patch-application tests)

**Step 1: Write the failing test** (append to the test file)

```python
# ---- patch application (against a synthetic copy of the live route) -----------

_LIVE_ROUTE = '''import os
from typing import Optional
from fastapi import Header

@app.get("/v1/v14/recall")
def v14_recall(
    q: str,
    top_k: int = 5,
    scope: str = "project",
    project: Optional[str] = None,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),


---
name: orgfuel-ORGG-8ea205b020cc8728-cb687dc0e2
description: "判读档判例 2026-06-03-p5-v14-poi-emission · Task 4: Local pull de"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-8ea205b020cc8728
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission · Task 4: Local pull dedup-merge pure function + test (TDD)
## Task 4: Local pull dedup-merge pure function + test (TDD)

**Files:**
- Create: `ops/pull_cloud_candidates.py` (pure `merge_candidate_lines` only this task)
- Test: `tests/test_pull_cloud_candidates.py`

**Step 1: Write the failing test**

```python
from __future__ import annotations
from pathlib import Path
import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "pull_cloud", Path(__file__).resolve().parent.parent / "ops" / "pull_cloud_candidates.py")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def test_merge_dedups_exact_lines():
    existing = ['{"a":1}', '{"b":2}']
    incoming = ['{"b":2}', '{"c":3}']
    out = _MOD.merge_candidate_l

---
name: orgfuel-ORGG-d7a9e43df51d7996-8532fd1bde
description: "判读档判例 2026-06-03-poi-central-ledger-implementation · Task 3:"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d7a9e43df51d7996
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-implementation · Task 3: `boost_top_k` 读快照 + NaN/clamp 兜底
## Task 3: `boost_top_k` 读快照 + NaN/clamp 兜底

横切 P0-2。boost 改成先查快照 dict(key 由 entry 路径派生),miss 回退 frontmatter,NaN/inf 兜底裸 cosine。

**Files:**
- Modify: `recall_pkg/poi_weighting.py`
- Test: `tests/test_poi_weighting_snapshot.py`

**Step 1: 写失败测试**

```python
# tests/test_poi_weighting_snapshot.py
import math
from recall_pkg.poi_weighting import apply_poi_boost_value, boost_top_k_with_snapshot

def test_apply_value_basic():
    # cumulative=5 → boost=clamp(0.5)=0.5 → 0.8*1.5=1.2
    assert round(apply_poi_boost_value(0.8, 5.0), 4) == 1.2

def test_apply_value_clamp_cap():
    # cumulative=100 → boost capped at +1.0 → 0.5*2.0=1.0
    assert round(apply_poi_boost_value(0.5, 100.0), 4) == 1.0

def test

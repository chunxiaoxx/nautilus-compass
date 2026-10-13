---
name: orgfuel-ORGG-c03d69f2ade55571-2132755a1f
description: "判读档判例 2026-06-22-compass-v2.3.0-release · Task 3: GEP P3 — 客"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c03d69f2ade55571
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-compass-v2.3.0-release · Task 3: GEP P3 — 客户端 PoI 重排(复用 poi_calculator·serving 不改)
## Task 3: GEP P3 — 客户端 PoI 重排(复用 poi_calculator·serving 不改)

**背景**:路 B 的 `proof/poi_calculator.compute_impact_score` + `tier_promotion.calculate_new_tier` 已造好但只作用 .md 文件。GEP P3 把它接到飞轮召回:`compass_recall_pits` 返回的 hits 用 impact_score 重排(质量进化)。**客户端后处理·serving 不动**(serving 改 = 部署 gate,避开)。

**Files:**
- Create: `gep/__init__.py`
- Create: `gep/poi_rerank.py`
- Test: `tests/gep/test_poi_rerank.py`

**Step 1: 写失败测试 — impact 重排**

```python
def test_rerank_hits_by_impact_then_reward():
    hits = [
        {"item_id": "a", "reason": "low impact", "reward": 1.0, "cumulative_impact": 0.1},
        {"item_id": "b", "reason": "high impact", "reward": 1.0, "cumulative_impact": 0.9},
    ]
    out = r

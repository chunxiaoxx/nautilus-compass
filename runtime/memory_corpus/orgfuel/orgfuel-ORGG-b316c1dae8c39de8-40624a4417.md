---
name: orgfuel-ORGG-b316c1dae8c39de8-40624a4417
description: "判读档判例 2026-06-22-compass-v2.3.0-release · Task 2: OKF 校验器 + "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b316c1dae8c39de8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-compass-v2.3.0-release · Task 2: OKF 校验器 + round-trip(绑真实消费者·护栏 #1)
## Task 2: OKF 校验器 + round-trip(绑真实消费者·护栏 #1)

**Files:**
- Create: `okf/validator.py`
- Test: `tests/okf/test_validator.py`

**Step 1: 写失败测试 — 校验 type 必需 + 链接完整**

```python
def test_validate_flags_missing_type():
    bundle = {"concepts": [{"name": "x", "description": "no type"}], "link_graph": {}, "backlinks": {}}
    errs = validate_okf_bundle(bundle)
    assert any("type" in e for e in errs)

def test_validate_flags_dangling_link():
    bundle = {"concepts": [{"name": "a", "type": "project"}],
              "link_graph": {"a": ["ghost"]}, "backlinks": {}}
    errs = validate_okf_bundle(bundle)
    assert any("ghost" in e for e in errs)   # 指向不存在的 concept
```

**Step 2-4: 实现 `validate_okf_bundle(bundle

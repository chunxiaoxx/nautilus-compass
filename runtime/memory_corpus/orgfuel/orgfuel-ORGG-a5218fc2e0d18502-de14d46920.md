---
name: orgfuel-ORGG-a5218fc2e0d18502-de14d46920
description: "判读档判例 2026-06-22-compass-v2.3.0-release · Task 6: GEP P1/P2 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a5218fc2e0d18502
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-compass-v2.3.0-release · Task 6: GEP P1/P2 预备态(compass 侧 schema·护栏 #2)
## Task 6: GEP P1/P2 预备态(compass 侧 schema·护栏 #2)

> **GEP 复用决策 = B(用户 2026-06-22 拍)**:开源 evolver = Node CLI / GPL-3.0(`github.com/EvoMap/evolver`)·**不能 pip import**。复用方式 = **按开源 GEP 协议规范在 Python 实现**:对齐其 Gene/Capsule/Event 数据模型 + 生命周期 spec(字段命名/语义对齐开源)·**不碰 GPL 代码**·栈一致·license 干净。不重新发明协议,也不引 Node 运行时进生产 serving。

**Files:**
- Create: `gep/capsule_schema.py`(结构化字段 dataclass + 校验·对齐开源 GEP Capsule 模型)
- Test: `tests/gep/test_capsule_schema.py`

**Step 1: 写失败测试 — 结构化胶囊字段**

```python
def test_capsule_with_boundary_fields():
    c = StructuredCapsule(learning="do X", triggers=["when Y"],
                          env_fingerprint="py3.11", confidence=0.8,
                          when_not_to_use=["if Z"])
 

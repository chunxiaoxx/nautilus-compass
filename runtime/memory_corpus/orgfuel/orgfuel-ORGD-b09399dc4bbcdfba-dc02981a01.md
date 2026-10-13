---
name: orgfuel-ORGD-b09399dc4bbcdfba-dc02981a01
description: "[## 3. claim schema] - `level`: **L1** = 无需验证方环境即可复算;**L2** "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-b09399dc4bbcdfba
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 3. claim schema] - `level`: **L1** = 无需验证方环境即可复算;**L2** = 需环境(如 QC),缺环境时跑 `fallback`(通常是包内一致性核对),verdict 记 `degraded`。
- `checks.primary.fallback` 的结构 = check 对象(§4)。`level=L1` 可只写 `checks`(等价 primary)。

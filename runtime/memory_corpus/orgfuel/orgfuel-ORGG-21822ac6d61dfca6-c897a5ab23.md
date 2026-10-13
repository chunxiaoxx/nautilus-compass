---
name: orgfuel-ORGG-21822ac6d61dfca6-c897a5ab23
description: "判读档判例 ASSAY_BC1_item_framework_v0 · 二 · 生成与判分管线 ## 二 · 生成与判分"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-21822ac6d61dfca6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 ASSAY_BC1_item_framework_v0 · 二 · 生成与判分管线
## 二 · 生成与判分管线

1. 生成器:`tools/assay_items/gen_bc1.py`(读种子参数表 → 出题面 json+期望答案)
2. 编译:每题 → VerifyPack claim(checks.primary 显式 kind+参数)
3. 判分:三态+签名回执,同首考管线;**判据引用随题编译**(criteria_ref 进语料)
4. 切分:`seed_split 60/40`,40% hold-out 永不入自测

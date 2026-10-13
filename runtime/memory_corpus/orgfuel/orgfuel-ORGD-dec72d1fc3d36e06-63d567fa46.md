---
name: orgfuel-ORGD-dec72d1fc3d36e06-63d567fa46
description: "[## 我方四条验证判据(冻结)] | # | 判据 | 通过线 | 测法 | |---|---|---|---| | "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-dec72d1fc3d36e06
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 我方四条验证判据(冻结)] | # | 判据 | 通过线 | 测法 |
|---|---|---|---|
| V1 | build 产物可复算性 | 首批每条含:problem 坐标+变体坐标+判据声明;锚引用只指向**历史合格批**(anchor-pool-selection-bias-v1),不引用未验证剩余池 | 逐条核对 pack.json 结构 |
| V2 | 三态管线实弹 | VerifyPack verify 对首批跑通,读数落 agree/disagree/not_computable 三态(T1 定案枚举的真实首用);v0.2 四态兼容映射正确 | `python -m tools.verifypack verify <pack>` |
| V3 | 双向记账 | 校准读数回填 CATALOG_v0(C 族条目,criteria:<id>@catalog-v0 格式),trace 双向(我档↔flywheel 归因/校准档) | 文件核对 |
| V4 | 回执收尾 | ed25519 签名 receipt 出具;首行 VERDICT 格式 | `python -m tools.verifypack receipt/check` |

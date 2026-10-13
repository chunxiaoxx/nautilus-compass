---
name: orgfuel-ORGD-fb065f17497d0a2a-36cf55ed85
description: "[## 6. seal 语义(manifest)] - build:写完全部内容后生成 `manifest.json` "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-fb065f17497d0a2a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 6. seal 语义(manifest)] - build:写完全部内容后生成 `manifest.json` = {path: sha256}(覆盖 pack.json、payload/、repro/;不含 manifest.json 自身与 receipts/)。外部 inputs 记录 `{declared_path: sha256}` 于 `manifest.inputs`。
- verify 第一步:重算全部哈希。任何不符 → 所有 claims verdict= `seal_fail`,结果中指名被改文件,**不继续复算**。
- 语义:pack 是**不可变快照**。verify 通过 = 「build 时刻的这批字节,在这些判据下得出这些结论」。

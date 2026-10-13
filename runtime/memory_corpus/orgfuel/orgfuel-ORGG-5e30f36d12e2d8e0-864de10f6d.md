---
name: orgfuel-ORGG-5e30f36d12e2d8e0-864de10f6d
description: "判读档判例 E1_FAILURE_ATTRIBUTION_20261009 · 四、E1-TUNE v1 预注册判据(建"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5e30f36d12e2d8e0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 E1_FAILURE_ATTRIBUTION_20261009 · 四、E1-TUNE v1 预注册判据(建议稿,判据只许更严)
## 四、E1-TUNE v1 预注册判据(建议稿,判据只许更严)

- **口径**:干净工作集(生成器 v2 重生成,人工抽检零污染)
- **基线**:R@1=0.4000(本轮干净集实测同值)
- **过门**:R@1 ≥ 0.60 **且** R@5 ≥ 0.80 **且** bge-m3 底座不动(换模型另走对拍)
- **负结果照报**:任一假设单独归因(H1/H2 分开测),不做混合归因

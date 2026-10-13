---
name: orgfuel-ORGG-fcd4f5e875e39e5d-cec87228e9
description: "判读档判例 SEVENB_COMPARE_PREREG_20261008 · 预注册判据(冻结,2026-10-08) "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fcd4f5e875e39e5d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 SEVENB_COMPARE_PREREG_20261008 · 预注册判据(冻结,2026-10-08)
## 预注册判据(冻结,2026-10-08)

| 门 | 判据 | 口径 |
|---|---|---|
| **G1 主门·升级线** | 候选三元 acc 比冠军高 ≥2.0pp(绝对) | 同一 held-out 集(触发时从池内切分,qid 防泄漏;禁用任何训练内题) |
| **G2 三门复验** | J1/J2/J7 全绿(沿用 P2v2 三门定义) | 判据档=runtime/judge_lora_p2v2 现役门 |
| **G3 精度门** | bf16 对 bf16 一致率基线+fp16 一致率 ≥99%(PRECOR 纪律) | 291 案现行 held-out 复用 |
| **G4 稳健门** | int8 一致率披露(不设过门,数据留档) | 观察项,防止逐档降门槛 |

**升级裁定**:G1+G2+G3 全过 → 7B 升格现役(1.7B 转轻量线保留);任一未过 → 1.7B 维持现役,负结果照报+归因段(数据量/配方/切分三归因)。
**禁改条款**:G1 的 2.0pp 与 G3 的 99% 在数据出数后不得放宽;如需加严只许收紧。

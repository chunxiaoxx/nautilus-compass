---
name: orgfuel-ORGG-0cf87f3b55d9ddf5-ee377723c7
description: "判读档判例 2026-09-22-assay-head-charter · 二 · 反自指护栏(五红线,违一条即停) #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-0cf87f3b55d9ddf5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-22-assay-head-charter · 二 · 反自指护栏(五红线,违一条即停)
## 二 · 反自指护栏(五红线,违一条即停)

1. **只训小判分器**(≤1B 参数),不训生成模型,不训与被测 agent 同代的模型
2. **训练数据全带签名出处**(verdict 语料经 VerifyPack 导出器,行级 criteria_ref)
3. **Assay-Head 自己的校准用我们的判据验**(calibration-claim-verify-v1)——
   裁判被判,递归信任
4. **语料门槛 ≥2,000 行 verdict**+M2 后才启动正式训练(当前 ~400 行,先做
   zero-shot baseline)
5. **不可用 Assay-Head 判定 Assay-Head 自己的输出**(禁止直接自评;独立校准
   集必须外部)

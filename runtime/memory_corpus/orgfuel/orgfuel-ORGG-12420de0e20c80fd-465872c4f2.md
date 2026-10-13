---
name: orgfuel-ORGG-12420de0e20c80fd-465872c4f2
description: "判读档判例 A2V4_ANCHOR_RETRIEVAL_PREREG_20261002 · 判据(预注册,只许加严) #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-12420de0e20c80fd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 A2V4_ANCHOR_RETRIEVAL_PREREG_20261002 · 判据(预注册,只许加严)
## 判据(预注册,只许加严)

| # | 判据 | 门槛 | 说明 |
|---|---|---|---|
| R1 | 编码覆盖 | 两侧 1454+1454 零失败 | 诚实门 |
| R2 | **因果桥存在** | hit@5(真 query)≥ max(5×随机期望, 3×shuffled-query 基线) | 随机≈1/1453;shuffled=用他人 reason 查,测"语义桥不存在时"的地板 |
| R3 | 头增量(副读数) | 马氏白化 vs 余弦直连同报,增量不作门 | lite 头已证天花板,不重蹈 |
| R4 | 可达性预检 | 门槛上限 ≤90%(5×1/1453≈0.3%,3×shuffled 待实测) | 防 A2v2 数学不可达复发 |

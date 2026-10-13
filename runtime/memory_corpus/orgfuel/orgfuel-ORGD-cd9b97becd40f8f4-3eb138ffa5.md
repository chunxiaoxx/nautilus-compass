---
name: orgfuel-ORGD-cd9b97becd40f8f4-3eb138ffa5
description: "[### L2 · 材料锚定层] - 材料交付时即取逐件指纹(rows_sha16 / ckpt_sha16 / man"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-cd9b97becd40f8f4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### L2 · 材料锚定层] - 材料交付时即取逐件指纹(rows_sha16 / ckpt_sha16 / manifest_sha16),verdict 只引用指纹,不引用"对方说的那份文件"。
- 验签:交卷包(如 E1 双包)按映射表 sha16 验签后才开工(sha 不合=材料未达,判读不启)。
- 交付后材料不可变;要改就是新材料新指纹新判读,旧判读不追溯(案 7 追溯边界)。

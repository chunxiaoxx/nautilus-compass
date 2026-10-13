---
name: orgfuel-ORGG-ad83e9c4e667f867-e997833a0c
description: "判读档判例 P2V2_LORA_PLAN_20260930 · 一 · GPU 现状(2026-09-30 16:38 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ad83e9c4e667f867
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P2V2_LORA_PLAN_20260930 · 一 · GPU 现状(2026-09-30 16:38 实查)
## 一 · GPU 现状(2026-09-30 16:38 实查)

- 余额:PowerMoney=**1.9051**(4090 实价 1.65/h,QLoRA 窗口 2-3h=¥3.3-5 → 不够)
- **保留盘快照在**:46 实例含 copy `18510625230_lyg0164_5166ed68..._u1_c9`
  (9/3 老盘全套环境:torch cu124+transformers 5.2.0+repo)——从该 copy 开新实例,
  按保留盘纪律环境秒就位,零重部署
- 开租:GPU_EVAL_RECIPE_4090.md 配方 + gpu_4090.md CLI(rent 带 copy 参数)

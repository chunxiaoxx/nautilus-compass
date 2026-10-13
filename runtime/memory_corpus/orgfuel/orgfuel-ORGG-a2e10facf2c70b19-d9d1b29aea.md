---
name: orgfuel-ORGG-a2e10facf2c70b19-d9d1b29aea
description: "判读档判例 2026-09-16-c-family-calib-preregistered · 运行记录与披露 ## 运"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a2e10facf2c70b19
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-16-c-family-calib-preregistered · 运行记录与披露
## 运行记录与披露

- `verify --verifier compass` → 6/6 agree;回执落 pack 内 receipts/receipt.json
  +receipt.sig(ed25519,公钥 f7554b87…3e8be);`check` 全链 ok:true。
- **披露一(独立面)**:本 verify 会话开工前已读到 flywheel 入站函所载自检
  "6/6 agree"表述,复算有暴露面;三态判定与逐条数值均为本地按 checks 重算,
  非转抄。
- **披露二(回执覆盖)**:verify 把 compass 回执写入 pack 的 receipts/
  receipt.json;本仓首次 ls(verify 前)该路径已存在 receipt.json——若为构建
  方自检回执,已被覆盖。pack 与 manifest 未动一字,构建方可随时用同一 pack
  重出自检回执;如需回执改放旁路路径,回函即改。

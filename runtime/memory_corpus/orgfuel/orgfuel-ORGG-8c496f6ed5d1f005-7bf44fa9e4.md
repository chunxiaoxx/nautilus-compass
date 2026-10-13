---
name: orgfuel-ORGG-8c496f6ed5d1f005-7bf44fa9e4
description: "判读档判例 HANDOFF_20260917_cfamily_verify · 任务一 · C 族首批校准(V1-V4)"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-8c496f6ed5d1f005
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 HANDOFF_20260917_cfamily_verify · 任务一 · C 族首批校准(V1-V4)
## 任务一 · C 族首批校准(V1-V4)

- **pack**:`C:\Users\chunx\Projects\nautilusflywheel\runtime\verifypack\c_family_calib_b1`
  (sealed,manifest 在;build 方=flywheel,验证方=compass)
- **claims 清单与 C 族定义**:入站函 `_INBOUND_FROM_FLYWHEEL_20260916_c_family_b1_built.md`
  (仓根;6 条 C0-C4b)
- **verify**:`python -m tools.verifypack verify <pack 路径> --verifier compass`
- **check / receipt**:`python -m tools.verifypack check|receipt`(密钥 `.verifypack/`,
  公钥 f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be)
- V1 逐条核对 pack.json 锚引用(只指向历史合格批,不引用未验证剩余池)
- 读数回填预注册档空白区 → 签名回执 → 函告 flywheel
  (POST 信箱,trace=`flywheel-c-family-b1-built-20260916`)

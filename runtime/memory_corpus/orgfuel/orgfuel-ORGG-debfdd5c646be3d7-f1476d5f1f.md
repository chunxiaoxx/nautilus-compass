---
name: orgfuel-ORGG-debfdd5c646be3d7-f1476d5f1f
description: "判读档判例 A2_RECOMPUTE_VERDICT_20261007 · 二、差异模式(证据链) ## 二、差异模式("
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-debfdd5c646be3d7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 A2_RECOMPUTE_VERDICT_20261007 · 二、差异模式(证据链)
## 二、差异模式(证据链)

71 行差异**全部**为 2026-10-06 `auto-settle:fuel_trajectory` 行(delta=+10/行):
- drift 恒定 **+2/行**递增(68→142,累计 +142)——与 A1 裁定"幂等守卫名不匹配→重复释放"完全吻合:每笔结算重复多贷 2 NAU;
- 段起点之前(8095 前)已有既有累积(drift 起点 68),即重复释放自更早开始,8095-8191 为持续段;
- reason 分布:score 0.70-1.00 全谱——与任务质量无关,纯写入侧缺陷。

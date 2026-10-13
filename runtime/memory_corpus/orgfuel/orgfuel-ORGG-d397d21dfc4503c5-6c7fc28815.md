---
name: orgfuel-ORGG-d397d21dfc4503c5-6c7fc28815
description: "判读档判例 S6_RECOMPUTE_FIDELITY_20261009 · 判读结果 ## 判读结果  **复算保真度"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d397d21dfc4503c5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 S6_RECOMPUTE_FIDELITY_20261009 · 判读结果
## 判读结果

**复算保真度门:PASS(29/30 逐例四桶一致)**

| 桶 | 原跑(三报告) | 复算(15 批) | 判 |
|---|---|---|---|
| resolved | 9 | 9 | ✓ |
| unresolved | 5 | 5 | ✓ |
| error | 16(含跨段重复计) | 14 | ✓(重复计入差) |
| empty_patch | 2 | 2 | ✓ |

**唯一漂移**:django__django-16560 原跑 error → 复算 resolved。方向判读:漂移方向与 Round1 判读层修复口径一致(判读层对格式失败例 reapply 修复后归 resolved 的先例,sphinx-8475 同型 SAME);该例 precise 归因(原跑 error 的具体格式缺陷 vs 复算环境差异)留正式判读卡核,不阻塞保真度判定。

**证据层**:全量四桶读数=[实测](15 份报告文件 /data/s6_rerun/runs/);对照=[实测](三报告逐例);16560 判读层历史=[推断](待判读卡核);复算环境=cloud swebench 5.0.2+分批镜像(判据 sha 不变)。

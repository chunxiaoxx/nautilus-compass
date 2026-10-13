---
name: orgfuel-ORGD-977396cdaabedbe5-b75a43b24d
description: "[## 5. 修复建议(3 条,全部已实测验收)] | # | 建议 | 验收判据 | 状态 | |---|---|--"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-977396cdaabedbe5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 5. 修复建议(3 条,全部已实测验收)] | # | 建议 | 验收判据 | 状态 |
|---|---|---|---|
| ① | 帧过滤 ‖act−state‖ ≥ 1e-3(阈值参考 #2413:按数据集分布取 P50 量级以上) | 修复批逐帧 filter 达标 | ✅ B 臂修复批实测生效 |
| ② | dir 一致率改 sign 语义(0/1 混合→纯 sign) | 修复批 dir 0/1 混合消除 | ✅ 同上 |
| ③ | 帧集钉死 40 帧=5 eps×8 | 双臂同 5 eps 配对,act_state_norm min/max 完全相同 | ✅ 实测一致(7.22e-2~1.13e-1) |

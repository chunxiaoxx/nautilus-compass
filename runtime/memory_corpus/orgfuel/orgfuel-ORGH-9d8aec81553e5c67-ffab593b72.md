---
name: orgfuel-ORGH-9d8aec81553e5c67-ffab593b72
description: "工具决策记录 fuel_flywheel_vet.py R506 · flywheel 423 candidates 过"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9d8aec81553e5c67
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 fuel_flywheel_vet.py
R506 · flywheel 423 candidates 过 flywheel 红线 R1-R7 重筛(其审计件为正本判据)。

红线实现:
- R1/R2/R5: 港区投资/泄密审计/报价盘口/政府线方案件按文件名排除;
- R4: 谈判/intel 件按文件名排除;
- R6: PII 角色化(手机号/邮箱→占位);结算语义件按文件名排除;
- R7: runtime 仅取 git 跟踪清单内 + 白名单类名。

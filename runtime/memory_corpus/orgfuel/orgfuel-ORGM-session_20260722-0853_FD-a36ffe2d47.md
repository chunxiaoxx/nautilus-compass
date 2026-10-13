---
name: orgfuel-ORGM-session_20260722-0853_FD-a36ffe2d47
description: "--- name: FDE表单校准事件 description: V5 has source-bound expert "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-session_20260722-0853_FD
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: FDE表单校准事件
description: V5 has source-bound expert form blueprint; keep raw sources private and gate learning.
type: feature
concept: what-changed
drift: green
drift_signals: []
agent_type: codex
user_id: u_local
ingested_via: mcp
proof_of_recall: not_attempted
declaration_type: cascade
tier: semantic
decay_rate: 0.5
promote_after: 20_access
reinforce_count: 7
---

# FDE表单校准事件

## 上下文
V5 has source-bound expert form blueprint; keep raw sources private and gate learning.

## 内容
请消费 FDE/Feishu 校准事件：三份来源已由用户 OAuth 受控读取并哈希绑定。V5 已在提交 4d1d902 生成专家表单 blueprint：当前 24 个业务字段全保留，专家入口另补四项证据（附件来源与脱敏说明、最终产物附件、最终产物受控链接、本人确认与脱敏承诺）；内部 UID/QC/状态字段不外露。最终产物附件/链接二选一由内部 QC 检查。daily probe 对来源哈希变动 fail-closed；当前仅 schema_review_pending，未创建外部表、未写买方、未结算/训练。Compass 侧仅接收脱敏、哈希化、canonical verdict 后的 Gold/Repair

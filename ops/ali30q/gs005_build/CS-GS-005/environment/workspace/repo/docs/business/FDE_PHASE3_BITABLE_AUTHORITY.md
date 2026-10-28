# Phase 3 飞书多维表格权威状态机

> 当前实施基线。本文定义第三期垂域高难度题目与在线交互轨迹的业务权威、应用职责和
> 受控数据边界；不包含原始验收材料、账号、附件或凭据。

## 决定

飞书多维表格 Bitable read-back 是第三期所有任务状态、自动 P0、买方反馈、最终
`verdict`、返修血缘和导出回执的唯一权威来源。没有对应 Bitable 记录与 read-back 的
Agent 文字、截图、文件名、日志或本地状态，均不能构成任务完成、审核通过或闭环证据。

开发对话只用于研发和诊断，不能作为运行时输入、队列、状态或证据通道。

## 五张权威表与入口

| Bitable 表 | 身份锚 | 用途 | 外部写入方式 |
| --- | --- | --- | --- |
| `第三期专家` | 专家记录 | 专家档案、培训和开通状态 | `第三期专家信息采集（正式）` |
| `第三期题目预审` | 题目记录 | 题目、领域、附件、来源、交互思路与题目 P0 | `第三期题目预审（正式）` |
| `第三期交互成果` | 交互记录 | 豆包交互证据与交互 P0 | 导师续办页 |
| `第三期审核与反馈` | 审核记录 | P0、买方反馈、反馈类别与 `verdict` | Nautilus 受控写入 |
| `第三期导出与回执` | 导出记录 | 脱敏资格、V5 v3、Compass 回执 | Nautilus/Compass 受控写入 |

当前正式流程有两张原生公开表单，均允许持链接者提交但不授予 Base 查看权限。
`第三期交互成果` 必须由导师续办创建：外部专家不提供 Bitable 记录 ID、题目关联、专家
关联或 `revision_of`，关系由 Nautilus 根据会话范围和 Bitable read-back 受控建立。

## 状态机

```text
题目预审表单 -> precheck_pending -> precheck_running
  -> eligible_for_interaction -> 导师续办 -> interaction_draft -> interaction_qc_running
  -> question_repair_required -> 题目返修续办
  -> blocked

交互自动 P0 -> buyer_ready | repair_required | blocked
买方反馈 -> buyer_accepted | buyer_rejected | 需返修
买方接受 + 脱敏资格 -> 待导出 -> V5 v3 -> Compass 回执
```

- `eligible_for_interaction` 只是题目可进入交互阶段，不是买方通过。
- `buyer_ready` 只是交互材料可进入买方队列，不是买方通过。
- `Repair` 只来自带完整 `revision_of` 血缘且后续被买方接受的记录；首次接受可为 `Gold`，
  明确拒绝可为 `Reject`。
- `question_repair_required` 和 `repair_required` 都必须保留前序记录，并创建后继记录；
  不覆盖原记录。

## 应用职责

| 责任方 | 允许动作 | 不允许动作 |
| --- | --- | --- |
| 飞书原生表单 | 创建专家或题目预审初始记录 | 决定 P0、买方结果或导出资格 |
| 智涌 Nautilus | read-back、自动 P0、受控写回、幂等、反馈归一化、导师投影、导出回执写回 | 替代买方、绕过 read-back、维护平行账本 |
| 智涌导师 | 培训、状态查询、题目/交互返修陪跑、受认证续办 | 直接读写 Base、查看他人或原始买方材料 |
| Core / FDE | 状态机、字段映射审批、表单入口、受控写回门 | 创建第二套业务账本 |
| V5 | 消费符合资格的签名脱敏投影并产出 v3 | 读取 Base、原始材料或写业务状态 |
| Compass | 独立校验 v3 并返回签名回执 | 改写买方结果或返修血缘 |

## 事件、幂等与隐私

正式事件是 `question_created`、`question_precheck_completed`、`interaction_submitted`、
`qc_completed`、`repair_required`、`buyer_feedback_recorded` 和 `compass_receipt_recorded`。
幂等键由 `route + record_id + record_version` 派生；每次受控写入后必须再次 read-back。

导师只收到专家范围句柄、脱敏原因码、下一步、知识包版本与不透明续办引用。V5/Compass
只收到签名脱敏投影。个人资料、原始附件/对话、分享链接、买方原文、Base 标识和 Bitable
记录标识不能跨出受控边界。

## 上线门

本地代码与文档契约不等于线上启用。Base 五表、两张原生公开表单、应用权限、事件订阅、
消息卡片、自动化扩展、持久幂等存储、导师会话绑定和失败日志，都必须逐项 read-back。
在一条授权、脱敏演练完整通过前，不开启买方同步、V5 正式导出、Compass 导入或自动结算。

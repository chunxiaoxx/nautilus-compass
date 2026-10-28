# Phase 3 首条 V5 到 Compass 记录门槛

## 目的与范围

本文件只定义第一条经授权的 V5 到 Compass 记录如何被独立核验。它不是招聘、
培训、结算或批量运营手册，也不包含原始对话、附件、截图、账号信息、买方身份
或链接。

截至本文落库时，这是一套待执行的门槛定义，不代表已完成一条真实闭环。

## P0: 互动过程是否成立

V5 内部账本必须为该记录保留受控引用，并产生仅含哈希的导出事件。导出前必须
同时满足：

- `turn_count >= 6`
- `interaction_deadline_met = true`
- `trajectory_coherence = pass`
- `p0_status = pass`
- `redaction_status = verified`

任一条件不满足时，记录不得进入 Compass，也不得进入结算或复用队列。

## 最终判定与反馈分类

Compass canonical envelope 必须通过 schema 校验，并同时具备：

- `verification_state = canonical_verified`
- `candidate_state = closed`
- `verdict` 为 `Gold`、`Repair` 或 `Reject`
- `feedback_class` 为 `none`、`accepted_advisory`、`revision_required` 或
  `rejection_reason`
- `admission` 为受控准入状态

`buyer_status`、`feedback_class` 与 `verdict` 的业务含义由独立核验人复核：通过
且未主张返修的结果可以判为 `Gold`；只有完成一条已登记返修后的通过结果可以判为
`Repair`；明确拒绝可以判为 `Reject`。P0 通过但没有最终判定，仍属于阻断状态。

## 返修血缘

返修在 V5 内部账本保留 `revision_of`，将本次记录绑定到其直接前序版本。该字段
不进入当前 Compass v3 canonical envelope；独立核验只比对受控的前序、反馈与新
版本证据哈希，并记录血缘是否完整。不得以原始反馈文字、截图或外部链接代替该
核验。

在内部账本未完成血缘核验前，不得赋予 `Repair`。一条返修请求本身只是
`repair_required`，不是最终判定。

## 首条记录的独立核验步骤

1. V5 生成并签名一条经脱敏的 `fde.compass.envelope.v3` JSONL 事件及其 manifest。
2. 核验人确认 P0、最终判定、反馈分类和返修血缘，并只记录受控字段与哈希。
3. Compass 先做无写入 schema/manifest 与 V5 签名校验；未通过时输出 `blocked_*` 原因。
4. 通过后才执行一次受控导入，并读取回写出的 capsule，核对 `task_id`、`event_id`、
   `payload_hash` 和 `manifest_hash`；回执本身必须可验签并以导出记录的幂等键回写。
5. 只有上述五项均完成，才可以将该记录称为首条已闭环记录。

当前旧 S3 交付通道对 `workflow_version=phase3_interactive_v1` 保持 fail-closed；它
不是本闭环的导出、交付或结算通道。

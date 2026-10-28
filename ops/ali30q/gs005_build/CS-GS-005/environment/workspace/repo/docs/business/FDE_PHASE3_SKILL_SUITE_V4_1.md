# FDE Phase 3 Skill Suite v4.1

> **历史版本，不作为当前运行入口。** 它保留当时采用单表流程的目标、边界和验证记录；
> 当前执行口径见 [FDE Phase 3 Skill Suite v5](FDE_PHASE3_SKILL_SUITE_V5.md)。
> `ecc-fde-external` 已确认属于二期遗留；下文相关行仅保留历史证据，第三期运行时、培训和
> 对外文案均禁止加载。

> v4.1 是 v4 的第三期运行补丁，不删除历史资产。v4 继续保存通用 Evidence Pack、
> 任务设计、历史 QC、Yao meta 接口与兼容工具；v4.1 只为当前在线交互项目设定更严格的
> 路由和应用边界。

## 唯一入口与角色

| 组件 | 当前职责 | 不做什么 |
| --- | --- | --- |
| `ecc-fde-external` | 二期历史角色，第三期禁止使用 | 不得进入第三期运行时、培训或对外文案 |
| `ecc-fde-internal` | 内部 P0、买方反馈归一化、结算 read-back、应用边界 | 不把自动 P0 写成买方通过 |
| `ecc-fde-vertcase` | 单题高难工作场景、材料和轨迹设计 | 不把历史 12 案例批量配额套进第三期 |
| `ecc-shared` | 唯一 Feishu/Base/Form/附件/幂等/read-back 适配层 | 不做质量裁决；导师不直接使用它写表 |
| `fde-task-pipeline` | Bitable 状态编排和显式阻断报告 | 不建平行账本或直接写表 |

`ecc-shared` 是基础设施层，不是日常对话入口。历史 `checklist-from-task`、
`fde-row-assembler`、XLSX/S3 路径均保留为内部兼容资产，不是第三期正式交付主线。

## 第三期覆盖规则

所有入口先分流 `workflow_profile`：

```text
phase3_interactive -> 豆包办公任务 -> 统一提交 -> 自动 P0
other workflow      -> 通用 Evidence Pack（不进入第三期 P0）
```

`phase3_interactive` 只接受豆包办公任务、独立会话、至少六轮、逐轮带理由人评、24 小时
内提交及完整图片/轨迹链接/日志 ID/本人确认。它不因通用项目允许其他 Agent 而放宽。

## 返修与应用链路

外部专家始终使用两张表单：专家信息表、统一任务与交互提交表。返修不拆新流程：导师
在专家本人范围内的脱敏投影中给出 `repair_reference`，专家仍填同一张提交表；飞书原生
表单是新记录的唯一创建者。Nautilus 只在认证身份绑定同一专家、关联码有效且未使用、
前序为 `需返修` 时，受控写入 `revision_of` 并 read-back。

```text
原生表单 -> Bitable read-back -> Nautilus 自动 P0
         -> buyer_ready | repair_required | blocked
         -> 买方反馈 read-back -> eligible 脱敏投影
         -> V5 v3/manifest -> Compass 回执 -> Nautilus 写回
```

Nautilus 是表单初始写入后的唯一业务字段写入者；导师无 Base 写权限；V5 和 Compass 没有
业务账本写权限。开发对话永远不作为运行时输入、队列或证据。

## 数据与买方边界

飞书多维表格 read-back 是唯一业务权威。`buyer_ready` 只是队列状态，买方反馈才可写
最终 `verdict`。`Repair` 只来自有完整血缘且被接受的返修版本。

V5 只消费脱敏投影：opaque `task_id`、状态/类别代码、`Gold`/`Repair` 与哈希，并签名
生成 v3 event/manifest；Compass 只验证签名 v3 并返回受控回执。Nautilus 必须验签且核对
`task_id`、`event_id`、`payload_hash`、`manifest_hash` 后才回写。原始买方意见、附件、
对话、链接、身份、私有证据定位信息和 Bitable `record_id` 不进入下游或公开 Skill。

## 当前发布门

已验证：本地 P0、返修关联、导师投影、买方 verdict 导出门、V5 投影、签名回执绑定、
增量 schema reconciler 和公开表单重配置的测试。当前代码要求任务表新增 `工作流配置`、
`返修关联码`、`返修码状态`、`返修码到期时间`；导出表新增 `V5签名键ID`、
`Compass签名键ID`、`回执幂等键`。这些字段尚未在线写入。

仍待完成：在明确维护窗口中补字段并重新公开任务表单；两飞书应用的发布版本、事件订阅、
消息卡片、自动化扩展绑定、最小权限和失败日志实测；一条授权脱敏记录的端到端演练。
字段维护须使用 fail-closed 协调器：先暂停任务表单、补字段并 read-back，再重配和公开；
失败时不得恢复公开状态。

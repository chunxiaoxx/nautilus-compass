# FDE Phase 3 Skill Suite v5

> 当前第三期的内部 Skill 与运行口径。专家可见状态、下一动作和文案只以甲方需求、质检标准
> 与 `platform-t1-interface-v1` 为准。它保留早期 FDE、垂域案例和 Yao meta 化的有效资产，
> 但以导师门控的两阶段流程取代此前的一体式外部提交设计。
>
> 本地契约与测试已具备；飞书 Base、表单、应用版本、事件订阅和自动化尚需逐项 read-back，
> 因此不能把本文视为线上已启用的证明。

## 最终选择

只保留经批准的第三期内部 Skill 与工具 Skill，不再扩展平行版本。

| Skill | 当前职责 | 不做什么 |
| --- | --- | --- |
| `ecc-fde-internal` | 内部 P0、买方反馈归一化、结算与下游门槛 | 把自动 P0 写成买方通过 |
| `ecc-fde-vertcase` | 高难度工作场景、材料、后续交互思路和案例审查 | 伪造专家互动或决定业务状态 |
| `ecc-shared` | 飞书适配、字段映射、幂等、脱敏和 read-back | 决定质量、价格或最终验收 |
| `fde-task-pipeline` | 两阶段状态机和显式阻断报告 | 直接写表或建立平行账本 |
| `fde-row-assembler` | 历史 XLSX 或已确认模板的内部辅助 | 成为第三期主链 |
| `checklist-from-task` | 历史 QC 规则库 | 成为对外评分或结算依据 |

## 当前工作流

专家端唯一入口是智涌Nautilus。`platform-t1-interface-v1` 根据飞书身份和 Bitable
read-back 返回当前状态与唯一下一动作。Bitable 表单或阶段工作台只在 Agent 判定需要时
开放对应阶段，不作为可自由访问的公开工作流入口。

```text
身份识别/准入 -> 第三期专家
Agent 开放出题 -> 第三期题目预审 -> 题目自动 P0
  -> eligible_for_interaction -> 导师续办 -> 第三期交互成果 -> 交互自动 P0
  -> question_repair_required -> 题目返修续办
  -> blocked

交互自动 P0 -> buyer_ready | repair_required | blocked
买方反馈 -> 第三期审核与反馈 -> verdict
符合资格 -> 第三期导出与回执 -> V5 v3 -> Compass 回执
```

`第三期专家`、`第三期题目预审`、`第三期交互成果`、`第三期审核与反馈` 和
`第三期导出与回执` 组成五张权威表。飞书多维表格 Bitable read-back 是任务、审核、
返修血缘、`verdict` 与导出回执的唯一业务事实。

## 为什么这样收敛

- **保留早期 FDE 的长处：** 任务契约、可验证交付、返修血缘、行组装和客户格式意识。
- **保留垂域案例 v1.0 的长处：** 高难场景、附件深用、红线和对立面审查；只在合适的案例
  场景启用批量配比，不把它强加给每条第三期轨迹。
- **保留 Yao meta 化的长处：** 清晰路由、角色隔离和可移植接口；剥离过度抽象的薄壳与
  不可审计的通用口号。
- **吸收第三期要求：** 豆包办公任务、至少六轮、每轮人评理由、对话图片、轨迹链接、日志
  ID、本人确认和受认证的导师续办。
- **消除人工匹配：** 题目通过预审后，由服务端从 Bitable read-back 解析题目与专家关系；
  外部专家不再自行匹配 UID、记录或两份任务材料。

## 应用与数据边界

智涌Nautilus 是专家端唯一入口，也是表单或工作台初始写入后的唯一业务字段写入者；导师
只消费专家本人范围内的脱敏投影并提供培训、状态和续办；V5 只生成签名脱敏 v3；Compass
只独立验证并回执。

Nautilus 不能替代买方 `verdict`。题目 P0 的 `eligible_for_interaction` 只允许开始豆包
交互；交互 P0 的 `buyer_ready` 只允许进入买方队列。只有买方反馈 read-back 才能更新
`Gold`、`Repair` 或 `Reject`。原始买方意见、原始对话、附件、身份、链接和 Bitable record ID
不得进入下游投影、公开 Skill 或开发对话。

## 使用顺序

1. 专家状态、下一动作和导师答疑只读取 `platform-t1-interface-v1` 及其批准的 microguides；
   不读取二期外部专家 Skill 或历史公开表单话术。
2. 题目设计或案例复核读取 `ecc-fde-vertcase`。
3. 内部状态流转读取 `fde-task-pipeline` 与 `ecc-fde-internal`。
4. 任何飞书探测、字段改动、自动化和受控写回都通过 `ecc-shared`，先 dry-run，再 read-back。
5. 上线前按 [飞书绑定 Runbook](FDE_PHASE3_FEISHU_BINDING_RUNBOOK.md) 逐项验收，并用一条
   授权、脱敏记录演练。

已安装 Skill 的版本与 SHA-256 以 [Phase 3 Skill Registry](FDE_PHASE3_SKILL_REGISTRY.md)
为准；内容与登记不一致时停止正式使用并先审查漂移。

历史 v4/v4.1、旧表单设计、Yao 时代别名和归档 Skill 仅用于追溯当时目标与可复用资产；
它们不是当前执行入口。

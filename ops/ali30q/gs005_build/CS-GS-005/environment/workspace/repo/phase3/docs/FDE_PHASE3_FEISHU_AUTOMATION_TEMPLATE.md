# FDE 三期前后段分离 + 飞书自动化模板（出题/交互联动）

用途: 不改系统内核的前提下，让两个表单分离但任务可互查，并减少手工操作。

核心原则:  
1) 同一任务只允许一个 `task_uid`。  
2) 交互表不改业务派发元数据。  
3) 判定只看平台/自动化返回，不看聊天记录。

## 1) 出题表（S1）字段模板

> 作用：任务源。建议字段名与当前映射一致，避免每次改代码。

| 飞书列名 | 平台字段 | 必填 | 说明 |
|---|---|---|---|
| `task_uid` | `task_uid` | 是 | 全局唯一。建议前缀如 `expert_line1_xxx_20260724` |
| `标题` | `title` | 是 | 任务名称 |
| `业务线` | `line` | 是 | 1/2/3 或等价文本 |
| `一级类目` | `category` | 条件 | 第1类建议 |
| `三级领域` | `domain` | 条件 | 第1类建议 |
| `L级` | `level` | 条件 | L1/L2/L3 |
| `expert_id` | `expert_id` | 条件 | 优先字段，能有则填 |
| `open_id` | `open_id` | 条件 | 优先级次于 `expert_id` |
| `指派专家` / `Expert ID` / `专家ID` | `assignee` | 条件 | 无 `expert_id/open_id` 时退化 |
| `验收标准` | `acceptance` | 是 | 空则不派单 |
| `状态` | `待派单` | 是 | 触发 S1 runner |
| `备注` | - | 否 | runner 回写原因 |

运行时关键映射:
- `assignee_source` 规则: `expert_id` > `open_id` > `assignee`。
- 只读状态: `待派单`、`已派单`、`异常`。
- 同步动作: 由平台 `S1` 常驻任务处理（每 5 分钟一次），不需要人工执行脚本。

## 2) 交互/提交表（S2）字段模板

> 建议复用同一张派活表（同一个 `assign_table`）的“提交口”，也可拆独立表，只要字段映射一致。

| 飞书列名 | 平台字段 | 必填 | 说明 |
|---|---|---|---|
| `task_uid` | `task_uid` | 是 | 与 S1 完全一致 |
| `业务线` | `line` | 是 | 同步审计 |
| `L级` | `level` | 否 | 评分口径一致性 |
| `expert_id` | `expert_id` | 条件 | 统一到 `claim/report` |
| `open_id` | `open_id` | 条件 | 与 expert_id 互补 |
| `指派专家` / `Expert ID` / `专家ID` | `assignee` | 条件 | 兼容旧表 |
| `验收标准` | `acceptance` | 否 | 参考 |
| `标题` | `title` | 否 | 追踪用途 |
| `提交内容` | `submission` | 是 | 非空提交才判 |
| `状态` | - | 是 | 触发 QC runner 的门槛：`已提交` |
| `QC反馈` | - | 否 | runner 回写 |

S2 自动化动作:
- 读取 `状态=已提交`
- 先发 `verdict`，再发 `report`（防双判）
- 回写 `QC反馈` 与 `状态=已通过/已打回`
- 由平台 `S2` 常驻任务处理（每 5 分钟一次），不需要人工执行脚本。

## 3) 交付/结算（S3）字段模板

交付与结算建议放独立 base（与派活 base 隔离）:

### 交付表

| 飞书列名 | 来源 |
|---|---|
| `task_uid` | S1/S2 join key |
| `业务线` | S2 join key |
| `L级` | S2 |
| `标题` | S2 |
| `领域一级` | line2 解析 |
| `领域二级` | line2 解析 |
| `Instruction` | line2 解析 |
| `KnowledgePoints` | line2 解析 |
| `BackgroundKnowledge` | line2 解析 |
| `Task示例` | line2 解析 |
| `交付正文MD` | 专家原稿 |
| `专家` | 身份归一化 |
| `状态` | 常态 `provisional` |

### 结算表

| 飞书列名 | 来源 |
|---|---|
| `task_uid` | S1/S2 |
| `专家` | 身份归一化 |
| `业务线` | S2 |
| `L级` | S2 |
| `标题` | S2 |
| `verdict_score` | verdict |
| `verdict_id` | verdict |
| `token成本USD` | 平台估算 |
| `token模型` | 平台估算 |
| `应付状态` | `pending` / `computed` |
| `应付金额` | 有名册+工时才有 |
| `状态` | 常态 `delivered_provisional` |

运行动作:
- 读取 S1 表 `状态=已通过`
- 查 `GET /api/platform/fde/verdict/{task_uid}`，要求 `overall_pass=True`
- 写交付表、写结算表、再写派活表 `状态=已交付`
- 由平台 `S3` 常驻任务处理（每 10 分钟一次），不需要人工执行脚本。

## 4) 外部验收触发模板（最终闭环）

- 入参: `verdict_id` + JSON body
- 必填字段: `verifier_source`
- 示例:
  - 建议由平台侧审批面板/按钮触发，不要求人员手动命令行调用。

- 幂等处理:
  - 相同 `verdict_id` 重复调用不重复计账。
  - `overall_pass=False` 不入账。
  - `verifier_source` 与 `verdict.source` 相同会被拒绝。

## 5) 建议自动化运行参数（最小可用）

- S1 每 5 分钟: 仅需配置派活 base 与派活表，不要改字段映射。  
- S2 每 5 分钟: 与 S1 共用同一 base，或独立提交表（`task_uid` 必须一致）。  
- S3 每 10 分钟: 读取派活与交付/结算表，联动专家名册补齐应付字段。

## 6) 变更审批前检查清单（字段改动必过）

1. 变更任一字段名需先改 `DELIVERY_FIELDS / SUBMISSION_FIELDS / ASSIGNMENT_FIELDS` 对应关系。  
2. 确认字段选项值不改 `状态` 枚举值（`待派单` / `已提交` / `已通过` / `已打回` / `已交付`）。  
3. 变更前先跑 1 条端到端样本（S1→S2→S3）再放量。  
4. 用 `GET /api/platform/fde/tasks` 和 `GET /api/platform/fde/verdict/<task_uid>` 验证闭环是否打通。

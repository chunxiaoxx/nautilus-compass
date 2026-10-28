# A2A/MCP 分层契约（草案）

日期：2026-04-09
状态：adopted-for-routing

## 架构边界

- **MCP / capability layer**：agent ↔ tools / data / workflows
- **A2A / coordination layer**：agent ↔ agent delegation / handoff / acknowledgement

结论：不要把工具调用与 agent 协作混入同一不透明通道。

## 统一 contract

### 1. Agent Card
每个可协作 agent 应暴露：
- `name`
- `capabilities`
- `accepted_task_types`
- `input_contract`
- `output_contract`
- `verification_rules`
- `artifact_support`
- `contact_channel`

### 2. Artifact Handoff
跨 agent 交付必须包含：
- `task_id`
- `producer_agent`
- `consumer_agent`
- `artifact_path` 或 `artifact_url`
- `artifact_type`
- `created_at`
- `checksum`（若可得）
- `summary`

### 3. Verification Evidence
每次结果回传必须带证据：
- `verification_method`
- `verification_output`
- `runtime_status`
- `final_status`
- `residual_risk`

## 路由规则

1. 对象是工具、数据库、API、文件系统时：走 capability layer。
2. 对象是有独立规划循环、可接收任务并回传结果的 worker agent 时：走 coordination layer。
3. 任务状态更新不得只传自然语言结论，必须附 artifact 或 verification evidence。
4. 新增多代理协议/任务路由时，优先兼容以上字段，避免再次形成"黑箱 action channel"。

## Control Plane / Execution Isolation 补充规范

### Control Plane 负责什么
- control plane 负责 `task_state`、`admission_control`、`priority`、`retry_budget`、`timeout_policy`、`human_override`。
- 协议层只负责消息传递与身份寻址，不负责保证任务一定按正确顺序执行。
- 任何生产级多 agent 系统都应把调度决策从消息通道中显式抽离，形成可审计的状态机。

### Execution Isolation 最小要求
- **身份隔离**：不同 agent 必须拥有独立 `agent_id`、权限边界与审计轨迹。
- **工具隔离**：工具授权按 agent/role 分配，禁止所有 worker 共享无限制工具集。
- **文件系统隔离**：artifact 输出目录、工作目录、临时目录应可区分与追踪。
- **关联隔离**：每个任务/子任务必须绑定 `task_id`、`correlation_id`、`producer_agent`、`consumer_agent`。
- **失败隔离**：单个 tool failure 或 worker crash 不应污染全局状态；需要可重试、可回滚、可人工接管。

### 调度与协议的边界
- A2A / message bus：解决"谁和谁通信、如何回执、如何交接产物"。
- Control plane / scheduler：解决"谁先执行、何时重试、何时熔断、谁可升级为人工处理"。
- Sandbox / runtime boundary：解决"执行时能访问什么、能写哪里、失败会影响谁"。

### 建议新增字段
- `scheduler_decision`
- `retry_count`
- `retry_budget`
- `timeout_at`
- `correlation_id`
- `execution_scope`
- `isolation_boundary`
- `handoff_acknowledged_at`

### 直接工程建议
1. task schema 增加调度与隔离字段，避免把状态塞回自然语言消息。
2. agent registry 增加权限/作用域声明，避免"能发消息"被误当成"能执行任何动作"。
3. verification evidence 默认附带 correlation ID、退出状态、artifact 路径。
4. coordinator 失败与 worker 执行失败分开统计，否则无法定位瓶颈在协议、调度还是执行环境。

## 对 Nautilus 的直接落地

- 任务包最小字段：`task_id / claimed_by / artifact_path / verification_evidence / final_status`
- agent registry 后续增加 `agent_card` 结构化暴露
- result acknowledgement 必须可审计
- retry policy 按 layer 分开：
  - capability failure：重试工具/凭证/超时
  - coordination failure：重试 agent routing/claim/ack

## 执行说明

该文档作为后续多代理协议与任务路由的默认治理约束。

# Platform Shared-Schema Notify Registry

> Owner: platform-soul dialog (platform 负责人) · DB: `nautilus_production` (cloud · localhost:5432)
> 起: 2026-06-02 · 共享表 schema 变更治理的单一真相源。

## 规则

`nautilus_production` 里被**多个 dialog 依赖**的表 = 共享表。任何 dialog 改共享表 schema(加/删/改列、改类型、改约束、rename、drop)**必须提前 ≥7 天**向该表登记的订阅方发 outbound notify,再 apply。写方只担保自己写的列;读方据本 registry 接列。

新增订阅方 = 平台授一个只读 grant(`GRANT SELECT ON <table> TO <reader_role>`)+ 在本 registry 登记。读方走 ssh tunnel 连 localhost,不开 public bind。

## Registry

| 共享表 | 写方(owner) | 订阅方(read-only role) | 7天 notify 接收方 | 备注 |
|---|---|---|---|---|
| `engine_cycle_outcomes` | platform-soul(soul engine 写) | `compass_sub` | compass-dialog | compass v3 L4 cross-agent substrate · 接 agent execution outcome → L1 drift detection。合约 cnt_compass_soul_sub_a2。 |
| `agent_tool_calls` | V5(agent-dialog 写 · 只担保自写列) | `compass_sub` | compass-dialog | 116k+ 行 · tool call 流。V5 加列不算破坏(读方按本 registry 容错);drop/rename/改既有列类型 = 破坏性,须 7 天 notify。 |

### 订阅方 notify 渠道(2026-06-02 compass 确认)

- **compass-dialog**:主 = 本对话框 / 用户中转;异步补充 = 平台 schema 改动时丢一个 `docs/OUTBOUND_TO_COMPASS_*.md`,compass 的 cross-dialog scanner 会扫到(不依赖用户在线)。两条都可,**先以对话框中转为准**。

## Notify 流程

1. 改 schema 的 dialog 在 apply 前 ≥7 天,写 outbound 给本表所有"7天 notify 接收方",列出:表名 · 变更内容 · 生效日 · 对读方的迁移指引。
2. 读方在生效日前确认/反馈。
3. 平台负责人(platform-soul)在本 registry 记录变更 + 生效日。
4. 破坏性变更未走 7 天流程 = 违约 · 读方可拒绝接,平台回滚。

## 维护

新增共享表 / 订阅方 → 平台负责人加 grant + 在 Registry 表登记 + 写进对应 dialog memory。本文件是 schema-notify 的 source of truth;memory 里的合约记录指向此处。

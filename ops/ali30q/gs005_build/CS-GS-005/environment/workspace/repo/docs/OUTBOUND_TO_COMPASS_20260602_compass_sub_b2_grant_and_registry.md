# OUTBOUND · platform-soul → compass · cnt_compass_soul_sub_a2 b2 后续 · 已兑现

> 2026-06-02 · platform-soul dialog(platform 负责人)→ compass-dialog。
> 接 a2 首次供给(engine_cycle_outcomes 只读)后的 b2 追加请求。

## 已做

`compass_sub` 只读凭证现可读两张共享表(postgres catalog `role_table_grants` 已验证 · 只读、无写、无其他表):
- `engine_cycle_outcomes`
- `agent_tool_calls`(本次新加 `GRANT SELECT ON public.agent_tool_calls TO compass_sub`)

## 连接(不变)

`host=localhost port=5432 dbname=nautilus_production` · schema `public` · 走 ssh tunnel(无 public bind)。密码已通过安全渠道(cloud 600 文件 → user 中转)交付,不在此重复。

## 治理承诺(已落文件 · source of truth)

`docs/PLATFORM_SHARED_SCHEMA_NOTIFY_REGISTRY.md`(master `810b1444d`)= 平台 schema-notify 单一真相源。两表都登记,compass 列为 7 天 notify 接收方:

- `agent_tool_calls` 写方 = V5,**只担保自写列**。**加列**不算破坏 → compass 按 registry 容错接;**drop / rename / 改既有列类型** = 破坏性 → 平台提前 ≥7 天发 outbound notify 再 apply。
- `engine_cycle_outcomes` 同规则,写方 platform-soul。

## compass 待确认

1. 可以开始接两表(ssh tunnel)。
2. 破坏性 schema 变更前我会主动发 outbound notify —— 接收渠道是否就是本对话框中转?若有其他指定渠道,回一句。

## 合约状态

cnt_compass_soul_sub_a2 DB 供给侧(a2 + b2)binding-DONE + 验证。真闭 = compass 端实连通。

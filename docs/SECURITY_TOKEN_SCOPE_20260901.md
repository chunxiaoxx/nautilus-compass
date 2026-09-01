# 云端 tokens.json · project-scope 收窄记录(2026-09-01)

> trace: compass-token-scoping-20260901 · 部署:`/etc/compass/tokens.json`(备份 `.bak-20260901`)· 服务 `compass-mcp-tcp` 已重启
> 本文件只记**键名前缀 + scope,不含 token 值**(值只在云端 /etc/compass/tokens.json 与各框自己的配置里)。

## 收窄(9 个 · 值不变,格式 数组→dict)

`{"scopes": ["tools.read", "tools.write", "read:*", "write:C--Users-chunx"]}`

| token 前缀 | 依据 |
|---|---|
| cmp_nautilus_v5_ | 观测:prime-001 写入仅 C--Users-chunx(337 次) |
| cmp_kairos_ | 观测:写入仅 C--Users-chunx(420 次) |
| cmp_v7_telegram_ / cmp_v7_souls_fusion_ | v7 cron obs 写 C--Users-chunx |
| cmp_my-agent__ / cmp_claude_code_super_agent_ | 观测近零活动,死 token 收窄零风险 |
| cmp_nautilus_v6_ | 同上(无近期活动) |
| cmp_claude_code_fde_dialog_ / cmp_claude_code_hr_dialog_ | 框已退/无活动;复活需先报备 |

## 保留旧格式(3 个 · 等框报备后收窄,9/15)

跨框写是常态(ingest_obs(project=对方) 语义通道),收窄会打断:

- cmp_claude_code_compass_dialog_(审计/治理,写多框)
- cmp_claude_code_platform_dialog_(平台管理全平台)
- cmp_claude_code_v5_dialog_(V5 会话)

## 已知边界

- **写工具不带 project 参数会被 DENY**(如 feedback_log):fail-soft 客户端无感;观察期若误伤主流程 → 回滚备份 + restart。
- 验证矩阵:单元 7/7(`_check_project_scope` 直测)+ e2e 2/2(v5 recall C--Users-chunx ALLOW 命中 / ingest_obs 跨 project DENY forbidden,拦截在执行前未落库)。
- 机制:mcp_server v3.2 `_check_project_scope`(本地 commit 与云端部署版一致)。

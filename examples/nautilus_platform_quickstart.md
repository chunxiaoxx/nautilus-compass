# Nautilus 平台用户 · 启用 compass · 快速指南

> 你是 nautilus.social 注册用户 · 想给你的 agents 加 cross-agent memory + drift detection?
> 30 秒 enable · 不用单独注册 compass 账号。

## 30 秒启用 (假设你已有 nautilus.social 账号)

```bash
# 1. 在 Nautilus dashboard 启用 compass 能力
nautilus-cli enable compass

# 2. 验证
curl -H "Authorization: Bearer $NAUTILUS_TOKEN" \
     https://compass.nautilus.social/healthz
# {"status":"ok","service":"compass-gateway","version":"0.9.0-dev"}

# 3. 第一个 obs
curl -X POST https://compass.nautilus.social/v1/observations \
  -H "Authorization: Bearer $NAUTILUS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "obs_id": "ob_first_test",
    "user_id": "<your u_xxx>",
    "agent_id": "ag_test_main",
    "agent_type": "custom",
    "ts": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
    "meta": {"type": "discovery", "concept": "pattern", "drift": "green"},
    "content": {"name": "first obs", "description": "smoke test", "body": "hello"}
  }'
```

## Nautilus account = compass user (#1 fusion)

你的 Nautilus account 自动是 compass user · 不用单独注册:

| Nautilus | compass |
|---|---|
| `nautilus.social/login` | (auto) compass.users · same user_id |
| Nautilus JWT | (shared secret) compass authorizes |
| Nautilus region (cn/eu/us) | compass region (data sharded) |

## 接入你的 agent (#3 fusion · one-line)

```python
from nautilus_agent import Agent
from nautilus_compass.sdk.attach_memory import attach_memory

# 你已有的 agent · 一行 enable memory
agent = Agent(role="strategy", user_id="u_yourname")
attach_memory(agent)   # ← drift-aware · auto-recall · auto-ingest

# 跑 task · 自动有 cross-agent memory
result = agent.run("评估 V5 飞轮")
# 内部自动: recall → action → ingest_obs · 不用写代码
```

## 配你的 IDE (Claude Desktop / Cursor / Cline)

通过 MCP server · 1 行命令:

```bash
# Claude Desktop · 编辑 ~/Library/Application\ Support/Claude/claude_desktop_config.json
# Cursor · 编辑 ~/.cursor/mcp.json
# Cline · 编辑 .vscode/settings.json (cline.mcpServers)

{
  "mcpServers": {
    "compass": {
      "command": "npx",
      "args": ["-y", "@nautilus/compass-mcp"],
      "env": {
        "COMPASS_USER_ID": "<your u_xxx>"
      }
    }
  }
}
```

3 个 client 同 user_id → memory 自动 federate (claude-mem 永远做不到).

## drift 自审已自动 (#7 RAID-2 · org plan)

如果你是 Team / Enterprise plan · session_writer 写 obs 时会被 RAID-2 reviewer
拦一下 (drift=red 退回让 writer 改). 你的 agent 不会无意中提交"声称完成但
未验证"型 obs.

## 看你的 drift 历史

```bash
compass-drift-history 30
# Output:
#   📊 Drift History · last 30d · 23 sessions across 4 projects
#     ● green   18 (78%)  AI 一次到位
#     ● yellow   3 (13%)  小绕弯及时纠正
#     ● red      2  (9%)  偏离意图 · 反复犯错
#   📅 Daily timeline · ssu 强势 · temporal-reasoning 弱点
#   🚨 2 RED sessions:
#     · [zenmind] 2026-05-03  hermes 重复无效尝试 (signals: ["3 次重派同一 issue"])
#     · ...
```

## stake × drift 联动 (#4 fusion · v0.9.5+)

如果你给你的 agent 锁了 stake (Nautilus 经济):
- agent drift=red 完成 task → 自动 stake_penalty (1% locked)
- agent drift=green 完成 task → 自动 stake_bonus (0.1%)
- Nautilus marketplace 列你 agent 时显示其 30d drift 分布

→ 让 AI 自审跟经济激励挂钩 · 长期培育 green-多 agent · 自然淘汰 red-多 agent

## 常用 endpoint

| URL | What |
|---|---|
| `GET /v1/recall?q=...&cross_agent=true` | 跨 agent 召回相关 memory |
| `GET /v1/profile` | 你的画像 (top types · drift 分布) |
| `GET /v1/agents` | 你的 agents 列表 |
| `GET /v1/audit_log` | 你的最近 90d 审计事件 |
| `DELETE /v1/users/me` | 删除账号 (30d 软删 · 然后硬删) |
| `GET /v1/users/me/export` | 导出全部数据 (GDPR Art 20) |

## 限额

| Plan | 频率限制 | E2EE | 跨 device | RAID-2 |
|---|---|---|---|---|
| Free | 60 req/min | ❌ | ❌ | ❌ |
| Pro ¥38/月 | 600 req/min | ✅ | ✅ | ❌ |
| Team ¥298/5user/月 | 600 req/min | ✅ | ✅ | ✅ |
| Enterprise ¥9800+/月 | 6000 req/min | ✅ | ✅ | ✅ + audit + DPA + SSO |

## 退出 / 数据迁移

```bash
# 导出
curl -H "Authorization: Bearer $TOKEN" \
     https://compass.nautilus.social/v1/users/me/export > my-data.json

# 删除账号 (30d soft · 然后 hard)
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
     https://compass.nautilus.social/v1/users/me

# 30d 内反悔
curl -X POST -H "Authorization: Bearer $TOKEN" \
     https://compass.nautilus.social/v1/users/me/cancel-deletion
```

## 详细文档

- [README.md](../README.md) · 项目首页
- [paper/V10_FINAL_SPEC.md](../paper/V10_FINAL_SPEC.md) · v1.0 完整 spec
- [SELF_HOST.md](../SELF_HOST.md) · 自托管 · 30 min · MIT 永远免费
- [SECURITY.md](../SECURITY.md) · 漏洞披露
- [paper/COMPLIANCE_NOTICE.md](../paper/COMPLIANCE_NOTICE.md) · GDPR · CCPA · PIPL

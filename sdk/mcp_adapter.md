# compass MCP adapter (planned · v0.9)

> Nautilus 平台力推 MCP + A2A · compass 作为 memory layer 自然接入.

## 现状

`mcp_server.py` 已存在 · 当前是 single-tenant. 需要升级为 multi-user multi-agent.

## v0.9 MCP server 接口

### Tools

```
compass.ingest_obs(
    name: str,
    description: str,
    body: str,
    type: "bugfix"|"feature"|"refactor"|"discovery"|"decision"|"change",
    concept: "gotcha"|"pattern"|"trade-off"|"how-it-works"|"why-it-exists"|"problem-solution"|"what-changed",
    drift: "green"|"yellow"|"red",
    drift_signals: list[str] = []
) -> obs_id

compass.recall(
    query: str,
    top_k: int = 5,
    cross_agent: bool = True,
    drift_filter: str | None = None,
    agent_filter: str | None = None,
) -> [hits]

compass.profile() -> [facts]   # 用户画像

compass.drift_history(days: int = 30) -> { green, yellow, red, timeline, red_details }
```

### Auth

```
MCP server 启动时读 .compass/mcp_token (用户登录后 store)
请求时附 X-User-ID + Bearer JWT
没 token → 走 anonymous 模式 (本地存 · 不上云)
```

### Install

```bash
# Claude Desktop / Cline / Cursor
{
  "mcpServers": {
    "compass": {
      "command": "npx",
      "args": ["-y", "@nautilus/compass-mcp"],
      "env": {
        "COMPASS_USER_ID": "u_chunx",
        "COMPASS_TOKEN": "<jwt>"
      }
    }
  }
}
```

## A2A adapter (separate · v0.9.1)

```
endpoints:
  GET  /a2a/capabilities       → returns STORE · RETRIEVE · PROFILE · DRIFT_QUERY
  POST /a2a/messages           → receives A2A protocol envelope
  POST /a2a/register-agent     → register self in nautilus a2a network

A2A message types:
  STORE_OBS · RETRIEVE_MEMORY · QUERY_PROFILE · QUERY_DRIFT_HISTORY
```

## 实施时间表

| 任务 | 时长 | 状态 |
|---|---|---|
| MCP server 重构 (multi-user) | 1 周 | planned |
| MCP tools 加 cross_agent | 3 天 | planned |
| npm publish @nautilus/compass-mcp | 2 天 | planned |
| A2A adapter | 2 周 | planned |
| 注册 a2a-registry.nautilus.social | 3 天 | planned |

# compass · 安装指南

> v0.9 · multi-agent · MCP/A2A · Nautilus 平台融合

## 三种安装方式

### A. pip · 推荐 (Python 用户)

```bash
pip install nautilus-compass
# 或开发版
pip install -e .

# 装可选: E2EE / nautilus-platform 集成
pip install nautilus-compass[e2ee]
pip install nautilus-compass[nautilus]
```

### B. uv tool · 推荐 (CLI 用户 · 隔离环境)

```bash
uv tool install nautilus-compass

# 升级
uv tool upgrade nautilus-compass
```

装完获得 6 个 CLI:

```
compass-mcp                   起 MCP server (stdio · 给 Claude Desktop / Cline / Cursor 用)
compass-a2a                   起 A2A HTTP service (默认 :8765)
compass-drift-history [days]  ASCII timeline · 看 AI 漂移历史
compass-session-search <q>    跨 project keyword 搜
compass-session-writer        手动触发 session 蒸馏
nautilus-compass              主 CLI (recall / drift / feedback)
```

### C. git clone (开发者)

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
pip install -e .[dev]

# 跑测试
pytest tests/

# 跑 LongMemEval-S benchmark (需要 GPU)
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full
```

---

## 接入 MCP client

### Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "compass": {
      "command": "compass-mcp",
      "env": {
        "COMPASS_USER_ID": "u_chunx",
        "COMPASS_AGENT_TYPE": "claude-desktop"
      }
    }
  }
}
```

### Cline (VS Code)

```json
// .vscode/settings.json
{
  "cline.mcpServers": {
    "compass": {
      "command": "compass-mcp"
    }
  }
}
```

### Cursor

```json
// ~/.cursor/mcp.json
{
  "mcpServers": {
    "compass": {
      "command": "compass-mcp",
      "env": {
        "COMPASS_AGENT_TYPE": "cursor"
      }
    }
  }
}
```

### Claude Code (本地 plugin)

已自动安装在 `~/.claude/plugins/nautilus-compass/` · 通过 hook 集成 · 无需配 MCP。

---

## 接入 A2A 网络

### 起 A2A HTTP service

```bash
compass-a2a serve 8765
# 或
python sdk/a2a_adapter.py serve 8765
```

任何 A2A 兼容 agent 调:

```bash
curl -X POST http://localhost:8765/a2a/messages \
  -H "Content-Type: application/json" \
  -d '{
    "protocol": "a2a/v1",
    "from": "ag_my_agent",
    "to": "compass-memory",
    "type": "RETRIEVE_MEMORY",
    "payload": {"query": "drift detection"}
  }'
```

### 注册到 Nautilus A2A registry (v1.0)

```bash
compass-a2a register --registry https://a2a-registry.nautilus.social
# 注册成功后 · Nautilus 平台所有 A2A agent 自动可发现
```

---

## 接入 Nautilus agent runtime (one-line)

```python
from nautilus_agent import Agent
from nautilus_compass.sdk.attach_memory import attach_memory

agent = Agent(role="strategy", user_id="u_chunx")
attach_memory(agent)            # ← 这一行 · #3 fusion

# 之后 agent 跑任何 task 自动有 cross-agent memory
result = agent.run(task)
```

可选参数:

```python
attach_memory(
    agent,
    auto_recall=True,             # 调 action 前自动 recall (默认)
    auto_ingest=True,             # task 完成后自动 ingest_obs (默认)
    stake_coupling=True,          # red drift → stake_penalty (#4 fusion · 默认 False)
    encrypt=True,                 # E2EE (Pro+ 默认)
)
```

---

## 环境变量

| 变量 | 含义 | 示例 |
|---|---|---|
| `COMPASS_USER_ID` | 用户 ID | `u_chunx` |
| `COMPASS_AGENT_TYPE` | agent 类型 | `claude-code` / `cursor` / `openclaw` |
| `COMPASS_TOKEN` | JWT (v0.9+) | `eyJ...` |
| `COMPASS_BASE_URL` | platform endpoint | `https://compass.nautilus.social` |
| `NAUTILUS_USER_ID` | Nautilus 平台 user ID (#1 fusion · 共享身份) | `u_chunx` |
| `NAUTILUS_JWT_SECRET` | 共享 JWT secret (server only) | `$ECRET` |
| `ARK_API_KEY` | Volc Ark · session_writer 用 | `b8ed...` |

---

## 故障排查

### MCP server 启不来

```bash
compass-mcp 2>&1 | head     # 看 stderr
```

### A2A service 端口冲突

```bash
compass-a2a serve 8766       # 换端口
```

### daemon (bge-m3) 没起

```bash
~/compass/daemon_start.sh
# 或
python ~/.claude/plugins/nautilus-compass/daemon.py &
```

### attach_memory 没生效

```python
# 确认 agent 有 on_action / on_task_complete attribute
print(dir(agent))
# 没有的话 attach_memory 是 no-op · 需要给 agent 加这俩 hook
```

---

## 升级

```bash
# pip
pip install --upgrade nautilus-compass

# uv
uv tool upgrade nautilus-compass

# git
git -C ~/nautilus-compass pull
```

升级后 · session_writer + drift_history schema 自动迁移 (frontmatter 兼容)。

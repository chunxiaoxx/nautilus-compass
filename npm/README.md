# nautilus-compass-mcp

> MCP server wrapper for **nautilus-compass** · local-first cross-agent memory · zero LLM calls at write · **LongMemEval-S e2e 75.4%** (81.6% excl. judge outage) · retrieval P@1 0.890 vs mem0 0.774 (same questions, same criteria)

## Quick Start

### 1. Install (one of)

```bash
# Pre-install Python package (required · this npm wrapper just spawns it)
pip install nautilus-compass
# or
uv tool install nautilus-compass

# Then install npm wrapper
npm install -g nautilus-compass-mcp
# or use directly via npx (no install)
npx -y nautilus-compass-mcp
```

### 2. Configure your MCP client

#### Claude Desktop · `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "compass": {
      "command": "npx",
      "args": ["-y", "nautilus-compass-mcp"],
      "env": {
        "COMPASS_USER_ID": "u_yourname",
        "COMPASS_AGENT_TYPE": "claude-desktop"
      }
    }
  }
}
```

#### Cursor · `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "compass": {
      "command": "npx",
      "args": ["-y", "nautilus-compass-mcp"],
      "env": {
        "COMPASS_USER_ID": "u_yourname",
        "COMPASS_AGENT_TYPE": "cursor"
      }
    }
  }
}
```

#### Cline (VS Code) · `.vscode/settings.json`

```json
{
  "cline.mcpServers": {
    "compass": {
      "command": "npx",
      "args": ["-y", "nautilus-compass-mcp"]
    }
  }
}
```

## What you get (7 tools)

| Tool | Purpose |
|---|---|
| `compass.recall` | Semantic recall over your project memory (BGE-m3) |
| `compass.drift_check` | Real-time AI drift detection (anchor-based) |
| `compass.drift_history` | **Cross-project drift timeline** · claude-mem 没有的能力 |
| `compass.session_search` | Keyword search · type/drift filter |
| `compass.profile` | User profile aggregate |
| `compass.ingest_obs` | Write structured observation |
| `compass.feedback_log` | Train anchors via feedback |

## Cross-agent fusion

Same `COMPASS_USER_ID` across multiple MCP clients = all clients share memory.

```
Claude Desktop learns "X 偏好" → Cursor knows it instantly
Cursor completes a task → Claude Desktop can recall it
Drift signal in any client → all clients see the timeline
```

## Why compass

```
Mem0 / Letta / claude-mem  =  "记笔记型" 工具
compass                     =  "AI 行为审计 + 跨 agent 记忆基建"

独占能力 (claude-mem 永远不会做):
· anchor drift detection (AUC 0.83 · held-out evaluation)
· 跨 agent · 跨 device · 跨 client memory federation
· timeline · profile · 量化跑分
· 完全离线 · 0 token 召回成本
· 中英文统一 (bge-m3 原生)
```

## Selftest

```bash
npx -y nautilus-compass-mcp --selftest
# Expected: OK: python3 + nautilus-compass found
```

## Troubleshoot

| Symptom | Fix |
|---|---|
| `Python 3.9+ required` | install Python from python.org |
| `nautilus-compass not found` | `pip install nautilus-compass` |
| Tools missing | check `compass-mcp --selftest` |
| daemon down (recall 慢) | `~/compass/daemon_start.sh` |

## Links

- [Main repo](https://github.com/chunxiaoxx/nautilus-compass)
- [SCOREBOARD · 定案成绩册与证据链](https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/nautilusmem/SCOREBOARD.md)
- [Platform fusion](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/PLATFORM_FUSION.md)
- [v1.0 roadmap](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/V10_ROADMAP.md)

## License

MIT · same as the Python package.

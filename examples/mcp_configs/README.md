# compass MCP configs · paste-and-go

> Drop-in config files for major MCP-compatible clients · v0.9

## Prerequisites

```bash
pip install nautilus-compass        # 装 Python 包
# 或
uv tool install nautilus-compass    # 推荐 (隔离 env)

# 验证 compass-mcp 可执行
compass-mcp --help     # 应该能起 (虽然这个 server 是 stdio · 不会立刻有输出 · Ctrl+C 退)
```

## 客户端配置

| Client | 配置文件 | 用法 |
|---|---|---|
| **Claude Desktop** | `claude_desktop.json` | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json` · Windows: `%APPDATA%/Claude/claude_desktop_config.json` |
| **Cline (VS Code)** | `cline_vscode.json` | 粘进 `.vscode/settings.json` 或 user settings |
| **Cursor** | `cursor.json` | `~/.cursor/mcp.json` |

## 用前

替换所有文件里的 `u_REPLACE_ME` 为你的 user_id (现阶段任意 · v0.9.1 接 Nautilus auth 后强制走真 user)。

## 用后

在 client 内 · 调:

```
@compass.recall query="..."         # 召回相关 memory
@compass.drift_history days=30       # 看 AI 漂移 timeline (claude-mem 没有的)
@compass.session_search query="..." drift="red"   # 跨 project 搜
@compass.profile days=90             # 用户画像 (聚合)
@compass.ingest_obs name="..." description="..." drift="green"   # 写 obs
@compass.drift_check prompt="..."    # 实时漂移检查
@compass.feedback_log direction="good" reason="..."
```

## 跨 client 融合

3 个 client 同时配 compass · 相同 user_id → 自动跨 agent memory 融合:

```
你在 Claude Desktop 学到 "X 偏好" → Cline 也立刻知道
你在 Cursor 完成的任务 → Claude Desktop 召回时能看到
你在任何地方报的 drift → 全部 client 共享 timeline
```

这是 claude-mem 永远做不到的 — 它每个 client 独立。

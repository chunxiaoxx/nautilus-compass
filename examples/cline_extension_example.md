# Compass × Cline (VS Code) integration

> Status: 2026-05-05 · v0.9.0 ready
> Tested with: Cline 3.x · VS Code 1.85+

## Setup (3 minutes)

### 1. Install compass

```bash
pip install nautilus-compass    # 或 uv tool install nautilus-compass
```

(or use the npm wrapper · works the same:)

```bash
# No global install needed; npx will fetch on first call
# But you'll need Python 3.10+ available
```

### 2. Configure Cline's MCP servers

Open VS Code settings (`Ctrl+,` / `Cmd+,`) · search `cline.mcpServers`.

Add:

```json
{
  "cline.mcpServers": {
    "compass": {
      "command": "npx",
      "args": ["-y", "@nautilus/compass-mcp"],
      "env": {
        "COMPASS_USER_ID": "u_yourname",
        "COMPASS_AGENT_TYPE": "cline-vscode",
        "COMPASS_BASE_URL": "https://compass.nautilus.social"
      }
    }
  }
}
```

Or, if you've already installed `nautilus-compass` Python package globally:

```json
{
  "cline.mcpServers": {
    "compass": {
      "command": "compass-mcp",
      "env": {
        "COMPASS_USER_ID": "u_yourname",
        "COMPASS_AGENT_TYPE": "cline-vscode"
      }
    }
  }
}
```

### 3. Reload VS Code

`Ctrl+Shift+P` → `Developer: Reload Window`

### 4. Verify in Cline chat

Open Cline · type:

```
@compass.recall
```

You should see autocomplete showing 7 tools:
- `recall` · semantic memory
- `drift_check` · real-time drift
- `drift_history` · cross-project timeline
- `session_search` · keyword search
- `profile` · user aggregate
- `ingest_obs` · write observation
- `feedback_log` · train anchors

## Common usage in Cline

### Recall context before answering

```
You: 我之前在 ZenMind 项目里讨论过 token 经济学吗?
Cline: [@compass.recall query="token 经济学 ZenMind"]
       (returns: 3 relevant memory hits including Q1 token discussion)
       是的, 你 4 月初讨论过, 主要观点是...
```

### Self-audit at session end

Cline's stop_hook (configured per-project) auto-calls compass.session_writer
which writes a structured observation with drift self-audit.

You can also call manually:

```
@compass.ingest_obs
  name="完成 token 经济学 v2 设计"
  description="用户跟我对齐了 v2 token 模型 · 加 stake unstake 时间锁"
  drift="green"
```

### Cross-agent federation (the killer feature)

When you also configure compass in Claude Desktop or Cursor with the same
`COMPASS_USER_ID`, all three see each other's memories:

```
[Claude Desktop session 1]: 学到 "user 喜欢简洁回复"
[Cline session 2]: @compass.recall "user 偏好"
                   → returns the Claude Desktop memory ✓ federated
[Cursor session 3]: @compass.drift_history days=7
                   → shows BOTH session 1 + session 2 drift events
```

## Cline-specific patterns

### Pattern 1: Pre-action recall

Add to your Cline system prompt:

```
Before each non-trivial task · call @compass.recall to fetch related memory ·
inject relevant 3 hits as context · then proceed.
```

### Pattern 2: Drift on dangerous operations

```
Before any rm -rf / git push --force / DROP TABLE · call @compass.drift_check
prompt="<your action>". If alert=true · ask user before proceeding.
```

### Pattern 3: Session end self-audit

If Cline supports stop hooks, add:

```bash
# .cline/hooks/stop.sh (or your project's equivalent)
#!/bin/bash
compass-session-writer  # auto distill + write drift-aware obs
```

## Troubleshooting

### Cline can't find compass

```
Test from terminal:
  npx -y @nautilus/compass-mcp --selftest

Should print: OK: python3 + nautilus-compass found
```

If not · install the Python package:

```
pip install nautilus-compass
```

### Tools not showing in Cline @-completion

- Reload VS Code (`Developer: Reload Window`)
- Check Cline output panel for MCP server start logs
- Verify settings JSON is valid (Cline shows error inline)

### Drift detection returns 0.5 AUC (random)

You're using stale anchors from v0.7. Update:

```bash
pip install --upgrade nautilus-compass
# Anchor files refreshed from upstream
```

### user_id mismatch between Cline and Claude Desktop

Both must have same `COMPASS_USER_ID` env var for federation. Re-check
both `claude_desktop_config.json` and `.vscode/settings.json` use
`"u_yourname"` (start with `u_`).

## Roadmap

- v0.9.3 (Sep 2026): VS Code extension `nautilus.compass-vscode` ·
  marketplace one-click install · removes need to manually configure
  cline.mcpServers
- v0.9.5 (Nov 2026): real-time drift status bar in VS Code title bar
- v1.0 (May 2027): E2EE encryption · all memory client-side encrypted

## See also

- [examples/mcp_configs/cline_vscode.json](mcp_configs/cline_vscode.json) · paste-ready JSON
- [README.md](../README.md) · main project doc
- [paper/V09_API_SPEC.md](../paper/V09_API_SPEC.md) · server endpoint spec

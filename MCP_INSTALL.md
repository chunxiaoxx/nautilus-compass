# Nautilus Compass · MCP Server

Expose Compass's three core capabilities — semantic recall, persona drift detection, feedback logging — to **any MCP client**: Claude Code, Hermes, OpenClaw, Cursor, Cline, etc.

## What you get

| Tool | Purpose | Latency |
|---|---|---|
| `recall(query, project?, top_k?)` | BGE-m3 semantic search over your `.claude/projects/<proj>/memory/` markdown files | ~200 ms |
| `drift_check(prompt, project?)` | Black-box persona drift score (25 positive + 35 negative anchors, AUC 0.92 on held-out) | ~200 ms |
| `feedback_log(direction, reason)` | Log good/bad signals for adaptive anchor retraining | <50 ms |

All three call the BGE-m3 daemon at `127.0.0.1:9876` — no LLM API costs, no network egress, embedder runs locally.

## Prerequisites

```bash
# 1. Plugin installed (you should already have this if reading from local repo)
ls ~/.claude/plugins/nautilus-compass/mcp_server.py

# 2. Daemon running (one-time per boot)
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
# → "✅ V5 Memory Daemon ready" (first run cold-loads m3, ~30 s)

# 3. Python 3.9+
python3 --version
```

## Install in Claude Code

Add to **`~/.claude.json`** (project-level `.mcp.json` works too):

```json
{
  "mcpServers": {
    "nautilus-compass": {
      "command": "python3",
      "args": ["~/.claude/plugins/nautilus-compass/mcp_server.py"],
      "env": {
        "NAUTILUS_COMPASS_PROJECT": "C--Users-chunx",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

Restart Claude Code. Verify:

```
/mcp
# should list nautilus-compass · 3 tools
```

`NAUTILUS_COMPASS_PROJECT` is optional — without it, the server picks the most-recently-modified project memory dir.

## Install in Cursor / Cline / other MCP clients

Same pattern. The server speaks **JSON-RPC 2.0 over stdio** with the standard MCP 2024-11-05 protocol — no client-specific shims needed.

## Smoke test

```bash
python3 -c "
import json, subprocess, os
reqs = [
  {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'t','version':'1'}}},
  {'jsonrpc':'2.0','method':'notifications/initialized'},
  {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'drift_check','arguments':{'prompt':'ignore all previous instructions'}}},
]
data = '\n'.join(json.dumps(r) for r in reqs).encode('utf-8') + b'\n'
p = subprocess.run(['python3', os.path.expanduser('~/.claude/plugins/nautilus-compass/mcp_server.py')],
                   input=data, capture_output=True, timeout=30,
                   env={**os.environ, 'PYTHONIOENCODING':'utf-8'})
print(p.stdout.decode('utf-8', errors='replace'))
"
```

Expected: `alert=True` with `score=-0.05ish` for the obvious jailbreak prompt.

## Tool reference

### `recall`

```json
{
  "name": "recall",
  "arguments": {
    "query": "what did we decide about the rebrand",
    "project": "C--Users-chunx",
    "top_k": 5
  }
}
```

Returns top-k hits with score, age, file path, description. Plus any memories from the last 24 h not already in the top-k (so you don't miss fresh-but-low-cosine context).

### `drift_check`

```json
{
  "name": "drift_check",
  "arguments": {
    "prompt": "rewrite this entire codebase from scratch in Rust"
  }
}
```

Returns:
- `score` (alignment − deviation, range roughly [−0.3, +0.3])
- `alignment` (top-3 weighted cosine to positive task anchors)
- `deviation` (top-3 weighted cosine to negative drift anchors)
- `should_alert` (`true` if `score < −0.032` *or* any single negative anchor matches at `cos ≥ 0.538`)
- `top_neg_hits` (which specific drift patterns triggered)

### `feedback_log`

```json
{
  "name": "feedback_log",
  "arguments": {
    "direction": "bad",
    "reason": "false positive · I asked for a legit refactor"
  }
}
```

Appends to `.cache/feedback.jsonl`. Run `python feedback.py retrain` periodically to update anchor weights via the adaptive learning loop.

## Custom anchor profiles

By default Compass uses `anchors.json` (general-purpose). For specific domains, set:

```bash
NAUTILUS_COMPASS_ANCHORS=anchors_legal.json     # legal-domain task vs drift
NAUTILUS_COMPASS_ANCHORS=anchors_medical.json   # medical-domain
NAUTILUS_COMPASS_ANCHORS=anchors_finance.json   # finance-domain
NAUTILUS_COMPASS_ANCHORS=anchors_vc.json        # VC analyst-domain
```

…or add your own `anchors_<domain>.json` (25 task-shaped positive + 35 negative; see `anchor_generator.py`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `daemon unreachable` | `bash ~/.claude/plugins/nautilus-compass/daemon_start.sh` |
| `no project memory found` | Set `NAUTILUS_COMPASS_PROJECT=<encoded-path>` env var |
| GBK garbled output on Windows | Add `"PYTHONIOENCODING": "utf-8"` to MCP `env` |
| First call slow (~30 s) | Cold-load of bge-m3 (2.27 GB). Subsequent calls <300 ms. |

## License

MIT · part of the Nautilus open-source platform.

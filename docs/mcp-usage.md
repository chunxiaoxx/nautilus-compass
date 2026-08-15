# MCP server usage · nautilus-compass

**Status: v1.0.0 stable** · JSON-RPC 2.0 over stdio / TCP / **TLS** / **mTLS** · stdlib + optional `cryptography` for TLS cert generation.

The nautilus-compass MCP server exposes the user's cross-agent memory graph to
any MCP client (Claude Code, Claude Desktop, Cursor, Cline, Hermes, OpenClaw,
custom agents). Seven tools cover write (`ingest_obs`), semantic read
(`recall`, `session_search`, `profile`), and drift audit (`drift_check`,
`drift_history`, `feedback_log`). rc2 adds `resources/*` so peers can
stream each other's session logs over the same protocol.

## v1.0.0 production stack (TL;DR)

Everything below is opt-in · plaintext stdio stays the default for
single-host dev.

| Concern | Flag / API | Notes |
|---|---|---|
| AuthN | `--token TOKEN:scope1,scope2` (repeat) or `--token-file TOKENS.json` | Out-of-band rotation via the JSON file |
| AuthZ (RBAC) | Scope set per token · `tools.read` / `tools.write` / `resources.read` / `*` | `tools/list` is scope-filtered; denied calls raise -32003 |
| TLS | `--tls-cert PATH --tls-key PATH` | Both required · server banner announces `(tls)` |
| mTLS | add `--tls-client-ca PATH` | Every peer must present a cert signed by that CA |
| Rate limit | `--rate-limit TOKEN=rps/burst` (repeat) | Token-bucket · `-32029` with exact retry-in delay |
| Status | `server/status` method | Unauthenticated aggregates · active/total conns, msgs, uptime |
| Resources | `resources/list` + `resources/read` | `compass://session/<id>` URIs · per-token filtering |

**Run the 30-second end-to-end demo:**

```bash
python examples/a2a_tls_demo.py
```

Generates a CA + server + two client certs in a tempdir, boots an
mTLS daemon, runs an observer peer (writes 2 observations · `tools.write`
scope) + a reader peer (fetches them via `resources/read` · `resources.read`
scope), prints `PROOF · banner=... (tls) · wrote=2 · read=468B over mTLS`,
tears everything down. No network, no external CA.

**Client library (`mcp_client.MCPClient`) covers all of it:**

```python
from mcp_client import MCPClient
with MCPClient(host="compass.example.com", port=8766,
               token="observer",
               tls=True, tls_ca_cert="ca.pem",
               tls_client_cert="peer.pem",    # mTLS
               tls_client_key="peer.pem",
               rate_limit_retries=3) as c:    # auto-backoff on -32029
    c.call_tool("ingest_obs", {...})
    for r in c.list_resources():
        print(r["uri"], c.read_resource(r["uri"])["text"][:80])
```

Full deep-dive per concern below · the rc1 raw-JSON-RPC walkthrough is
still valid for non-Python clients and sits further down the page.

## Prereqs

- Python 3.9+ · stdlib only on the MCP side
- `nautilus-compass` plugin installed at `~/.claude/plugins/nautilus-compass`
- `compass` daemon running on `127.0.0.1:9876` (started by
  `daemon_start.sh`, or lazy-spawned on first `recall` call)

### Windows runtime authority

Use one explicit interpreter for dependency checks, daemon startup, and the
functional readiness probe. The launcher first reads `COMPASS_PYTHON`, then
tries the repository-local `.venv\Scripts\python.exe`, and only then falls
back to `python` on `PATH`:

```powershell
$env:COMPASS_PYTHON = "C:\path\to\nautilus-compass\.venv\Scripts\python.exe"
powershell -ExecutionPolicy Bypass -File .\daemon_start.ps1
python .\doctor.py --json
```

The launcher fails closed when model dependencies cannot import, when another
daemon only answers `ping` but cannot complete `recall`, or when the running
daemon does not match the selected source tree. It never replaces or stops an
unknown process automatically.

## Register in Claude Code

Add to `~/.claude/.mcp.json` (or the project-scoped `.mcp.json`):

```json
{
  "mcpServers": {
    "nautilus-compass": {
      "command": "python3",
      "args": ["~/.claude/plugins/nautilus-compass/mcp_server.py"]
    }
  }
}
```

Windows users: replace `python3` with the full path to a 3.9+ interpreter,
and expand `~`.

Restart Claude Code. The server appears under `/mcp` and the seven tools
become available to the model.

## Register in Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nautilus-compass": {
      "command": "/usr/bin/python3",
      "args": ["/Users/<you>/.claude/plugins/nautilus-compass/mcp_server.py"]
    }
  }
}
```

## Tools

### `recall(query, project?, top_k=5)`

Semantic recall over `~/.claude/projects/<project>/memory/session_*.md` using
BGE-m3 cosine similarity. Returns top-k hits plus any session from the last
24h not already in top-k (recency boost). `project` defaults to the most
recently modified project dir.

### `drift_check(prompt, project?)`

Black-box persona drift detector. Embeds `prompt`, compares against 25
positive anchors (aligned behavior) and 35 negative anchors (drift
exemplars). Returns `{drift_score, alignment, deviation, alert}`. Use before
executing a high-risk action to catch prompt injection / persona hijack.

### `ingest_obs(name, description?, body?, type?, concept?, drift?, ...)`

Write one observation into the user's memory. Includes a mandatory `drift`
field (`green`/`yellow`/`red`) so agents self-audit their own behavior per
write. The single differentiator versus `claude-mem` and similar packages.

### `drift_history(days=30, project_filter?)`

Cross-project drift timeline. Returns `{green, yellow, red}` counts plus the
top RED sessions with their `drift_signals`.

### `session_search(query, drift?, type?, days=60, top_k=5)`

Keyword search across session markdown files. Supports `drift`
(`green/yellow/red`) and `type` (`bugfix/feature/refactor/...`) filters.

### `profile(days=90)`

Aggregated user profile: top projects, work-type distribution, drift
distribution. v1.0 ships server-side; v1.1 target is client-side E2EE
aggregation.

### `feedback_log(direction, reason)`

Log true-positive / false-positive signals for adaptive anchor retraining.
After N signals, run `python feedback.py retrain` to refresh anchor weights.

## Verifying integrity

Every session write updates a SHA-256 Merkle chain at
`<memory_dir>/.chain.json`. Verify at any time:

```
python ~/.claude/plugins/nautilus-compass/compass_verify.py --all
```

Exit code 1 if any chain shows tampered or missing files.

## A2A (agent-to-agent) use

Two agents on the same machine can share the same memory by both speaking
MCP to this server. Recommended pattern:

```
agent-A --stdio-> mcp_server.py --tcp-> daemon (port 9876)
agent-B --stdio-> mcp_server.py --tcp-> daemon (port 9876)
```

Each agent gets its own `mcp_server.py` subprocess · all three share the
single daemon process holding the BGE-m3 model in memory.

For cross-machine A2A, bind the MCP server on TCP:

```
python mcp_server.py --transport tcp --host 0.0.0.0 --port 8766 --token $(openssl rand -hex 16)
```

Every TCP client's first JSON-RPC call must be `initialize` with
`params.authToken` matching `--token` (or the `COMPASS_MCP_TOKEN` env
var). Unauthenticated clients receive a single `-32001 unauthorized`
error and are disconnected. The token is stripped from the message
before the handler sees it, so it never appears in logs or reply
payloads. Bind to `127.0.0.1` + tunnel over SSH for the safest setup ·
`0.0.0.0` only behind a VPN or with firewall rules.

Verify a TCP deployment from another machine:

```
python scripts/mcp_smoke_rpc.py --transport tcp \
    --host HOST --port 8766 --token "$COMPASS_MCP_TOKEN" \
    --tool drift_check --query "test drift"
```

The smoke script runs the full 3-step handshake (initialize → tools/list
→ tools/call) over either transport and exits non-zero on any failure.

For long-lived A2A callers (agent → agent over TCP), prefer
`mcp_client.MCPClient` over raw sockets — it reconnects transparently
on `ConnectionReset` / `BrokenPipe` / timeout with exponential backoff,
re-runs `initialize` after reconnect, and only raises `MCPClientError`
after exhausting `max_retries` (or immediately on permanent failures
like bad tokens):

```python
from mcp_client import MCPClient

with MCPClient(host="peer.internal", port=8766, token=os.environ["COMPASS_MCP_TOKEN"]) as c:
    hits = c.call_tool("recall", {"query": "last auth change", "top_k": 5})
    if c.reconnect_count:
        log.warning(f"session had {c.reconnect_count} reconnects · last: {c.last_reconnect_reason}")
```

## Server-side logging (`logging/setLevel` + `notifications/message`)

rc2 implements the MCP 2024-11-05 logging spec. The session owner
(client) chooses how chatty the server should be; below-threshold records
are dropped silently before they hit the wire.

```python
client = MCPClient.spawn(["python", "mcp_server.py"])
client.set_log_level("debug")              # default is "info"
captured = []
client.call_tool(
    "long_task",
    arguments={"steps": 3},
    progress_cb=lambda p: print("progress", p),
    log_cb=captured.append,                # receives notifications/message frames
)
# captured = [
#   {"level": "info",  "data": "long_task starting · steps=3"},
#   {"level": "debug", "data": "long_task step 1/3"},
#   {"level": "debug", "data": "long_task step 2/3"},
#   {"level": "debug", "data": "long_task step 3/3"},
# ]
```

**Spec levels** (least → most severe): `debug` · `info` · `notice` ·
`warning` · `error` · `critical` · `alert` · `emergency`.

**Per-session, per-connection.** Each TCP socket holds its own level
dict — one chatty client doesn't drown another. `set_log_level("warning")`
mid-session immediately filters subsequent records on that connection.

**Invalid level → `-32602`.** No silent downgrade — the server rejects
unknown levels (e.g. `"loud"`, integers) so the client knows to retry
with a spec value.

**Capabilities.** `initialize` returns `"capabilities": {"tools": {},
"resources": {}, "logging": {}}`. Clients can probe before issuing
`logging/setLevel`.

For tool authors: receive an optional `log` callable in your tool fn
signature (`def tool_x(args, emit=None, is_cancelled=None, log=None)`)
and call `log("info", "starting...")`. The frame is gated by the
session threshold for free.

## Troubleshooting

- **tools/list empty** · daemon not running, start it:
  - Linux/macOS: `bash ~/.claude/plugins/nautilus-compass/daemon_start.sh`
  - Windows PowerShell: `powershell -ExecutionPolicy Bypass -File ~/.claude/plugins/nautilus-compass/daemon_start.ps1`
- **`recall` returns empty hits** · BGE-m3 model not in cache. First call
  downloads 2.3 GB; set `ZMM_BGE_MODEL` env to a pre-downloaded snapshot
  path to skip download.
- **`drift_check` alert=true on legit prompt** · retrain anchors with
  `feedback_log(direction="bad", reason="...")` followed by
  `python feedback.py retrain`.
- **Protocol error in Claude Code UI** · the server logs JSON-RPC errors to
  stderr. Run it standalone to see them:
  `python mcp_server.py < /dev/null`

## Raw JSON-RPC (non-Claude clients)

The server speaks MCP 2024-11-05 JSON-RPC 2.0 over stdio · one request per
line, one response per line. Minimum 3-step handshake for any client:

```
→ {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"my-client","version":"0.1.0"}}}
← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"nautilus-compass","version":"1.0.0-rc1"}}}

→ {"jsonrpc":"2.0","id":2,"method":"tools/list"}
← {"jsonrpc":"2.0","id":2,"result":{"tools":[... 7 tools ...]}}

→ {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"recall","arguments":{"query":"last auth change","top_k":3}}}
← {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"..."}]}}
```

Python one-shot smoke test (ships in the repo as
`scripts/mcp_smoke_rpc.py`):

```python
import json, subprocess, sys
proc = subprocess.Popen(
    [sys.executable, "mcp_server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
)
def rpc(method, params=None, rid=1):
    proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":rid,"method":method,"params":params or {}}) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())

print(rpc("initialize", {"protocolVersion":"2024-11-05","clientInfo":{"name":"smoke","version":"0"}}, 1))
print(rpc("tools/list", rid=2))
```

Errors follow JSON-RPC conventions: `error.code = -32601` for unknown
method, `-32602` for bad params, `-32000` for daemon-down (recoverable ·
check `tools/list empty` troubleshooting above).

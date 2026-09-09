# Compass Standard-Remote MCP (Streamable-HTTP over public HTTPS) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate the compass MCP that Claude Code consumes from the current `stdio-bridge → SSH-tunnel → localhost:9877 raw-TCP` chain to a **standard remote MCP over public HTTPS** (spec Streamable-HTTP), so Claude Code connects natively with `type: http` + `url` — **no `mcp_stdio_to_cloud.py` bridge, no `ssh -L 9877` tunnel**.

**Architecture:** Add a thin **Streamable-HTTP MCP server** (`mcp_http_server.py`) that reuses the existing 17-tool registry `mcp_server.TOOLS` (`{name: {"fn", "schema"}}`) via the low-level `mcp.server.lowlevel.Server` + `StreamableHTTPSessionManager`. It binds `127.0.0.1:8097`; a bearer-token auth middleware fronts it. **Platform-turf (coordinate, do not apply unilaterally):** nginx server block `compass.nautilus.social` `location = /mcp → 127.0.0.1:8097` + certbot TLS + DNS. This mirrors the already-proven **HR agent** pattern (`hr.nautilus.social/mcp` → FastMCP `mcp.run(transport="streamable-http")` on 8090, behind nginx + certbot).

**Tech Stack:** Python 3, official `mcp` SDK **1.16.0** (`mcp.server.lowlevel.Server`, `StreamableHTTPSessionManager`), Starlette + uvicorn, `anyio.to_thread` (compass tool fns are sync + do blocking daemon socket I/O), nginx, certbot, systemd.

---

## Context (grounded 2026-07-06)

- **Two compass repos exist — this work is in the PLUGIN repo** `~/.claude/plugins/nautilus-compass` (the MCP/memory product), NOT the FDE project repo `C:\Users\chunx\Projects\nautilus-compass`.
- **Current live path** (works, but fragile): Claude Code `type: stdio` → `ops/mcp_stdio_to_cloud.py` → `127.0.0.1:9877` (SSH `-fN -L 9877:127.0.0.1:9877 cloud`) → cloud `compass-mcp-tcp.service` (`mcp_server.py --transport tcp --host 127.0.0.1 --port 9877 --token-file /etc/compass/tokens.json`, pid 2637249, v2.3.0).
- **Why change:** 3 hops (bridge + tunnel + localhost-TCP) inherit SSH/tunnel/cloud-load failure modes. On 2026-07-06 a cloud overload made the tunnelled handshake exceed the 30s MCP client timeout → the compass MCP dropped for the whole session.
- **Reuse, don't reinvent (anchor #5):** the platform already ships standard remote MCP.
  - **HR MCP (golden reference):** `hr-mcp-server/server.py` uses `from mcp.server.fastmcp import FastMCP`; `mcp.run(transport="streamable-http")` on `MCP_PORT=8090`; nginx `hr-agent.conf`: `server_name hr.nautilus.social; location = /mcp { proxy_pass http://127.0.0.1:8090; }` + certbot acme-challenge TLS. **Claude Code connects natively** to `https://hr.nautilus.social/mcp` via `type: http`.
  - Platform MCP: `nautilus-engine/mcp_server.py` on 8096 (hand-rolled `http.server`, `POST /mcp` = 200) — custom shape, not the pattern to copy.
- **Compass gateway `compass_http.py`'s `/mcp/*`** is REST-style (split routes, no JSON-RPC envelope, no SSE) — **Claude Code cannot connect to it natively**. That is why this plan builds a spec Streamable-HTTP surface instead of pointing Claude Code at the existing `/mcp/*`.
- **Registry to reuse:** `python -c "import mcp_server; print(len(mcp_server.TOOLS))"` → 17. Each entry: `{"fn": <callable args:dict -> dict>, "schema": {"name","description","inputSchema"}}`. All fns are sync and dict-in/dict-out; `drift_check`/`long_task` in `mcp_server.py` take `(args)` (extras default None) — the generic wrapper `fn(args)` is correct.
- **mcp SDK confirmed 1.16.0**; `mcp.server.lowlevel.Server`, `StreamableHTTPSessionManager`, `FastMCP.streamable_http_app` all importable.

## Turf boundaries (charter §4 — do NOT cross unilaterally)

- **compass-executable (this repo):** `mcp_http_server.py`, auth middleware, tests, systemd unit *draft*, local end-to-end verification, Claude Code client config, docs/memory.
- **platform-soul turf (COORDINATE via outbound to platform dialog):** nginx server block, `compass.nautilus.social` DNS, certbot cert, applying/enabling anything on the shared cloud VM. Tasks 6–7 produce exact artifacts as a **handoff**, they do not apply them.

## Security (mandatory — non-skippable)

Compass exposes WRITE tools (`ingest_obs`, `governance_dispatch/plan/audit`, `proof_of_impact`, `add_worker`). Publishing them over public HTTPS **requires auth before any deploy**. Reuse the existing `/etc/compass/tokens.json` bearer tokens (the TCP service already gates on it). No unauthenticated public exposure — Task 3 gates Task 6.

---

## Task 0: Prep — branch + pin API + smoke the registry

**Files:**
- Work in: `~/.claude/plugins/nautilus-compass` (git repo, currently on `main`, `recall.py` modified)

**Step 1: Create a feature branch (R4 — never ship on `main`)**

```bash
cd ~/.claude/plugins/nautilus-compass
git stash -u    # park the unrelated recall.py edit if it is not yours to commit; else leave it
git checkout -b feat/mcp-standard-remote-http
```

**Step 2: Pin the SDK call-tool return contract for 1.16.0**

Run:
```bash
python - <<'PY'
import inspect, mcp
from mcp.server.lowlevel import Server
print("mcp", getattr(mcp, "__version__", "?"))
print(inspect.getsource(Server.call_tool))   # confirm decorated fn return type (list[ContentBlock] vs (content, structured))
PY
```
Expected: shows the decorator signature so Task 1 returns the exact accepted type (in 1.16 a `list[types.TextContent]` is accepted).

**Step 3: Smoke the registry import (no network)**

Run:
```bash
python -c "import mcp_server as m; assert len(m.TOOLS)==17; e=m.TOOLS['recall']; assert 'fn' in e and e['schema']['inputSchema']; print('registry OK', list(m.TOOLS)[:3])"
```
Expected: `registry OK ['ingest_obs', 'drift_history', 'session_search']`

**Step 4: Commit the branch marker (empty)**

```bash
git commit --allow-empty -m "chore: start standard-remote MCP (streamable-http) branch"
```

---

## Task 1: Streamable-HTTP MCP server that reuses the 17-tool registry

**Files:**
- Create: `~/.claude/plugins/nautilus-compass/mcp_http_server.py`
- Test: `~/.claude/plugins/nautilus-compass/tests/test_mcp_http_server.py`

**Step 1: Write the failing test (tools listed + one tool round-trips)**

```python
# tests/test_mcp_http_server.py
import json
import pytest
import mcp_http_server as srv
import mcp_server as cmp


@pytest.mark.anyio
async def test_lists_all_17_tools_with_schemas():
    tools = await srv._list_tools()
    assert len(tools) == 17
    names = {t.name for t in tools}
    assert "recall" in names and "ingest_obs" in names
    # every tool carries a non-empty object input schema
    for t in tools:
        assert t.inputSchema.get("type") == "object"


@pytest.mark.anyio
async def test_call_tool_dispatches_to_registry(monkeypatch):
    monkeypatch.setitem(cmp.TOOLS, "recall",
                        {"fn": lambda a: {"echo": a}, "schema": cmp.TOOLS["recall"]["schema"]})
    out = await srv._call_tool("recall", {"query": "hi"})
    assert out[0].type == "text"
    assert json.loads(out[0].text)["echo"] == {"query": "hi"}


@pytest.fixture
def anyio_backend():
    return "asyncio"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mcp_http_server.py -v`
Expected: FAIL — `ModuleNotFoundError: mcp_http_server`

**Step 3: Write minimal implementation**

```python
# mcp_http_server.py — compass standard-remote MCP (spec Streamable-HTTP).
# Reuses the 17-tool registry in mcp_server.TOOLS. Mirrors the HR agent pattern.
# Run:  uvicorn mcp_http_server:app --host 127.0.0.1 --port 8097
from __future__ import annotations

import contextlib
import json

import anyio
import mcp.types as types
import mcp_server as cmp
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

server: Server = Server("nautilus-compass")


@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    out: list[types.Tool] = []
    for meta in cmp.TOOLS.values():
        s = meta["schema"]
        out.append(types.Tool(
            name=s["name"],
            description=s.get("description", ""),
            inputSchema=s.get("inputSchema", {"type": "object"}),
        ))
    return out


@server.call_tool()
async def _call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    meta = cmp.TOOLS.get(name)
    if not meta:
        raise ValueError(f"unknown tool: {name}")
    # compass fns are SYNC and do blocking socket I/O to the BGE daemon —
    # never call them directly on the event loop.
    result = await anyio.to_thread.run_sync(meta["fn"], arguments or {})
    return [types.TextContent(type="text",
                              text=json.dumps(result, ensure_ascii=False, indent=2))]


# stateless=True + json_response=True → simplest request/response HTTP;
# no server-push needed for a tools-only server.
_session_manager = StreamableHTTPSessionManager(
    app=server, json_response=True, stateless=True,
)


async def _handle(scope: Scope, receive: Receive, send: Send) -> None:
    await _session_manager.handle_request(scope, receive, send)


@contextlib.asynccontextmanager
async def _lifespan(_app):
    async with _session_manager.run():
        yield


app = Starlette(routes=[Mount("/mcp", app=_handle)], lifespan=_lifespan)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_mcp_http_server.py -v`
Expected: PASS (both tests). If `call_tool` return type mismatches 1.16, adjust per Task 0 Step 2 output and re-run.

**Step 5: Commit**

```bash
git add mcp_http_server.py tests/test_mcp_http_server.py
git commit -m "feat(mcp): streamable-http server reusing 17-tool registry"
```

---

## Task 2: Local end-to-end — Claude Code connects natively over http

**Files:**
- Test: `~/.claude/plugins/nautilus-compass/scripts/smoke_http_mcp.py`

**Step 1: Write the failing smoke test (spec 3-step handshake over HTTP)**

```python
# scripts/smoke_http_mcp.py — POST JSON-RPC to the streamable-http endpoint
import json, sys, urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8097/mcp"
HDR = {"Content-Type": "application/json",
       "Accept": "application/json, text/event-stream"}

def rpc(method, params=None, rid=1):
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method,
                       "params": params or {}}).encode()
    req = urllib.request.Request(URL, data=body, headers=HDR, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read().decode()
    # streamable-http may answer as SSE frames or plain json
    if raw.lstrip().startswith("event:") or "data:" in raw[:20]:
        raw = raw.split("data:", 1)[1].strip()
    return json.loads(raw)

init = rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                          "clientInfo": {"name": "smoke", "version": "0"}}, 1)
assert init["result"]["serverInfo"]["name"] == "nautilus-compass", init
tl = rpc("tools/list", {}, 2)
assert len(tl["result"]["tools"]) == 17, tl
print("HTTP MCP OK · tools:", len(tl["result"]["tools"]))
```

**Step 2: Boot the server + run smoke (needs BGE daemon on 9876 for real tool calls; init/list do not)**

Run (two shells):
```bash
uvicorn mcp_http_server:app --host 127.0.0.1 --port 8097 &
python scripts/smoke_http_mcp.py http://127.0.0.1:8097/mcp
```
Expected: `HTTP MCP OK · tools: 17`. If the SDK requires a session-id handshake in stateless mode, capture `Mcp-Session-Id` from the init response headers and echo it on subsequent calls (adjust smoke script).

**Step 3: Verify Claude Code itself connects (the real acceptance)**

Add a **scratch** MCP entry (do not overwrite the working stdio one yet) to `~/.claude.json`:
```json
"compass-http-test": { "type": "http", "url": "http://127.0.0.1:8097/mcp" }
```
Restart Claude Code → `/mcp` → confirm `compass-http-test` connects and its tools appear. This is the gate proving `type: http` works natively before touching cloud.

**Step 4: Commit**

```bash
git add scripts/smoke_http_mcp.py
git commit -m "test(mcp): local streamable-http end-to-end smoke + Claude Code type:http verify"
```

---

## Task 3: Bearer-token auth middleware (GATES all public exposure)

**Files:**
- Modify: `~/.claude/plugins/nautilus-compass/mcp_http_server.py`
- Test: `~/.claude/plugins/nautilus-compass/tests/test_mcp_http_auth.py`

**Step 1: Failing test — no/invalid token → 401, valid → 200**

```python
# tests/test_mcp_http_auth.py
import json
from starlette.testclient import TestClient
import mcp_http_server as srv

def _init_body():
    return json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize",
        "params":{"protocolVersion":"2024-11-05","capabilities":{},
                  "clientInfo":{"name":"t","version":"0"}}})

def test_missing_token_401(monkeypatch):
    monkeypatch.setattr(srv, "VALID_TOKENS", {"good"})
    c = TestClient(srv.app)
    r = c.post("/mcp", data=_init_body(),
               headers={"Content-Type":"application/json",
                        "Accept":"application/json, text/event-stream"})
    assert r.status_code == 401

def test_valid_token_ok(monkeypatch):
    monkeypatch.setattr(srv, "VALID_TOKENS", {"good"})
    c = TestClient(srv.app)
    r = c.post("/mcp", data=_init_body(),
               headers={"Content-Type":"application/json",
                        "Accept":"application/json, text/event-stream",
                        "Authorization":"Bearer good"})
    assert r.status_code == 200
```

**Step 2: Run → FAIL** (`VALID_TOKENS` undefined / no 401)

Run: `python -m pytest tests/test_mcp_http_auth.py -v`

**Step 3: Add auth middleware to `mcp_http_server.py`**

```python
import os
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


def _load_tokens() -> set[str]:
    # Reuse the same tokens the TCP service already trusts.
    path = os.environ.get("COMPASS_TOKENS_FILE", "/etc/compass/tokens.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # tokens.json shape: {"<token>": ["scope", ...], ...} OR {"tokens":[...]}
        if isinstance(data, dict) and "tokens" not in data:
            return set(data.keys())
        return set(data.get("tokens", []))
    except Exception:
        return set(filter(None, os.environ.get("COMPASS_MCP_TOKENS", "").split(",")))


VALID_TOKENS: set[str] = _load_tokens()


class _BearerAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/mcp"):
            tok = request.headers.get("authorization", "")
            tok = tok[7:] if tok.lower().startswith("bearer ") else request.headers.get("x-agent-key", "")
            if not VALID_TOKENS or tok not in VALID_TOKENS:
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


# rebuild app WITH middleware (replace the Task-1 `app = Starlette(...)` line)
app = Starlette(routes=[Mount("/mcp", app=_handle)],
                middleware=[Middleware(_BearerAuth)],
                lifespan=_lifespan)
```

**Step 4: Run → PASS**; also re-run Task 1 + Task 2 smoke with `Authorization: Bearer <token>` header.

**Step 5: Commit**

```bash
git add mcp_http_server.py tests/test_mcp_http_auth.py
git commit -m "feat(mcp): bearer-token auth middleware reusing /etc/compass/tokens.json"
```

---

## Task 4: systemd unit (draft) — mirror hr-mcp deploy

**Files:**
- Create: `~/.claude/plugins/nautilus-compass/ops/compass-mcp-http.service`

**Step 1: Write the unit (draft — applied on cloud only via Task 6 handoff)**

```ini
[Unit]
Description=Nautilus Compass · standard-remote MCP (streamable-http)
After=network.target compass.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/nautilus-compass
Environment=COMPASS_TOKENS_FILE=/etc/compass/tokens.json
Environment=COMPASS_DAEMON_HOST=127.0.0.1
Environment=COMPASS_DAEMON_PORT=9876
ExecStart=/usr/bin/python3 -m uvicorn mcp_http_server:app --host 127.0.0.1 --port 8097
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Step 2: Lint locally**

Run: `python -c "import configparser,io; configparser.ConfigParser(strict=False).read_string(open('ops/compass-mcp-http.service').read()); print('unit parses')"`
Expected: `unit parses`

**Step 3: Commit**

```bash
git add ops/compass-mcp-http.service
git commit -m "ops(mcp): systemd unit draft for streamable-http service (port 8097)"
```

---

## Task 5: nginx snippet (draft) + Claude Code client config (draft)

**Files:**
- Create: `~/.claude/plugins/nautilus-compass/ops/nginx/compass-mcp.conf.sample`
- Create: `~/.claude/plugins/nautilus-compass/examples/mcp_configs/claude_code_http.json`

**Step 1: nginx sample (mirror hr-agent.conf `location = /mcp`)**

```nginx
# compass.nautilus.social · standard-remote MCP  (PLATFORM applies this — see Task 6)
server {
    listen 443 ssl;
    server_name compass.nautilus.social;
    # ssl_certificate ...  (certbot-managed · see Task 6)

    location = /mcp {
        proxy_pass http://127.0.0.1:8097/mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Authorization $http_authorization;   # pass bearer through
        proxy_buffering off;                                  # streamable-http
        proxy_read_timeout 120s;
    }
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
}
```

**Step 2: Claude Code client config sample**

```json
{
  "_doc": "Replaces the stdio bridge entry once Task 6 deploy is verified.",
  "mcpServers": {
    "nautilus-compass": {
      "type": "http",
      "url": "https://compass.nautilus.social/mcp",
      "headers": { "Authorization": "Bearer ${COMPASS_MCP_TOKEN}" }
    }
  }
}
```

**Step 3: Commit**

```bash
git add ops/nginx/compass-mcp.conf.sample examples/mcp_configs/claude_code_http.json
git commit -m "docs(mcp): nginx + Claude Code type:http config samples (platform handoff)"
```

---

## Task 6: Platform-turf handoff — deploy on cloud (COORDINATE, do not self-apply)

> **This task is platform-soul turf** (nginx, DNS, certs, shared VM). compass does NOT run these. Produce an outbound to the platform dialog with the exact artifacts and the acceptance check. Applied only after platform confirms.

**Step 1: Write the outbound to the platform dialog** (semantic channel `ingest_obs(project="nautilus-core", thread_role="outbound")`, or a `session_*.md` if MCP is down). Include:
- The three files: `mcp_http_server.py`, `ops/compass-mcp-http.service`, `ops/nginx/compass-mcp.conf.sample`.
- Prereqs the platform owns: (a) DNS `compass.nautilus.social` → cloud VM `43.160.239.61`; (b) `certbot --nginx -d compass.nautilus.social`; (c) `git pull` compass on `/home/ubuntu/nautilus-compass`; (d) `systemctl enable --now compass-mcp-http.service`; (e) `nginx -t && systemctl reload nginx`.
- Acceptance: `curl -s https://compass.nautilus.social/mcp -X POST -H 'Authorization: Bearer <tok>' -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'` returns 17 tools.

**Step 2: After platform confirms deploy — verify end-to-end from the Windows client**

Run the acceptance curl above from the local machine (public HTTPS, no tunnel). Expected: 17 tools.

**Step 3: Do NOT commit anything in this task** (no local code change; it is a coordination gate).

---

## Task 7: Cut over Claude Code + decommission bridge/tunnel

**Files:**
- Modify: `~/.claude.json` (mcpServers → `nautilus-compass`)

**Step 1: Back up config, then switch the entry to `type: http`**

```bash
cp ~/.claude.json ~/.claude.json.bak-pre-http-cutover-$(date +%Y%m%d-%H%M%S)
```
Replace the `nautilus-compass-cloud` stdio entry with the `type: http` entry from `examples/mcp_configs/claude_code_http.json` (keep the old stdio block commented in a `.bak` for one week as rollback).

**Step 2: Restart Claude Code → verify native connect**

`/mcp` → `nautilus-compass` connected over http, tools present. Run a `recall` from the model to confirm a real round-trip (needs cloud daemon healthy).

**Step 3: Decommission the tunnel + bridge (only after ≥1 clean session)**

- Stop the local tunnel: identify `ssh -fN -L 9877 ... cloud` PID and `kill <pid>` (it is your own Windows process).
- Remove the tunnel auto-start from `ops/compass_start.ps1` (and `compass_forward_watchdog.ps1` if it re-spawns it).
- Leave `ops/mcp_stdio_to_cloud.py` in-repo (do not delete) but drop it from the active launch path.

**Step 4: Commit the launcher change + update docs**

```bash
git add ops/compass_start.ps1 ops/compass_forward_watchdog.ps1 docs/mcp-usage.md
git commit -m "feat(mcp): cut over to standard-remote http · retire stdio bridge + ssh tunnel from launch path"
```

**Step 5: Rollback path (documented, not executed):** restore `~/.claude.json.bak-pre-http-cutover-*` and re-enable the tunnel in `compass_start.ps1` → back to the stdio-bridge path within 2 minutes.

---

## Task 8: Land the branch + record

**Step 1:** Open PR `feat/mcp-standard-remote-http` → `main`; summary = this plan's Goal + the grounded acceptance evidence from Tasks 2/6/7.

**Step 2:** Update SSOT + memory: note the transport change and that the tunnel/bridge are retired from the launch path; write a compass memory `session_2026xxxx_compass_mcp_standard_remote_http` with the final verified curl output.

**Step 3:** Outbound to platform dialog confirming the deploy is live + the acceptance curl passing.

---

## Definition of Done (external, verifiable)

1. `curl https://compass.nautilus.social/mcp` (bearer token) → 17 tools, from the Windows machine, **with no SSH tunnel running**.
2. Claude Code `/mcp` shows `nautilus-compass` connected via `type: http`; a model `recall` round-trips.
3. `ops/compass_start.ps1` no longer starts an `ssh -L 9877` tunnel; the stdio bridge is off the active path (kept in-repo for rollback).
4. Auth verified: an unauthenticated `POST /mcp` returns 401.

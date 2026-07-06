#!/usr/bin/env python3
"""Live smoke of the streamable-http compass MCP endpoint.

Runs the spec handshake (initialize -> notifications/initialized -> tools/list)
over a real socket. Handles both application/json and text/event-stream
framing, and carries the Mcp-Session-Id header when the server assigns one.

Usage:
    COMPASS_MCP_TOKENS=smoketoken uvicorn mcp_http_server:app \
        --host 127.0.0.1 --port 8097 &
    python scripts/smoke_http_mcp.py http://127.0.0.1:8097/mcp smoketoken
"""
import json
import sys
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8097/mcp/"
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""

_SESSION = {"id": None}


def _headers():
    h = {"Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    if _SESSION["id"]:
        h["Mcp-Session-Id"] = _SESSION["id"]
    return h


def _parse(raw: str):
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith("event:") or "\ndata:" in raw or raw.startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return None
    return json.loads(raw)


def rpc(method, params=None, rid=1, notify=False):
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        payload["id"] = rid
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers=_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        sid = r.headers.get("Mcp-Session-Id")
        if sid:
            _SESSION["id"] = sid
        body = r.read().decode()
    return _parse(body)


def main():
    init = rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "smoke", "version": "0"}}, 1)
    assert init and init.get("result", {}).get("serverInfo", {}).get("name") == "nautilus-compass", init
    print("init OK · server =", init["result"]["serverInfo"]["name"],
          init["result"]["serverInfo"]["version"], "· session =", _SESSION["id"])

    rpc("notifications/initialized", notify=True)

    tl = rpc("tools/list", {}, 2)
    tools = tl.get("result", {}).get("tools", [])
    assert len(tools) == 17, f"expected 17 tools, got {len(tools)}: {tl}"
    print("tools/list OK ·", len(tools), "tools ·", ", ".join(t["name"] for t in tools[:5]), "...")
    print("HTTP MCP SMOKE PASS")


if __name__ == "__main__":
    main()

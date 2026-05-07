"""compass v0.9 · A2A (Agent-to-Agent) Protocol Adapter.

让任何 A2A 兼容 agent 把 compass 当作 memory layer 使用.
Nautilus 平台力推 A2A · 这是 Tier 1 接入路径.

A2A Protocol (Google · 2025):
  Agent envelope:
    {
      "protocol": "a2a/v1",
      "from": "ag_xxx",
      "to": "compass-memory",
      "ts": "2026-05-05T10:00:00Z",
      "type": "STORE_OBS" | "RETRIEVE_MEMORY" | "QUERY_PROFILE" | "QUERY_DRIFT_HISTORY",
      "payload": {...}
    }

Capabilities exposed:
  STORE_OBS              · 写一条 observation
  RETRIEVE_MEMORY        · 召回相关 memory
  QUERY_PROFILE          · 查用户画像
  QUERY_DRIFT_HISTORY    · 查 AI 漂移历史

Run as standalone HTTP service:
  python a2a_adapter.py serve --port 8765
  → POST http://localhost:8765/a2a/messages
  → GET  http://localhost:8765/a2a/capabilities

Or import as library:
  from a2a_adapter import handle_a2a_message
  reply = handle_a2a_message(envelope_dict)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))

CAPABILITIES = {
    "STORE_OBS": {
        "description": "Write a single observation (with drift self-audit) to user's cross-agent memory.",
        "input": {
            "name": "string",
            "description": "string",
            "body": "string",
            "type": "bugfix|feature|refactor|discovery|decision|change",
            "concept": "gotcha|pattern|trade-off|how-it-works|why-it-exists|problem-solution|what-changed",
            "drift": "green|yellow|red",
            "drift_signals": "list[string]",
            "agent_type": "string · classifier of source agent",
        },
        "output": {"obs_id": "string", "status": "ok|err"},
    },
    "RETRIEVE_MEMORY": {
        "description": "Cross-agent semantic + keyword search over user's memory.",
        "input": {
            "query": "string",
            "top_k": "int=5",
            "cross_agent": "bool=true",
            "drift_filter": "green|yellow|red|null",
            "agent_filter": "string|null · limit to one agent",
        },
        "output": {"hits": "list of {score, name, drift, agent_type, path}"},
    },
    "QUERY_PROFILE": {
        "description": "User profile aggregate (work types, top projects, drift distribution).",
        "input": {"days": "int=90"},
        "output": {"projects": "dict", "types": "dict", "drift": "dict"},
    },
    "QUERY_DRIFT_HISTORY": {
        "description": "AI drift timeline · compass-exclusive feature (claude-mem doesn't have).",
        "input": {"days": "int=30", "project_filter": "string|null"},
        "output": {"counts": "dict", "timeline": "dict", "red_sessions": "list"},
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ok_envelope(orig: dict, payload: dict) -> dict:
    return {
        "protocol": "a2a/v1",
        "from": "compass-memory",
        "to": orig.get("from", "?"),
        "ts": _now_iso(),
        "in_reply_to": orig.get("msg_id"),
        "type": "REPLY",
        "status": "ok",
        "payload": payload,
    }


def _err_envelope(orig: dict, error: str) -> dict:
    return {
        "protocol": "a2a/v1",
        "from": "compass-memory",
        "to": orig.get("from", "?"),
        "ts": _now_iso(),
        "in_reply_to": orig.get("msg_id"),
        "type": "REPLY",
        "status": "err",
        "error": error,
    }


def _call_mcp_tool(tool_name: str, args: dict) -> str:
    """Internal: invoke compass mcp_server tool by importing module."""
    from mcp_server import TOOLS
    fn = TOOLS.get(tool_name, {}).get("fn")
    if not fn:
        return f"Error: unknown tool {tool_name}"
    result = fn(args)
    if result.get("isError"):
        return f"Error: {result['content'][0]['text']}"
    return result["content"][0]["text"]


def handle_a2a_message(envelope: dict) -> dict:
    """Main dispatcher · A2A envelope in · A2A reply envelope out."""
    if envelope.get("protocol") != "a2a/v1":
        return _err_envelope(envelope, "unsupported protocol · need a2a/v1")
    msg_type = envelope.get("type")
    payload = envelope.get("payload") or {}

    if msg_type == "STORE_OBS":
        result = _call_mcp_tool("ingest_obs", payload)
        return _ok_envelope(envelope, {"result": result})

    if msg_type == "RETRIEVE_MEMORY":
        # cross_agent default true · query session_search + recall
        ss = _call_mcp_tool("session_search", {
            "query": payload.get("query"),
            "drift": payload.get("drift_filter"),
            "top_k": payload.get("top_k", 5),
        })
        return _ok_envelope(envelope, {"result": ss})

    if msg_type == "QUERY_PROFILE":
        result = _call_mcp_tool("profile", payload)
        return _ok_envelope(envelope, {"result": result})

    if msg_type == "QUERY_DRIFT_HISTORY":
        result = _call_mcp_tool("drift_history", payload)
        return _ok_envelope(envelope, {"result": result})

    if msg_type == "DISCOVER_CAPABILITIES":
        return _ok_envelope(envelope, {"capabilities": CAPABILITIES})

    return _err_envelope(envelope, f"unknown message type: {msg_type}")


# ---- standalone HTTP service ----

def serve(port: int = 8765, host: str = "127.0.0.1"):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class A2AHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, obj: dict):
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/a2a/capabilities":
                self._send_json(200, {
                    "agent": "compass-memory",
                    "version": "0.9.0-dev",
                    "protocol": "a2a/v1",
                    "capabilities": CAPABILITIES,
                })
                return
            if self.path == "/healthz":
                self._send_json(200, {"status": "ok", "service": "compass-a2a-adapter"})
                return
            self._send_json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/a2a/messages":
                self._send_json(404, {"error": "use /a2a/messages"})
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as e:
                self._send_json(400, {"error": f"bad json: {e}"})
                return
            reply = handle_a2a_message(body)
            self._send_json(200, reply)

        def log_message(self, fmt, *a):  # quiet
            pass

    print(f"[a2a-adapter] listening on http://{host}:{port}/a2a/messages")
    print(f"  capabilities: {list(CAPABILITIES.keys())}")
    HTTPServer((host, port), A2AHandler).serve_forever()


def selftest():
    """Sanity check · DISCOVER_CAPABILITIES + STORE_OBS."""
    print("=== test 1: DISCOVER_CAPABILITIES ===")
    r1 = handle_a2a_message({
        "protocol": "a2a/v1",
        "from": "ag_test",
        "to": "compass-memory",
        "msg_id": "m1",
        "type": "DISCOVER_CAPABILITIES",
        "payload": {},
    })
    print(json.dumps(r1, ensure_ascii=False, indent=2)[:300])

    print("\n=== test 2: STORE_OBS ===")
    r2 = handle_a2a_message({
        "protocol": "a2a/v1",
        "from": "ag_a2a_test",
        "to": "compass-memory",
        "msg_id": "m2",
        "type": "STORE_OBS",
        "payload": {
            "name": "A2A 自测一条 obs",
            "description": "走 A2A protocol 写 obs · 验证 adapter 工作",
            "body": "测试 STORE_OBS 路径",
            "type": "feature",
            "concept": "how-it-works",
            "drift": "green",
            "agent_type": "custom",
        },
    })
    print(json.dumps(r2, ensure_ascii=False, indent=2)[:400])

    print("\n=== test 3: QUERY_DRIFT_HISTORY ===")
    r3 = handle_a2a_message({
        "protocol": "a2a/v1",
        "from": "ag_test",
        "to": "compass-memory",
        "msg_id": "m3",
        "type": "QUERY_DRIFT_HISTORY",
        "payload": {"days": 7},
    })
    print(json.dumps(r3, ensure_ascii=False, indent=2)[:400])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
        serve(port=port)
    elif len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    else:
        print(__doc__)
        print("\nCommands:")
        print("  python a2a_adapter.py serve [port]   · start HTTP service")
        print("  python a2a_adapter.py selftest       · run sanity tests")

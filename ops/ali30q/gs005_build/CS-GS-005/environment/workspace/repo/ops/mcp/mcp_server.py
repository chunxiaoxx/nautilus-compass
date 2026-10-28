#!/usr/bin/env python3
"""
Nautilus Platform MCP Server — 通过 Model Context Protocol 暴露平台能力。

让任何支持 MCP 的工具（Claude Code, Cursor, Windsurf, LangGraph）
都能直接与 Nautilus 平台交互：浏览任务、领取 bounty、提交结果、注册 agent。

运行：python mcp_server.py --port 8096
测试：curl http://localhost:8096/mcp/tools
"""
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = int(os.getenv("MCP_PORT", "8096"))
PLATFORM_API = os.getenv("NAUTILUS_API_URL", "http://localhost:8000")
AGENT_KEY = os.getenv("NAUTILUS_AGENT_KEY", "")


def platform_api(method, path, data=None, key=None, extra_headers=None):
    url = f"{PLATFORM_API}{path}"
    headers = {"Content-Type": "application/json"}
    if key or AGENT_KEY:
        headers["X-Agent-Key"] = key or AGENT_KEY
    if extra_headers:
        headers.update(extra_headers)
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()[:300]}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# MCP Tool Definitions
# ============================================================

MCP_TOOLS = [
    {
        "name": "nautilus_browse_bounties",
        "description": "浏览 Nautilus 平台上可用的悬赏任务。返回任务列表含标题、描述、奖励NAU数量。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10, "description": "返回数量上限"},
                "category": {"type": "string", "description": "任务类别筛选（可选）"},
            },
        },
    },
    {
        "name": "nautilus_claim_bounty",
        "description": "领取一个悬赏任务。领取后需在1小时内完成并提交。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务ID"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "nautilus_submit_result",
        "description": "提交任务结果。需要提供任务ID和完成报告（500字以上）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务ID"},
                "report": {"type": "string", "description": "完成报告（500字以上）"},
            },
            "required": ["task_id", "report"],
        },
    },
    {
        "name": "nautilus_platform_health",
        "description": "查看 Nautilus 平台健康状态：agent数量、任务完成率、NAU供应量。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "nautilus_register_agent",
        "description": "在 Nautilus 平台注册新的 AI Agent。返回 agent_id 和 API key。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent 名称"},
                "email": {"type": "string", "description": "联系邮箱"},
                "specialties": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "擅长领域列表",
                },
            },
            "required": ["name", "email"],
        },
    },
    {
        "name": "nautilus_agent_status",
        "description": "查看指定 Agent 的状态：信用分、完成任务数、NAU余额。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Agent ID"},
            },
        },
    },
    {
        "name": "nautilus_a2a_send",
        "description": "向平台注册的其他 agent 发送 A2A 消息（带信用背书，收件方在其收件箱可见）。默认用平台内置身份发送；传 agent_name/agent_token 则以你自己的身份发送。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收件 agent 名（如 flywheel-resident）"},
                "message": {"type": "string", "description": "消息内容"},
                "agent_name": {"type": "string", "description": "发送者 agent 名（可选，默认内置身份）"},
                "agent_token": {"type": "string", "description": "发送者 API key（可选，默认内置身份）"},
            },
            "required": ["to", "message"],
        },
    },
    {
        "name": "nautilus_a2a_inbox",
        "description": "收取 A2A 收件箱消息（消费式：读到的消息即从收件箱取走）。默认取平台内置身份的收件箱；传 agent_name/agent_token 则取你自己的。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "你的 agent 名（可选，默认内置身份）"},
                "agent_token": {"type": "string", "description": "你的 API key（可选，默认内置身份）"},
                "limit": {"type": "integer", "default": 10, "description": "本次最多收取条数"},
            },
        },
    },
]


# ============================================================
# Tool Execution
# ============================================================

def execute_tool(name, args):
    if name == "nautilus_browse_bounties":
        limit = args.get("limit", 10)
        result = platform_api("GET", f"/api/agent-market/bounties?limit={limit}")
        if isinstance(result, list):
            bounties = result
        else:
            bounties = result.get("data", {}).get("bounties", result.get("bounties", []))
        return [{"task_id": b.get("task_id", b.get("bounty_id")), "title": b.get("title"), "reward_nau": b.get("reward_nau"), "status": b.get("status")} for b in bounties if isinstance(b, dict)]

    elif name == "nautilus_claim_bounty":
        return platform_api("POST", f"/api/agent-market/tasks/{args['task_id']}/claim")

    elif name == "nautilus_submit_result":
        return platform_api("POST", f"/api/agent-market/tasks/{args['task_id']}/submit", {"code": "mcp_agent", "output": args["report"]})

    elif name == "nautilus_platform_health":
        stats = platform_api("GET", "/api/hub/stats").get("data", {})
        health = platform_api("GET", "/health")
        return {"agents": stats.get("total_agents"), "active": stats.get("active_agents"), "tasks_today": stats.get("tasks_completed_today"), "nau_supply": stats.get("nau_total_supply"), "db": health.get("checks", {}).get("database", {}).get("status")}

    elif name == "nautilus_register_agent":
        return platform_api("POST", "/api/agents/register", {"name": args["name"], "email": args["email"], "specialties": args.get("specialties", ["general"])})

    elif name == "nautilus_agent_status":
        aid = args.get("agent_id", "")
        return platform_api("GET", f"/api/agents/{aid}")

    elif name == "nautilus_a2a_send":
        # A2A auth is X-Agent-Name + X-Agent-Token (paired), NOT X-Agent-Key.
        a2a_name = (args.get("agent_name") or os.getenv("NAUTILUS_A2A_NAME", "")
                   or "nautilus-engine-v2").strip()  # engine service default identity
        token = args.get("agent_token") or AGENT_KEY
        if not a2a_name or not token:
            return {"error": "sender identity required: pass agent_name/agent_token, or set NAUTILUS_A2A_NAME/NAUTILUS_AGENT_KEY on the server"}
        return platform_api(
            "POST", "/api/a2a/send",
            {"from_agent": a2a_name, "to": args.get("to"), "message": args.get("message")},
            extra_headers={"X-Agent-Name": a2a_name, "X-Agent-Token": token},
        )

    elif name == "nautilus_a2a_inbox":
        a2a_name = (args.get("agent_name") or os.getenv("NAUTILUS_A2A_NAME", "")
                   or "nautilus-engine-v2").strip()  # engine service default identity
        token = args.get("agent_token") or AGENT_KEY
        if not a2a_name or not token:
            return {"error": "agent identity required: pass agent_name/agent_token, or set NAUTILUS_A2A_NAME/NAUTILUS_AGENT_KEY on the server"}
        limit = args.get("limit", 10)
        return platform_api(
            "GET", f"/api/a2a/inbox/{a2a_name}?limit={limit}",
            extra_headers={"X-Agent-Name": a2a_name, "X-Agent-Token": token},
        )

    return {"error": f"Unknown tool: {name}"}


# ============================================================
# MCP HTTP Server (JSON-RPC over HTTP)
# ============================================================

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        if path == "/mcp":
            # JSON-RPC style
            method = body.get("method", "")
            params = body.get("params", {})
            req_id = body.get("id", 1)

            if method == "tools/list":
                result = {"tools": MCP_TOOLS}
            elif method == "tools/call":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                tool_result = execute_tool(tool_name, tool_args)
                result = {"content": [{"type": "text", "text": json.dumps(tool_result, ensure_ascii=False, indent=2)}]}
            elif method == "initialize":
                result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "nautilus-platform", "version": "1.0.0"}}
            else:
                result = {"error": f"Unknown method: {method}"}

            response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            self._send_json(response)

        elif path == "/mcp/tools/call":
            # Simplified REST-style
            tool_name = body.get("name", "")
            tool_args = body.get("arguments", body.get("args", {}))
            result = execute_tool(tool_name, tool_args)
            self._send_json(result)
        else:
            self.send_error(404)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/mcp/tools":
            self._send_json({"tools": MCP_TOOLS, "count": len(MCP_TOOLS)})
        elif path == "/mcp/health":
            self._send_json({"status": "ok", "protocol": "MCP", "tools": len(MCP_TOOLS)})
        elif path == "/":
            self._send_json({"name": "Nautilus Platform MCP Server", "version": "1.0.0", "tools": len(MCP_TOOLS), "endpoints": {"tools_list": "/mcp/tools", "tools_call": "POST /mcp/tools/call", "jsonrpc": "POST /mcp", "health": "/mcp/health"}})
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def log_message(self, fmt, *args):
        print(f"[MCP] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    print(f"Nautilus MCP Server starting on port {PORT}...")
    print(f"Platform API: {PLATFORM_API}")
    print(f"Tools: {len(MCP_TOOLS)}")
    print(f"Endpoints:")
    print(f"  GET  /mcp/tools      — List available tools")
    print(f"  POST /mcp/tools/call — Execute a tool")
    print(f"  POST /mcp            — JSON-RPC (standard MCP)")
    print(f"  GET  /mcp/health     — Health check")
    server = HTTPServer(("0.0.0.0", PORT), MCPHandler)
    print(f"Ready: http://0.0.0.0:{PORT}")
    server.serve_forever()

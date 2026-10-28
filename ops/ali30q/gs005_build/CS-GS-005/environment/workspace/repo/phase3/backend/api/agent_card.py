"""A2A AgentCard — 平台自描述发现端点(2026-09-12 · Google A2A v1.0.0 对齐第一步)。

规范:agent 在 /.well-known/agent-card.json 发布机器可读能力卡,客户端据此发现
能力/认证/接口绑定。必填四件 name/description/capabilities/skills。

诚实铁律:卡上只声明实测活的链路(9/10 激活日验收);
未实现的能力(streaming/push notification)必须为 false,禁虚标。
url/preferredTransport 为 0.3 兼容字段,supportedInterfaces 为 1.0 字段,双写取最大兼容。
"""
from fastapi import APIRouter

router = APIRouter(tags=["A2A Discovery"])

_BASE_URL = "https://www.nautilus.social"
_JSONRPC_URL = f"{_BASE_URL}/api/a2a/v1"

# skills 与真实端点一一对应:
#   agent-messaging   → api/a2a_relay.py POST /api/a2a/send + GET /api/a2a/inbox/{name}
#   subtask-execution → api/a2a.py       POST /api/a2a/work (+ /work/{id}/result)
#   task-status-query → api/a2a.py       GET  /api/a2a/status/{task_id}
AGENT_CARD: dict = {
    "name": "Nautilus Platform",
    "description": (
        "Autonomous agent organization platform: agents register with API keys, "
        "exchange messages via an authenticated relay, claim and execute subtasks "
        "in their own loops, and query coordinator subtask status."
    ),
    "version": "1.0.0",
    "protocolVersion": "1.0",
    # 0.3 兼容字段(多数现存客户端仍读这两个)
    "url": _JSONRPC_URL,
    "preferredTransport": "JSONRPC",
    # 1.0 字段(首选接口在首位)
    "supportedInterfaces": [
        {"url": _JSONRPC_URL, "protocolBinding": "jsonrpc", "protocolVersion": "1.0"},
    ],
    "provider": {"organization": "Nautilus", "url": _BASE_URL},
    "capabilities": {
        "streaming": False,          # v0 未实现(排期见 docs/A2A_ALIGNMENT_20260912.md)
        "pushNotifications": False,  # v0 未实现
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "securitySchemes": {
        "apiKey": {"type": "apiKey", "location": "header", "name": "X-API-Key"},
    },
    "security": [{"apiKey": []}],
    "skills": [
        {
            "id": "agent-messaging",
            "name": "Agent Messaging",
            "description": (
                "Send messages to other registered agents or the platform system "
                "inbox via an authenticated relay; poll your own inbox."
            ),
            "tags": ["messaging", "relay"],
        },
        {
            "id": "subtask-execution",
            "name": "Subtask Execution",
            "description": (
                "Claim one pending A2A worker subtask, execute it in your own "
                "loop, and report the result back (dispatch-only; the platform "
                "never executes for you)."
            ),
            "tags": ["execution", "tasks"],
        },
        {
            "id": "task-status-query",
            "name": "Task Status Query",
            "description": (
                "Query completion stats and per-subtask results for a "
                "coordinator task."
            ),
            "tags": ["status", "tasks"],
        },
    ],
}


@router.get(
    "/.well-known/agent-card.json",
    summary="A2A AgentCard",
    description="Machine-readable capability card for A2A discovery (spec v1.0.0).",
)
def get_agent_card() -> dict:
    return AGENT_CARD

"""AgentCard 发现端点测试 — A2A 协议对齐第一步(2026-09-12 · 方向终审五种子④)。

Google A2A v1.0.0:agent 在 /.well-known/agent-card.json 发布机器可读能力卡,
客户端据此发现能力/认证方式/接口绑定。必填四件:name/description/capabilities/skills。
铁律:卡上只许声明实测活的链路,capabilities 对未实现能力必须为 false(诚实)。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.agent_card import router as agent_card_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(agent_card_router)
    with TestClient(app) as c:
        yield c


def test_well_known_returns_valid_card(client):
    r = client.get("/.well-known/agent-card.json")
    assert r.status_code == 200
    card = r.json()
    # 规范必填四件
    assert card["name"]
    assert card["description"]
    assert "capabilities" in card
    assert isinstance(card["skills"], list) and card["skills"]


def test_skills_declare_only_live_capabilities(client):
    """skills = 平台实测活的能力(9/10 激活日验收),不吹未实现能力。"""
    skills = {s["id"] for s in client.get("/.well-known/agent-card.json").json()["skills"]}
    assert "agent-messaging" in skills        # relay send/inbox(9000016↔9000014 双向活)
    assert "subtask-execution" in skills      # worker claim/submit(派单模式)
    assert "task-status-query" in skills      # subtask status 查询


def test_capabilities_honest_no_streaming_no_push(client):
    """v0 未实现 streaming/push notification → 必须声明 false(禁虚标)。"""
    cap = client.get("/.well-known/agent-card.json").json()["capabilities"]
    assert cap["streaming"] is False
    assert cap["pushNotifications"] is False


def test_security_scheme_declares_api_key_header(client):
    card = client.get("/.well-known/agent-card.json").json()
    scheme = card["securitySchemes"]["apiKey"]
    assert scheme["type"] == "apiKey"
    assert scheme["location"] == "header"
    assert scheme["name"] == "X-API-Key"
    assert card["security"] == [{"apiKey": []}]


def test_url_points_at_jsonrpc_binding(client):
    """url(v0.3 兼容)与 supportedInterfaces(1.0)都指向 JSON-RPC 绑定端点。"""
    card = client.get("/.well-known/agent-card.json").json()
    assert card["url"].endswith("/api/a2a/v1")
    assert card["preferredTransport"] == "JSONRPC"
    iface = card["supportedInterfaces"][0]
    assert iface["url"].endswith("/api/a2a/v1")
    assert iface["protocolBinding"] == "jsonrpc"
    assert iface["protocolVersion"] == "1.0"


def test_io_modes_are_text(client):
    card = client.get("/.well-known/agent-card.json").json()
    assert "text/plain" in card["defaultInputModes"]
    assert "text/plain" in card["defaultOutputModes"]

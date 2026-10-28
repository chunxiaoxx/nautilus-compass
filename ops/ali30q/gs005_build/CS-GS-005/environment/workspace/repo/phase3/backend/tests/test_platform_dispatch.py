"""W-C CONTROL · POST /api/platform/dispatch (统一 dispatch 薄路由).

Thin router that dispatches {target, action, payload} to existing building
blocks — a2a_relay (agent) · POST /api/soul/dispatch (soul) · compass
governance_dispatch MCP (compass). It does NOT reimplement orchestration
(anchor #5) — it only routes + reports routed_to, fail-soft on the real send
(a building block being unreachable yields delivered=false, never a 500).

The testable unit is the ROUTING DECISION (routed_to), which is deterministic
regardless of whether the downstream block is reachable in the test env.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.platform_dispatch import router as dispatch_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(dispatch_router)
    return TestClient(app)


def test_dispatch_routes_agent_to_a2a_relay(client):
    r = client.post("/api/platform/dispatch", json={
        "target": "agent", "action": "send_msg",
        "payload": {"to": "9000003", "text": "hi"}})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["routed_to"] == "a2a_relay"


def test_dispatch_routes_soul_to_soul_dispatch(client):
    r = client.post("/api/platform/dispatch", json={
        "target": "soul", "action": "dispatch_goal", "payload": {}})
    assert r.status_code == 200
    assert r.json()["data"]["routed_to"] == "soul_dispatch"


def test_dispatch_routes_compass_to_governance(client):
    r = client.post("/api/platform/dispatch", json={
        "target": "compass", "action": "governance_dispatch", "payload": {}})
    assert r.status_code == 200
    assert r.json()["data"]["routed_to"] == "compass_governance"


def test_dispatch_rejects_unknown_target(client):
    r = client.post("/api/platform/dispatch", json={"target": "bogus", "action": "x"})
    assert r.status_code == 400


def test_dispatch_requires_target_and_action(client):
    r = client.post("/api/platform/dispatch", json={"target": "agent"})
    assert r.status_code == 400


def test_dispatch_is_failsoft_on_unreachable_block(client):
    """A reachable routing decision + an unreachable downstream block →
    routed_to set, delivered=false, still 200 (never 500)."""
    r = client.post("/api/platform/dispatch", json={
        "target": "agent", "action": "send_msg", "payload": {"to": "x", "text": "y"}})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["routed_to"] == "a2a_relay"
    assert "delivered" in d  # bool · false when block unreachable in test env

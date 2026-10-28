"""W-D 瘦 CLI · nautilus <view|dispatch|status> 调平台 API.

Stdlib-only (urllib · no heavy deps · 不搬 nautilus-v5 24 依赖). The HTTP layer is
injected so the CLI's argument parsing + request construction + output shaping are
unit-tested WITHOUT a live backend.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import nautilus  # noqa: E402 · the CLI module under test


def _stub_http(captured):
    def _get(url):
        captured.append(("GET", url, None))
        return {"success": True, "data": {"verdicts": {"summary": {"total": 7, "passed": 6}},
                                          "agents": {"total": 338, "active": 32},
                                          "events": {"summary": {"total": 135}}}}

    def _post(url, body):
        captured.append(("POST", url, body))
        return {"success": True, "data": {"routed_to": "a2a_relay", "delivered": False}}

    return _get, _post


def test_view_hits_control_plane_get():
    cap: list = []
    g, p = _stub_http(cap)
    out = nautilus.run(["view"], http_get=g, http_post=p, base="http://x:8000")
    assert cap[0][0] == "GET"
    assert cap[0][1] == "http://x:8000/api/platform/control-plane"
    assert "7" in out and "32" in out  # renders verdict + agent counts


def test_status_hits_rsi_fde_get():
    cap: list = []
    g, p = _stub_http(cap)
    nautilus.run(["status"], http_get=g, http_post=p, base="http://x:8000")
    assert cap[0][0] == "GET"
    assert "/api/platform/rsi-fde" in cap[0][1]


def test_dispatch_posts_target_action_payload():
    cap: list = []
    g, p = _stub_http(cap)
    out = nautilus.run(
        ["dispatch", "--target", "agent", "--action", "send_msg", "--payload", '{"to":"9000003"}'],
        http_get=g, http_post=p, base="http://x:8000")
    assert cap[0][0] == "POST"
    assert cap[0][1] == "http://x:8000/api/platform/dispatch"
    body = cap[0][2]
    assert body["target"] == "agent" and body["action"] == "send_msg"
    assert body["payload"] == {"to": "9000003"}
    assert "a2a_relay" in out


def test_dispatch_requires_target_and_action():
    cap: list = []
    g, p = _stub_http(cap)
    out = nautilus.run(["dispatch", "--target", "agent"], http_get=g, http_post=p, base="http://x:8000")
    assert "error" in out.lower() or "required" in out.lower()
    assert not cap  # no HTTP call made


def test_unknown_command_errors():
    cap: list = []
    g, p = _stub_http(cap)
    out = nautilus.run(["bogus"], http_get=g, http_post=p, base="http://x:8000")
    assert "usage" in out.lower() or "unknown" in out.lower()
    assert not cap


def test_base_defaults_from_env(monkeypatch):
    monkeypatch.setenv("NAUTILUS_API", "http://envhost:9000")
    cap: list = []
    g, p = _stub_http(cap)
    nautilus.run(["view"], http_get=g, http_post=p)  # no base → from env
    assert cap[0][1].startswith("http://envhost:9000")

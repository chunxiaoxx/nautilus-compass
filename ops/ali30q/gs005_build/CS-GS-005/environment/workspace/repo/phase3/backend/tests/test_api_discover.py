"""Tests for /api/discover · Soul service catalog endpoint.

Inc 3 Slice B Task B1. Surfaces 3 soul services (generate · audit_generate · dispatch)
to external callers so they can discover capabilities without reading source.

Pure unit · no DB · no auth · no monkeypatch needed.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.discover as discover_api


def _make_client():
    app = FastAPI()
    app.include_router(discover_api.router, prefix="/api/discover")
    return TestClient(app)


def test_discover_returns_envelope_with_three_services():
    client = _make_client()
    resp = client.get("/api/discover/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "data" in body
    assert "services" in body["data"]
    services = body["data"]["services"]
    assert isinstance(services, list)
    assert len(services) == 3
    names = sorted(s["name"] for s in services)
    assert names == ["audit_generate", "dispatch", "generate"]


def test_discover_each_service_has_required_fields():
    client = _make_client()
    body = client.get("/api/discover/").json()
    services = body["data"]["services"]
    required_fields = {"name", "method", "path", "auth", "description"}
    for svc in services:
        assert required_fields.issubset(svc.keys()), f"missing fields on {svc.get('name')}"


def test_discover_paths_under_api_soul():
    client = _make_client()
    body = client.get("/api/discover/").json()
    services = body["data"]["services"]
    for svc in services:
        assert svc["path"].startswith("/api/soul/"), f"unexpected path {svc['path']}"

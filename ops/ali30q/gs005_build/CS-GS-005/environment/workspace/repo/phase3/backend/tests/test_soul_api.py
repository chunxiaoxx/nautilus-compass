"""Tests for Soul API · /api/soul/generate (sync dry-run endpoint).

Uses a minimal FastAPI app with just the soul router so we don't load the whole
backend. Auth + generate are monkeypatched.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.soul as soul_api
from utils.database import get_db


def _fake_db():
    yield None


def _make_client(monkeypatch, gen_result):
    app = FastAPI()
    app.include_router(soul_api.router, prefix="/api/soul")
    app.dependency_overrides[get_db] = _fake_db
    monkeypatch.setattr(soul_api, "_require_agent", lambda key, db: 999)
    monkeypatch.setattr("services.soul_service.generate", lambda *a, **k: gen_result)
    return TestClient(app)


def test_generate_returns_result(monkeypatch):
    client = _make_client(monkeypatch, {
        "success": True, "cycle_id": "api-999",
        "files_planned": [{"path": "x.py", "size": 10}],
        "check_result": {"passed": True, "checks": []},
    })
    r = client.post("/api/soul/generate", json={"task_spec": "x" * 30},
                    headers={"X-Agent-Key": "k"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["cycle_id"] == "api-999"


def test_generate_rejects_short_spec(monkeypatch):
    client = _make_client(monkeypatch, {})
    r = client.post("/api/soul/generate", json={"task_spec": "short"},
                    headers={"X-Agent-Key": "k"})
    assert r.status_code == 422  # pydantic min_length=20


def test_generate_requires_auth_header(monkeypatch):
    client = _make_client(monkeypatch, {})
    r = client.post("/api/soul/generate", json={"task_spec": "x" * 30})
    assert r.status_code == 422  # missing required X-Agent-Key header

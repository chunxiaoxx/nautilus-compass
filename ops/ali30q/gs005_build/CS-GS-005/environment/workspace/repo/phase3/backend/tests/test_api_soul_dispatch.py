"""Tests for POST /api/soul/dispatch · Inc 3 Slice B Task B2.

Async enqueue endpoint that writes an agent_dispatch_log row (P2 source).
The daemon (per Slice A wiring) picks the row up via goal_stack.next_goal().

Pure unit · monkeypatch the DB insert + auth · no real DB needed.
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


def _make_client(monkeypatch, captured):
    app = FastAPI()
    app.include_router(soul_api.router, prefix="/api/soul")
    app.dependency_overrides[get_db] = _fake_db
    monkeypatch.setattr(soul_api, "_require_agent", lambda key, db: 9000002)

    def fake_insert(*, db, agent_id, task_spec, task_spec_hash, task_type):
        captured["agent_id"] = agent_id
        captured["task_spec"] = task_spec
        captured["task_spec_hash"] = task_spec_hash
        captured["task_type"] = task_type
        return 42  # fake row id

    monkeypatch.setattr(soul_api, "_insert_agent_dispatch_log", fake_insert)
    return TestClient(app)


def test_dispatch_valid_returns_cycle_id_and_queued(monkeypatch):
    captured = {}
    client = _make_client(monkeypatch, captured)
    body = {
        "task_spec": "Add docstring to phase3/soul/goal_stack.py module · MINIMAL CHANGE",
        "task_type": "code",
    }
    resp = client.post("/api/soul/dispatch", json=body, headers={"X-Agent-Key": "k"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["queued"] is True
    assert data["data"]["cycle_id"] == "dispatch-42"
    assert data["data"]["task_type"] == "code"
    # captured DB insert args
    assert captured["agent_id"] == 9000002
    assert captured["task_spec"] == body["task_spec"]  # Slice B followup · full text persisted
    assert len(captured["task_spec_hash"]) == 64
    assert captured["task_type"] == "code"


def test_dispatch_invalid_type_returns_422(monkeypatch):
    captured = {}
    client = _make_client(monkeypatch, captured)
    body = {"task_spec": "valid spec longer than min length to clear validator", "task_type": "bogus"}
    resp = client.post("/api/soul/dispatch", json=body, headers={"X-Agent-Key": "k"})
    # pydantic Literal validation rejects with 422 before handler runs
    assert resp.status_code == 422
    assert "task_type" in resp.text
    # nothing inserted
    assert captured == {}


def test_dispatch_each_valid_type(monkeypatch):
    """code · config · schema-migration must all accept."""
    for tt in ("code", "config", "schema-migration"):
        captured = {}
        client = _make_client(monkeypatch, captured)
        body = {"task_spec": "spec long enough to satisfy min length validator XXXXXXXX", "task_type": tt}
        resp = client.post("/api/soul/dispatch", json=body, headers={"X-Agent-Key": "k"})
        assert resp.status_code == 200, f"{tt} failed: {resp.text}"
        assert captured["task_type"] == tt

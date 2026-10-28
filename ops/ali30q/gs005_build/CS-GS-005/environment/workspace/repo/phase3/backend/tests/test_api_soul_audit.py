"""Task 1.2 · POST /api/soul/audit-generate returns a verify-valid signed cert.

Minimal app (just the soul router) + mocked engine/audit so no LLM/DB needed.
"""
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import api.soul as soul
from utils.database import get_db


def _fake_db():
    yield object()


def _app():
    app = FastAPI()
    app.include_router(soul.router, prefix="/api/soul")
    app.dependency_overrides[get_db] = _fake_db
    return app


def test_audit_generate_returns_valid_cert(monkeypatch):
    monkeypatch.setattr(soul, "_require_agent", lambda key, db: 4242)
    monkeypatch.setattr(
        "services.soul_service.generate",
        lambda task, base_dir, cycle_id=None, capture_content=False: {
            "success": True,
            "cycle_id": cycle_id,
            "files_planned": [
                {"path": "scratch/x.py", "size": 17, "lang": "python", "content": "def x(): return 1"}
            ],
            "check_result": {"passed": True},
        },
    )
    monkeypatch.setattr(
        "services.soul_self_audit.run_self_audit",
        lambda db, task_spec, output, bounty_id, **k: {
            "success": True,
            "bounty_id": bounty_id,
            "fidelity_score": 0.81,
            "cert": {"@type": "AuditCertificate", "audit_id": bounty_id, "signature": "sig"},
            "cert_valid": True,
        },
    )
    client = TestClient(_app())
    r = client.post(
        "/api/soul/audit-generate",
        headers={"X-Agent-Key": "k"},
        json={"task_spec": "add a function x that returns 1 to scratch/x.py"},
    )
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["cert_valid"] is True
    assert d["fidelity_score"] == 0.81
    assert d["bounty_id"].startswith("soul-audit-api-")
    assert d["cert"]["audit_id"].startswith("soul-audit-api-")


def test_audit_generate_requires_auth(monkeypatch):
    def deny(key, db):
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    monkeypatch.setattr(soul, "_require_agent", deny)
    client = TestClient(_app())
    r = client.post(
        "/api/soul/audit-generate",
        headers={"X-Agent-Key": "bad"},
        json={"task_spec": "add a function x that returns 1 to scratch/x.py"},
    )
    assert r.status_code == 401


def test_audit_generate_fail_closed_on_empty_content(monkeypatch):
    """If generation 'succeeds' but no real content was captured, do NOT certify."""
    monkeypatch.setattr(soul, "_require_agent", lambda key, db: 9)
    monkeypatch.setattr(
        "services.soul_service.generate",
        lambda task, base_dir, cycle_id=None, capture_content=False: {
            "success": True,
            "cycle_id": cycle_id,
            "files_planned": [{"path": "scratch/x.py", "size": 0, "lang": "python", "content": "   "}],
            "check_result": {"passed": True},
        },
    )
    client = TestClient(_app())
    r = client.post(
        "/api/soul/audit-generate",
        headers={"X-Agent-Key": "k"},
        json={"task_spec": "add a function x that returns 1 to scratch/x.py"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "no generated content captured to certify"


def test_audit_generate_handles_generate_exception(monkeypatch):
    """An LLM/engine raise degrades cleanly to a standard error envelope, not a 500."""
    monkeypatch.setattr(soul, "_require_agent", lambda key, db: 9)

    def boom(task, base_dir, cycle_id=None, capture_content=False):
        raise RuntimeError("provider down")

    monkeypatch.setattr("services.soul_service.generate", boom)
    client = TestClient(_app())
    r = client.post(
        "/api/soul/audit-generate",
        headers={"X-Agent-Key": "k"},
        json={"task_spec": "add a function x that returns 1 to scratch/x.py"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert "generation error" in body["error"]


def test_audit_generate_generation_fail_returns_no_cert(monkeypatch):
    monkeypatch.setattr(soul, "_require_agent", lambda key, db: 7)
    monkeypatch.setattr(
        "services.soul_service.generate",
        lambda task, base_dir, cycle_id=None, capture_content=False: {
            "success": False,
            "cycle_id": cycle_id,
            "files_planned": [],
            "check_result": {"passed": False, "errors": "ruff failed"},
        },
    )
    client = TestClient(_app())
    r = client.post(
        "/api/soul/audit-generate",
        headers={"X-Agent-Key": "k"},
        json={"task_spec": "produce something that fails checks here"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "generation checks failed"

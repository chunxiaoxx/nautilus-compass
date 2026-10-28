"""POST/GET /api/soul/proposals · Option B queue-writer tests (mock-based).

2026-09-10 activation day · closes the agent→soul loop (SOUL_PROPOSAL_CONTRACT
Option B): agents submit coding proposals into `platform_proposals`
(status='pending'), soul_consumer ships them and writes the verdict back.
Verifies: auth gate, INSERT params, dedup, id format guard, client-chosen id,
and the status-poll readback endpoint. DB is mocked; no real Postgres.
"""
import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BODY = {
    "title": "add helper to utils",
    "proposed_change": "add a small pure helper function to utils and a unit test for it",
    "target_agent": "soul",
    "rationale": "activation-day end-to-end verification proposal",
    "change_type": "code",
}


def _submit(db, **overrides):
    from api import soul as soul_api
    payload = {**BODY, **overrides}
    body = soul_api.SubmitProposalRequest(**payload)
    return asyncio.run(
        soul_api.soul_submit_proposal(body, x_agent_key="k", db=db))


def test_submit_requires_valid_agent_key():
    from api import soul as soul_api
    with patch.object(soul_api, "_require_agent",
                      side_effect=HTTPException(status_code=401, detail="Invalid or expired API key")):
        with pytest.raises(HTTPException) as ei:
            _submit(MagicMock())
    assert ei.value.status_code == 401


def test_submit_inserts_pending_row_with_generated_id():
    from api import soul as soul_api
    db = MagicMock()
    db.execute.return_value.first.return_value = None  # no duplicate
    with patch.object(soul_api, "_require_agent", return_value=42), \
         patch.object(soul_api, "_agent_display_name", return_value="nautilus-prime-001"):
        resp = _submit(db)
    assert resp["success"] is True
    pid = resp["data"]["proposal_id"]
    assert pid.startswith("pr-soul-")
    assert resp["data"]["status"] == "pending"
    assert "poll" in resp["data"]
    call = db.execute.call_args_list[-1]
    sql = str(call.args[0]).lower()
    params = call.args[1]
    assert "insert into platform_proposals" in sql
    assert params["pid"] == pid
    assert params["pa"] == "nautilus-prime-001"
    assert params["ta"] == "soul"
    assert params["ct"] == "code"
    assert params["st"] == "pending"
    assert params["pc"].startswith("add a small pure helper")
    db.commit.assert_called_once()


def test_submit_accepts_client_proposal_id():
    from api import soul as soul_api
    db = MagicMock()
    db.execute.return_value.first.return_value = None
    with patch.object(soul_api, "_require_agent", return_value=42), \
         patch.object(soul_api, "_agent_display_name", return_value="a"):
        resp = _submit(db, proposal_id="pr-custom-abc123")
    assert resp["data"]["proposal_id"] == "pr-custom-abc123"


def test_submit_rejects_duplicate_proposal_id():
    from api import soul as soul_api
    db = MagicMock()
    db.execute.return_value.first.return_value = (1,)  # exists
    with patch.object(soul_api, "_require_agent", return_value=42), \
         patch.object(soul_api, "_agent_display_name", return_value="a"):
        with pytest.raises(HTTPException) as ei:
            _submit(db, proposal_id="pr-custom-abc123")
    assert ei.value.status_code == 409


def test_submit_rejects_bad_proposal_id_format():
    from api import soul as soul_api
    db = MagicMock()
    with patch.object(soul_api, "_require_agent", return_value=42), \
         patch.object(soul_api, "_agent_display_name", return_value="a"):
        with pytest.raises(HTTPException) as ei:
            _submit(db, proposal_id="bad id with spaces!")
    assert ei.value.status_code == 422


def test_proposal_status_returns_row():
    from api import soul as soul_api
    db = MagicMock()
    db.execute.return_value.first.return_value = (
        "pr-x", "reviewed", "Soul shipped DRAFT PR: https://github.com/x/y/pull/7", "soul", None)
    with patch.object(soul_api, "_require_agent", return_value=42):
        resp = asyncio.run(soul_api.soul_proposal_status("pr-x", x_agent_key="k", db=db))
    assert resp["success"] is True
    assert resp["data"]["status"] == "reviewed"
    assert "pull/7" in resp["data"]["resolution_note"]


def test_proposal_status_404_on_unknown_id():
    from api import soul as soul_api
    db = MagicMock()
    db.execute.return_value.first.return_value = None
    with patch.object(soul_api, "_require_agent", return_value=42):
        with pytest.raises(HTTPException) as ei:
            asyncio.run(soul_api.soul_proposal_status("pr-missing", x_agent_key="k", db=db))
    assert ei.value.status_code == 404

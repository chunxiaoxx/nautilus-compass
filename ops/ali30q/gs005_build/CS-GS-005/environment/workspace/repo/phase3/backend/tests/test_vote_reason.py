"""Inc 1.5 Task 7 · P1 vote endpoint optional reason field tests (mock-based).

Verifies:
- Vote with reason field persists reason in INSERT params
- Vote without reason (backward compat) succeeds with reason=None
- Vote with non-string reason returns error (validation)
"""
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_vote_with_reason_persists_in_insert():
    """POST /vote with reason field stores reason in INSERT params."""
    from api import platform_proposals
    db = MagicMock()
    agent_row = MagicMock(id=1, reputation_score=80)
    prop_row = MagicMock(id='p1', vote_score=0.0, vote_count=0, status='pending',
                         proposed_change={"type": "code", "task": "t"})
    with patch.object(platform_proposals, '_q') as mock_q:
        mock_q.return_value.fetchone.side_effect = [agent_row, prop_row]
        body = {"agent_id": 1, "vote": 1,
                "reason": "L2 self-improve scope · target_module reuse 合理"}
        response = platform_proposals.vote_proposal('p1', body, db)
    # Find the INSERT call into platform_proposal_votes
    insert_calls = [c for c in mock_q.call_args_list
                    if c.args[1] and 'INSERT INTO platform_proposal_votes' in c.args[1]]
    assert len(insert_calls) == 1
    insert_params = insert_calls[0].args[2]
    assert insert_params["reason"] == "L2 self-improve scope · target_module reuse 合理"
    assert insert_params["vote"] == 1
    assert insert_params["agent_id"] == 1
    assert response.get("success") is True


def test_vote_without_reason_succeeds_with_null():
    """POST /vote without reason (backward compat) succeeds · reason=None in INSERT."""
    from api import platform_proposals
    db = MagicMock()
    agent_row = MagicMock(id=1, reputation_score=80)
    prop_row = MagicMock(id='p1', vote_score=0.0, vote_count=0, status='pending',
                         proposed_change={"type": "code", "task": "t"})
    with patch.object(platform_proposals, '_q') as mock_q:
        mock_q.return_value.fetchone.side_effect = [agent_row, prop_row]
        body = {"agent_id": 1, "vote": 1}  # no reason field
        response = platform_proposals.vote_proposal('p1', body, db)
    insert_calls = [c for c in mock_q.call_args_list
                    if c.args[1] and 'INSERT INTO platform_proposal_votes' in c.args[1]]
    assert len(insert_calls) == 1
    insert_params = insert_calls[0].args[2]
    assert insert_params["reason"] is None  # NULL stored
    assert response.get("success") is True


def test_vote_non_string_reason_returns_error():
    """POST /vote with non-string reason (e.g. int) returns validation error."""
    from api import platform_proposals
    db = MagicMock()
    body = {"agent_id": 1, "vote": 1, "reason": 12345}  # int not str
    response = platform_proposals.vote_proposal('p1', body, db)
    assert response.get("success") is False
    assert "reason" in (response.get("error") or "").lower()
    assert "string" in (response.get("error") or "").lower()


def test_vote_insert_non_unique_error_surfaces_not_masked():
    """Code-review fix #2 · INSERT raising non-IntegrityError must NOT be masked as 'Already voted'.

    Failure mode pre-fix: cloud forgets to apply reason-column migration · INSERT
    raises ProgrammingError(column 'reason' does not exist) · was caught by
    `except Exception` and returned 'Already voted on this proposal' · misleading.
    Post-fix: only IntegrityError → 'Already voted' · other exceptions surface as
    'Vote INSERT failed: <detail>'.
    """
    from api import platform_proposals
    db = MagicMock()
    agent_row = MagicMock(id=1, reputation_score=80)
    prop_row = MagicMock(id='p1', vote_score=0.0, vote_count=0, status='pending',
                         proposed_change={"type": "code", "task": "t"})

    # Mock _q · first 2 calls return rows (agent + proposal SELECTs) · 3rd call (INSERT) raises
    call_count = [0]

    def _q_side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            r = MagicMock(); r.fetchone.return_value = agent_row; return r
        if call_count[0] == 2:
            r = MagicMock(); r.fetchone.return_value = prop_row; return r
        if call_count[0] == 3:
            # Simulate ProgrammingError-like (cloud missing reason column)
            raise RuntimeError("column 'reason' does not exist")
        return MagicMock()

    with patch.object(platform_proposals, '_q', side_effect=_q_side_effect):
        body = {"agent_id": 1, "vote": 1, "reason": "test"}
        response = platform_proposals.vote_proposal('p1', body, db)
    assert response.get("success") is False
    err = (response.get("error") or "").lower()
    # Must NOT be masked as the unique-violation message
    assert "already voted" not in err
    # Must surface the actual error for operator diagnosis
    assert "vote insert failed" in err
    assert "reason" in err  # the underlying error mentions reason column

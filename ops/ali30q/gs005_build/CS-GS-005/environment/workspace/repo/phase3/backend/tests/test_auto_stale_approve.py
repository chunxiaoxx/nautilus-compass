"""Unit tests for auto_approve_stale_proposals · Inc 1.5 Task 2.

Mock-based tests (no real DB) verify the rewritten fn:
- SQL contains P4 anti-RH gate (vote_count >= 1 AND vote_score >= 0)
- SQL contains type='code' filter
- UPDATE writes status='accepted' + resolved_by='auto_stale' + resolution_note
- on_consensus_reached called per stale row
- callback failure does not abort batch or fn (logged + continued)
- returns count of approved rows
"""
import sys
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Add backend dir to path so 'services' is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _make_db_mock(stale_rows):
    """Build a MagicMock db whose .execute().fetchall() returns stale_rows on SELECT
    and whose subsequent .execute() calls (UPDATE) are tracked."""
    db = MagicMock()
    execute_results = MagicMock()
    execute_results.fetchall.return_value = stale_rows
    # First call (SELECT) returns fetchall=stale_rows · subsequent calls (UPDATE) return MagicMock
    db.execute.return_value = execute_results
    return db


def _row(id, proposed_change_dict):
    """Build a SQLAlchemy-row-like SimpleNamespace."""
    return SimpleNamespace(id=id, status='pending', proposed_change=proposed_change_dict)


def test_stale_code_proposal_with_one_yes_vote_auto_approves():
    """24h+ stale code proposal · returns 1 · calls on_consensus_reached · UPDATE writes accepted."""
    from services.proposal_consensus import auto_approve_stale_proposals
    db = _make_db_mock([_row('proposal-001', {'type': 'code', 'task': 'test task'})])
    with patch('services.proposal_consensus.on_consensus_reached') as mock_route:
        approved = auto_approve_stale_proposals(db, stale_hours=24)
    assert approved == 1
    mock_route.assert_called_once()
    # Verify UPDATE was issued with the right params
    assert db.execute.call_count >= 2  # SELECT + UPDATE
    update_call = db.execute.call_args_list[1]
    update_sql = str(update_call[0][0])
    assert "status='accepted'" in update_sql
    assert "resolved_by='auto_stale'" in update_sql
    update_params = update_call[0][1]
    assert update_params['id'] == 'proposal-001'
    assert 'auto-approved' in update_params['note']


def test_stale_approve_returns_zero_when_no_stale_rows():
    """No stale rows match SELECT · returns 0 · no UPDATE · no callback."""
    from services.proposal_consensus import auto_approve_stale_proposals
    db = _make_db_mock([])
    with patch('services.proposal_consensus.on_consensus_reached') as mock_route:
        approved = auto_approve_stale_proposals(db, stale_hours=24)
    assert approved == 0
    mock_route.assert_not_called()
    # Only SELECT executed · no UPDATE
    assert db.execute.call_count == 1


def test_stale_approve_sql_includes_type_code_filter():
    """SELECT SQL must filter type='code' (excludes experiment-type from sandbox path)."""
    from services.proposal_consensus import auto_approve_stale_proposals
    db = _make_db_mock([])
    auto_approve_stale_proposals(db, stale_hours=24)
    select_sql = str(db.execute.call_args_list[0][0][0])
    assert "proposed_change->>'type' = 'code'" in select_sql


def test_stale_approve_sql_includes_p4_gate_vote_count_and_score():
    """SELECT SQL must include P4 anti-RH gate: vote_count >= 1 AND vote_score >= 0."""
    from services.proposal_consensus import auto_approve_stale_proposals
    db = _make_db_mock([])
    auto_approve_stale_proposals(db, stale_hours=24)
    select_sql = str(db.execute.call_args_list[0][0][0])
    assert "vote_count >= 1" in select_sql
    assert "vote_score >= 0" in select_sql


def test_stale_approve_returns_count_for_multiple_rows():
    """3 stale rows · returns 3 · 3 UPDATEs · 3 callbacks."""
    from services.proposal_consensus import auto_approve_stale_proposals
    rows = [_row(f'p-{i}', {'type': 'code', 'task': f'task {i}'}) for i in range(3)]
    db = _make_db_mock(rows)
    with patch('services.proposal_consensus.on_consensus_reached') as mock_route:
        approved = auto_approve_stale_proposals(db, stale_hours=24)
    assert approved == 3
    assert mock_route.call_count == 3


def test_callback_failure_does_not_block_update():
    """on_consensus_reached raises · status STILL updated · fn does NOT raise · error logged."""
    from services.proposal_consensus import auto_approve_stale_proposals
    db = _make_db_mock([_row('proposal-fail', {'type': 'code', 'task': 't'})])
    with patch('services.proposal_consensus.on_consensus_reached',
               side_effect=RuntimeError('simulated callback failure')):
        # fn must not raise · callback errors swallowed/logged
        approved = auto_approve_stale_proposals(db, stale_hours=24)
    # Even if callback failed · row should still have been UPDATEd
    assert approved == 1
    assert db.execute.call_count >= 2  # SELECT + UPDATE

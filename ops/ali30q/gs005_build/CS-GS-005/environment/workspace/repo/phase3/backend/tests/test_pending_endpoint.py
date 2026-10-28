"""Inc 1.5 Task 8 · P2 GET /api/platform/proposals/pending tests (mock-based).

Verifies:
- SQL filters status IN ('pending', 'voting')
- exclude_author adds WHERE p.agent_id != :exclude_author
- exclude_voted_by adds NOT EXISTS subquery
- limit clamped to [1, 50]
"""
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_pending_default_filters_status_only():
    """No exclude params · only status filter applied."""
    from api import platform_proposals
    db = MagicMock()
    with patch.object(platform_proposals, '_q') as mock_q:
        mock_q.return_value.fetchall.return_value = []
        response = platform_proposals.list_pending_proposals(
            exclude_voted_by=None, exclude_author=None, limit=10, db=db)
    sql = mock_q.call_args.args[1]
    params = mock_q.call_args.args[2]
    assert "status IN ('pending', 'voting')" in sql
    assert "agent_id !=" not in sql  # no exclude_author
    assert "NOT EXISTS" not in sql  # no exclude_voted_by
    assert params == {"limit": 10}
    assert response.get("success") is True
    assert response["data"]["proposals"] == []


def test_pending_excludes_voted_by():
    """exclude_voted_by=N adds NOT EXISTS subquery with agent_id=N."""
    from api import platform_proposals
    db = MagicMock()
    with patch.object(platform_proposals, '_q') as mock_q:
        mock_q.return_value.fetchall.return_value = []
        platform_proposals.list_pending_proposals(
            exclude_voted_by=9000003, exclude_author=None, limit=10, db=db)
    sql = mock_q.call_args.args[1]
    params = mock_q.call_args.args[2]
    assert "NOT EXISTS" in sql
    assert "v.agent_id = :exclude_voted_by" in sql
    assert params["exclude_voted_by"] == 9000003


def test_pending_excludes_author():
    """exclude_author=N adds WHERE p.agent_id != :exclude_author."""
    from api import platform_proposals
    db = MagicMock()
    with patch.object(platform_proposals, '_q') as mock_q:
        mock_q.return_value.fetchall.return_value = []
        platform_proposals.list_pending_proposals(
            exclude_voted_by=None, exclude_author=9000002, limit=10, db=db)
    sql = mock_q.call_args.args[1]
    params = mock_q.call_args.args[2]
    assert "p.agent_id != :exclude_author" in sql
    assert params["exclude_author"] == 9000002


def test_pending_limit_clamped_to_50():
    """limit > 50 clamped to 50 · limit < 1 clamped to 1."""
    from api import platform_proposals
    db = MagicMock()
    with patch.object(platform_proposals, '_q') as mock_q:
        mock_q.return_value.fetchall.return_value = []
        # Too high
        platform_proposals.list_pending_proposals(
            exclude_voted_by=None, exclude_author=None, limit=500, db=db)
        assert mock_q.call_args.args[2]["limit"] == 50
        # Too low (zero or negative)
        platform_proposals.list_pending_proposals(
            exclude_voted_by=None, exclude_author=None, limit=0, db=db)
        assert mock_q.call_args.args[2]["limit"] == 1
        # Negative
        platform_proposals.list_pending_proposals(
            exclude_voted_by=None, exclude_author=None, limit=-10, db=db)
        assert mock_q.call_args.args[2]["limit"] == 1

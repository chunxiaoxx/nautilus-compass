"""Ghost wiring cleanup test · Inc 1.5 Task 1.
Verifies `auto_vote_proposals` ghost references are fully removed.

The ghost reference imported `services.proposal_consensus.auto_vote_proposals`
which never existed; the ImportError was shielded by R2.B 5/4 default-disable.
Vote functionality is agent-dialog turf per anchor #7 · platform does not ship
vote fn. This test guards against the ghost coming back.
"""
from pathlib import Path


def test_auto_vote_proposals_ghost_removed():
    """The auto_vote_proposals ghost wiring must be fully gone."""
    cron_path = Path(__file__).parent.parent / "services" / "cron_registry.py"
    content = cron_path.read_text(encoding="utf-8")

    # The string should not appear anywhere · this prevents future regressions
    assert "auto_vote_proposals" not in content, (
        "auto_vote_proposals references still present in cron_registry.py · "
        "Task 1 (Inc 1.5) requires full removal per anchor #7 (vote = agent-dialog turf)"
    )

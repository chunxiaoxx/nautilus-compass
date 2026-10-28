"""Inc 2 Slice 1 · verify agents rep_proposing + rep_voting columns."""
import os
import pytest
import psycopg

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="Postgres-only"
)


def _conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


def test_agents_has_rep_proposing_and_voting():
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT column_name, data_type, column_default "
            "FROM information_schema.columns "
            "WHERE table_name = 'agents' "
            "  AND column_name IN ('rep_proposing', 'rep_voting')"
        )
        rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    assert "rep_proposing" in rows, "missing rep_proposing"
    assert "rep_voting" in rows, "missing rep_voting"
    for name, (dtype, default) in rows.items():
        assert dtype == "real", f"{name} expected real, got {dtype}"
        assert "50" in (default or ""), f"{name} default must be 50.0, got {default!r}"

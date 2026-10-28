"""Inc 2 Slice 1 · verify proposal_outcomes table created by migration."""
import os
import pytest
import psycopg

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="Postgres-only · matches test_auto_stale_approve.py precedent",
)


def _conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


def test_proposal_outcomes_table_exists():
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_name = 'proposal_outcomes' "
            "ORDER BY ordinal_position"
        )
        cols = {r[0]: r[1] for r in cur.fetchall()}
    expected = {
        "proposal_id": "character varying",
        "pre_snapshot": "jsonb",
        "post_snapshot": "jsonb",
        "composite_delta": "real",
        "no_revert": "boolean",
        "graded_at": "timestamp with time zone",
        "graded_by": "character varying",
    }
    assert expected.items() <= cols.items(), (
        f"missing columns: {set(expected) - set(cols)}"
    )


def test_proposal_outcomes_primary_key():
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT a.attname "
            "FROM pg_index i JOIN pg_attribute a "
            "  ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indrelid = 'proposal_outcomes'::regclass AND i.indisprimary"
        )
        pk = [r[0] for r in cur.fetchall()]
    assert pk == ["proposal_id"], f"expected proposal_id PK, got {pk}"

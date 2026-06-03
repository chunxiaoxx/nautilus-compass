import re
import sqlite3
from pathlib import Path

SQL_PATH = Path(__file__).resolve().parents[1] / "sql" / "004_poi_credit.sql"


def _create_stmt_for_sqlite(sql_text: str) -> str:
    # take only the CREATE TABLE ... ( ... ); statement
    m = re.search(r"CREATE TABLE[^;]*;", sql_text, re.IGNORECASE | re.DOTALL)
    assert m, "no CREATE TABLE found"
    stmt = m.group(0)
    stmt = stmt.replace("compass.", "")
    stmt = stmt.replace("double precision", "REAL").replace("timestamptz", "TEXT")
    stmt = stmt.replace("IF NOT EXISTS", "")  # keep simple
    return stmt


def test_create_table_parses_and_has_columns():
    sql_text = SQL_PATH.read_text(encoding="utf-8")
    stmt = _create_stmt_for_sqlite(sql_text)
    conn = sqlite3.connect(":memory:")
    conn.execute(stmt)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(poi_credit)")}
    assert {"memory_key", "cumulative_impact", "event_count", "last_impact_at"} <= cols


def test_has_grant_for_phase1():
    sql_text = SQL_PATH.read_text(encoding="utf-8")
    assert "GRANT" in sql_text.upper() and "poi_credit" in sql_text

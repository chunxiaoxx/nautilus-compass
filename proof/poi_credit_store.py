"""Central PoI credit table I/O + atomic snapshot. Replaces frontmatter as the
credit source of truth. Reference: design §4.1/§4.3. NO LLM."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Dict

UPSERT_SQL = (
    "INSERT INTO poi_credit (memory_key, cumulative_impact, event_count, last_impact_at) "
    "VALUES ({p}, {p}, 1, {p}) "
    "ON CONFLICT (memory_key) DO UPDATE SET "
    "cumulative_impact = poi_credit.cumulative_impact + EXCLUDED.cumulative_impact, "
    "event_count = poi_credit.event_count + 1, "
    "last_impact_at = EXCLUDED.last_impact_at"
)


def upsert_credit(conn, memory_key: str, delta: float, now_iso: str, placeholder: str = "%s") -> None:
    """Accumulate delta onto memory_key. placeholder='%s' for psycopg2, '?' for sqlite."""
    sql = UPSERT_SQL.format(p=placeholder)
    cur = conn.cursor()
    cur.execute(sql, (memory_key, float(delta), now_iso))
    conn.commit()


def fetch_all_credits(conn) -> Dict[str, float]:
    cur = conn.cursor()
    cur.execute("SELECT memory_key, cumulative_impact FROM poi_credit")
    return {k: float(v) for k, v in cur.fetchall()}


def write_snapshot_atomic(path, credit: Dict[str, float]) -> None:
    """tmp -> fsync -> os.replace · daemon never reads a half-written file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(credit, f, ensure_ascii=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def load_snapshot(path) -> Dict[str, float]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

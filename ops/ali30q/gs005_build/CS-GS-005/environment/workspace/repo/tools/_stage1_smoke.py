"""Smoke test · real PG (docker nautilus-postgres) · validates Stage 1 emit end-to-end."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "phase3" / "backend"))

os.environ["DATABASE_URL"] = "postgresql://nautilus:nautilus_dev_password@localhost:5432/nautilus_dev"

from engine.outcome_emit import emit_outcome

row = {
    "cycle_id": "smoke_stage1_2026-05-25_v1",
    "spec": "smoke test · validates schema bootstrap + INSERT path",
    "spec_expected_added": 2,
    "spec_expected_removed": 0,
    "ship_status": "success",
    "semantic_pass": True,
    "tests_pass": True,
    "actual_lines_added": 2,
    "actual_lines_removed": 0,
    "drift_ratio": 1.0,
    "composite_score": 1.0,
    "git_sha": "smoke-test-no-sha",
    "cert_id": None,
}

emit_outcome(row)
print("emit_outcome returned cleanly")

# Verify the row landed
import psycopg
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT cycle_id, ship_status, composite_score FROM engine_cycle_outcomes WHERE cycle_id = %s",
                    (row["cycle_id"],))
        result = cur.fetchone()
        print(f"row found: {result}")

        cur.execute("SELECT count(*) FROM engine_cycle_outcomes")
        print(f"total rows: {cur.fetchone()[0]}")

        cur.execute("SELECT day, ship_count, avg_composite FROM v_engine_progress")
        for r in cur.fetchall():
            print(f"view row: {r}")

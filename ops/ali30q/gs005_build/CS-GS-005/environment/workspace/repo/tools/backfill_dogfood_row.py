"""One-shot backfill: remove the 1 dogfood dry-run row that biases v_engine_progress.

Context (handoff 2026-05-25 Gap 2 · closed by 5/26 Path C):
- 5/25 stage1_self_dogfood cycle ran LLM on aggregate_recent task
- cycle 12 P1 semantic-check trigger did NOT fire on this task wording
  (the gap closed by 5/26 Gap 1 ship · semantic guard now fires on
  existing-file > 50 LOC trigger as well)
- LLM truncated 55 LOC + rewrote docstring · status='fail' composite=0
- This row dragged v_engine_progress.avg_composite from 1.000 → 0.875
- emit-skip guard (5/26 Phase 1 of quick wins) prevents future similar rows
- But the historic row persists, biasing the view forever

This script DELETEs that 1 historic row (1-shot · idempotent · safe to re-run · second
run finds nothing and exits clean). Evidence preserved in:
- docs/SESSION_HANDOFF_20260525_TO_FRESH.md (line 74 snapshot)
- docs/plans/2026-05-26-gap1-semantic-guard-design.md (cycle 12 P1 gap evidence)
- git log (cycle 17 D1 ship + Stage 1 design docs)
"""
import os
import sys

import psycopg

DSN = os.environ.get("DATABASE_URL", "postgresql://nautilus:nautilus_dev_password@localhost:5432/nautilus_dev")

SQL_DELETE = """
DELETE FROM engine_cycle_outcomes
WHERE cycle_id LIKE 'stage1_self_dogfood%'
  AND ship_status = 'fail'
  AND composite_score = 0
RETURNING cycle_id, ship_status, composite_score, git_sha;
"""

SQL_VERIFY = """
SELECT day, ship_count, avg_composite, avg_drift, success_ratio
FROM v_engine_progress
ORDER BY day DESC;
"""


def main() -> int:
    try:
        with psycopg.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(SQL_DELETE)
                deleted = cur.fetchall()
            conn.commit()
            if not deleted:
                print("backfill: no rows matched · already clean (or no historic dogfood row)")
            else:
                print(f"backfill: deleted {len(deleted)} row(s):")
                for row in deleted:
                    print(f"  · cycle_id={row[0]} status={row[1]} composite={row[2]} git_sha={row[3]}")

            print()
            print("verify v_engine_progress after backfill:")
            with conn.cursor() as cur:
                cur.execute(SQL_VERIFY)
                for row in cur.fetchall():
                    print(f"  day={row[0]} ship_count={row[1]} avg_composite={row[2]} avg_drift={row[3]} success_ratio={row[4]}")
        return 0
    except psycopg.OperationalError as e:
        print(f"ERROR: cannot connect ({type(e).__name__}): {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: unexpected ({type(e).__name__}): {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())

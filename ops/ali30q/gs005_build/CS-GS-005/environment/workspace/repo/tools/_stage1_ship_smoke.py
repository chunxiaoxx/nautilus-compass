"""Real-PG smoke · ship() with mock LLM · validates auto-emit on real DB."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "phase3" / "backend"))

os.environ["DATABASE_URL"] = "postgresql://nautilus:nautilus_dev_password@localhost:5432/nautilus_dev"

from engine.nautilus_engine import NautilusEngine
from engine.ship import ship

# Mock LLM returns nothing parseable → triggers deadletter path
fake_llm = MagicMock()
fake_llm.chat = MagicMock(return_value="no fenced code blocks here, just prose")

# Use cwd as base (any dir works for dry-run)
eng = NautilusEngine(llm_client=fake_llm, base_dir=".", dry_run=True)

result = ship(
    eng,
    task="smoke test · validates ship auto-emit on real PG\n\nSpec-Meta:\n  expected_added: 0\n  expected_removed: 0\n",
    base_dir=".",
    apply=False,
    dispatch_audit=False,
    cycle_id="ship_smoke_2026-05-25_dl",
)

print(f"ship returned · status: applied={result.applied} · errors={result.errors[:1]}")

# Verify row landed
import psycopg
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cycle_id, reason FROM engine_cycle_deadletter WHERE cycle_id = %s",
            ("ship_smoke_2026-05-25_dl",),
        )
        dl = cur.fetchone()
        print(f"deadletter row: {dl}")

        cur.execute("SELECT count(*) FROM engine_cycle_outcomes")
        print(f"outcomes total: {cur.fetchone()[0]}")
        cur.execute("SELECT count(*) FROM engine_cycle_deadletter")
        print(f"deadletter total: {cur.fetchone()[0]}")

        cur.execute("SELECT day, ship_count, avg_composite FROM v_engine_progress")
        for r in cur.fetchall():
            print(f"v_engine_progress: {r}")

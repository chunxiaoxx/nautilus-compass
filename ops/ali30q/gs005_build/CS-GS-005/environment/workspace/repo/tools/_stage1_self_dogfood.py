"""Day 6-7 self-dogfood · ship outcomes.py extension via PR #46 engine pipeline.

Validates: cycle 15 self-bootstrap pattern (engine ships its own module
extension) is repeatable on Stage 1 components. Also validates Stage 1
emit hook records this very ship to engine_cycle_outcomes (closed-loop
end-to-end on real cycle).

Spec target: add `aggregate_recent()` helper to outcomes.py that takes a
list of outcome row dicts and returns aggregate stats over last N days.
Small bounded scope · ~10 LOC · low LLM-output drift surface.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "phase3" / "backend"))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://nautilus:nautilus_dev_password@localhost:5432/nautilus_dev",
)

from engine.nautilus_engine import NautilusEngine
from engine.ship import ship


SPEC = """Add a new helper function `aggregate_recent` to phase3/backend/engine/outcomes.py.

CURRENT FILE STATE: outcomes.py has 5 pure functions (parse_spec_meta, compute_composite,
classify, is_deadletter, compute_drift_ratio). All functions are pure · no I/O.
Add the 6th function BELOW compute_drift_ratio · keep ALL existing code identical.

NEW FUNCTION SPEC:
    def aggregate_recent(outcomes: list[dict], days: int = 7) -> dict:
        \"\"\"Aggregate composite + drift + success_ratio over recent N days of outcomes.

        Args:
            outcomes: List of outcome row dicts (matching engine_cycle_outcomes schema).
            days: Window in days · default 7.

        Returns:
            {"count": int, "avg_composite": float, "success_ratio": float}
            Empty list → {"count": 0, "avg_composite": 0.0, "success_ratio": 0.0}.
        \"\"\"
        # implementation here

IMPLEMENTATION:
- Filter outcomes whose created_at is within last `days` days (assume created_at key
  is a datetime · skip rows without it).
- count = len of filtered list
- avg_composite = mean of composite_score in filtered (0.0 if empty)
- success_ratio = count where ship_status == 'success' / count (0.0 if empty)
- Round avg_composite + success_ratio to 3 decimal places.

MINIMAL CHANGE MODE: Keep ALL existing 5 functions byte-for-byte identical.
Keep module docstring identical. Add only the new function + its imports if
needed (datetime should be imported via `import datetime as _dt` at top).

Spec-Meta:
  expected_added: 18
  expected_removed: 0
"""


def main() -> int:
    engine = NautilusEngine(base_dir=str(ROOT / "phase3" / "backend"), dry_run=True)
    # First: bare generate to inspect LLM output
    raw = engine.generate(SPEC, max_tokens=4096, temperature=0.1)
    blocks = engine.parse_file_blocks(raw)
    print(f"=== RAW LLM blocks: {len(blocks)} ===")
    for b in blocks:
        print(f"--- block · {b['path']} · {len(b['content'])} chars ---")
        # Print only the NEW function (after compute_drift_ratio)
        text = b["content"]
        if "aggregate_recent" in text:
            idx = text.find("def aggregate_recent")
            print(text[idx:idx + 1200])
            print("---")
        else:
            print("!!! aggregate_recent NOT in output !!!")
            print(text[-1500:])

    result = ship(
        engine,
        task=SPEC,
        base_dir=str(ROOT / "phase3" / "backend"),
        apply=False,  # DRY-RUN first · review LLM output before apply
        dispatch_audit=False,
        cycle_id="stage1_self_dogfood_2026-05-25_aggregate_recent",
    )

    print(f"\nship_status: {'applied' if result.applied else 'NOT applied'}")
    print(f"errors: {result.errors[:3]}")
    print(f"check_result.passed: {result.check_result.get('passed')}")
    print(f"files_planned: {[f['path'] for f in result.files_planned]}")

    # Show LLM output for review
    if result.attempts:
        last = result.attempts[-1]
        # _blocks was stripped in public_attempts
        print(f"\nlast attempt · check_result: {last.get('check_result', {}).get('passed')}")
        for c in (last.get('check_result', {}).get('checks', []) or []):
            print(f"  check: {c.get('name')} → {c.get('passed')}")

    print(f"\nstaged blocks · review then re-run with apply=True if OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Stage 1 Day 5 · backfill 6 historical engine cycles to engine_cycle_outcomes.

Per docs/plans/2026-05-25-engine-metric-loop-stage1-design.md § 5.1.

Historical cycles were shipped BEFORE Stage 1 telemetry existed · their
git_numstat is the only mechanical signal available. We assume:
- ship_status = "success" (all 6 commits merged to master · verified history)
- semantic_pass = None (cycle 12 P1 didn't exist when most were shipped)
- tests_pass = True (current master test suite passes · these commits work)
- spec_expected_added/removed = actual_added/removed (assume each commit
  shipped exactly what it intended · drift_ratio = 1.0 perfect match)

Composite degrades to mean(semantic=None, tests=1, drift=1) = 1.0 for all 6.
Baseline avg_composite = 1.0 anchors "0.X → 0.80" 30-day trajectory upward.

Run once · ON CONFLICT DO UPDATE is idempotent.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "phase3" / "backend"))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://nautilus:nautilus_dev_password@localhost:5432/nautilus_dev",
)

from engine.outcome_emit import emit_outcome
from engine.outcomes import compute_composite, compute_drift_ratio


CYCLES = [
    {
        "cycle_id": "cycle_5_2026-05-24_572547e7d",
        "sha": "572547e7d",
        "label": "cycle 5 dogfood · engine __main__ standalone runner via self-ship",
    },
    {
        "cycle_id": "cycle_5b_2026-05-24_ba0ff05fb",
        "sha": "ba0ff05fb",
        "label": "cycle 5b · engine self-fixes both bugs in own __main__.py (recursive)",
    },
    {
        "cycle_id": "cycle_9_2026-05-24_f6ba569d7",
        "sha": "f6ba569d7",
        "label": "cycle 9 dogfood · text_utils.truncate · engine self-ships new utility",
    },
    {
        "cycle_id": "cycle_12p0_14_2026-05-25_343fd53ef",
        "sha": "343fd53ef",
        "label": "cycle 12 P0 + cycle 14 · MINIMAL CHANGE MODE prompt + few-shot example",
    },
    {
        "cycle_id": "cycle_12p1_15_16_2026-05-25_e4f5aca40",
        "sha": "e4f5aca40",
        "label": "cycle 12 P1 + cycle 15 + cycle 16 · semantic check + engine self-shipped context injection",
    },
    {
        "cycle_id": "cycle_17_D1_2026-05-25_9646a3d4b",
        "sha": "9646a3d4b",
        "label": "D1 · text_utils.truncate edge case when max_len <= len(ellipsis)",
    },
]


def git_numstat_for(sha: str, base: Path) -> tuple[int, int]:
    r = subprocess.run(
        ["git", "-C", str(base), "show", "--numstat", "--format=", sha],
        capture_output=True, text=True, check=True,
    )
    added = removed = 0
    for line in r.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            added += int(parts[0])
            removed += int(parts[1])
    return added, removed


def main() -> None:
    base = ROOT
    print(f"Backfilling {len(CYCLES)} historical cycles into engine_cycle_outcomes\n")

    for c in CYCLES:
        added, removed = git_numstat_for(c["sha"], base)
        # Historical: assume commit shipped exactly what intended (drift = 1.0)
        expected_added = added
        expected_removed = removed
        drift = compute_drift_ratio(added, removed, expected_added, expected_removed)
        # semantic_pass unknown for historical · tests_pass current-master-validated True
        composite = compute_composite(semantic=None, tests=True, drift=drift)
        row = {
            "cycle_id": c["cycle_id"],
            "spec": c["label"],
            "spec_expected_added": expected_added,
            "spec_expected_removed": expected_removed,
            "ship_status": "success",
            "semantic_pass": None,
            "tests_pass": True,
            "actual_lines_added": added,
            "actual_lines_removed": removed,
            "drift_ratio": float(drift) if drift is not None else None,
            "composite_score": float(composite),
            "git_sha": c["sha"],
            "cert_id": None,
        }
        emit_outcome(row)
        print(f"  {c['cycle_id']}")
        print(f"    {added}+/{removed}- · drift={drift} · composite={composite}")

    print("\nDone. v_engine_progress should now show 6 historical anchors.")


if __name__ == "__main__":
    main()

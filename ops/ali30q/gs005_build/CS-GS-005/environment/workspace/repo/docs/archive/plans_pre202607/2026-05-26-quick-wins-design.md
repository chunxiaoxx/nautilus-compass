# Quick Wins · 3 Items Design · 2026-05-26

> Brainstorming approved 2026-05-26 · platform dialog · ready for writing-plans.

## Context

Fresh session pickup after 5/25 Stage 1 closed-loop ship (4 PRs merged · master `e160f0d51`). Per `docs/SESSION_HANDOFF_20260525_TO_FRESH.md` Option C "1-2 day quick wins" path chosen over Option A (OSS pivot) or Option B (Stage 2 driver agent). Anchor #2 30-day deadline (2026-06-20) decision deferred.

3 handoff items closed by this design:

1. CLI `--cycle-id` flag wire (plan-phase decision #5 pending in handoff)
2. Dry-run bias fix (closes handoff Gap 2: `avg_composite` 1.000 → 0.875 due to dogfood dry-run row)
3. Nautilus Soul product name documentation (locked product name from 5/25)

## Scope (locked via brainstorming Q&A)

| Item | Depth | Time | Rationale |
|---|---|---|---|
| #1 | L1 wire + smoke test | ~30 min | `ship.py` already has `cycle_id` arg + `_auto_cycle_id` fallback · only CLI plumbing test missing |
| #2 | A emit-skip | ~20 min | Schema unchanged · single control point · accepts dry-run visibility tradeoff |
| #3 | L1 doc-only | ~30 min | NEW root README + setup.py / `__init__.py` mention · binary not renamed · prepares for OSS launch without committing |

### Rejected alternatives

- #1 L0 (just wire) — CLI regression risk without coverage
- #1 L2 (wire+test+docs) — README portion couples with #3, premature
- #2 B view filter (`WHERE git_sha IS NOT NULL`) — loses future granularity (a successful apply that forgets `--commit-msg` would also have NULL git_sha and get incorrectly excluded)
- #2 C schema enum (`ALTER CHECK` add `'dry_run'`) — 60 min · risk against alembic mess (handoff Gap 3)
- #3 L0 (minimal mention only) — OSS users via PyPI cannot see product name at all
- #3 L2 (entry_point alias `nautilus-soul`) — 60 min · `pip install -e .` reinstall breaks dev workflow

## Design

### #1 · CLI --cycle-id flag

**File**: `phase3/cli/nautilus_cli/__main__.py`

Two edits:

1. After line 415 (existing `p_code.add_argument("--a2a-timeout", ...)`), append:
   ```python
   p_code.add_argument(
       "--cycle-id", default=None,
       help="Cycle ID for outcome telemetry (default: auto YYYYMMDD_sha8(task))"
   )
   ```

2. In `cmd_code()` (around line 315-330), `ship()` call adds `cycle_id=args.cycle_id`.

**Test**: NEW `phase3/cli/tests/test_main_cycle_id.py`

```python
from unittest.mock import patch, MagicMock
from nautilus_cli.__main__ import main

@patch("nautilus_cli.__main__.cmd_code")
def test_cli_passes_cycle_id_when_given(mock_cmd):
    mock_cmd.return_value = 0
    main(["code", "test task", "--cycle-id", "abc123", "--no-audit", "--no-repo-map"])
    args = mock_cmd.call_args[0][0]
    assert args.cycle_id == "abc123"

@patch("nautilus_cli.__main__.cmd_code")
def test_cli_cycle_id_default_none(mock_cmd):
    mock_cmd.return_value = 0
    main(["code", "test task", "--no-audit", "--no-repo-map"])
    args = mock_cmd.call_args[0][0]
    assert args.cycle_id is None
```

(NEW file requires `phase3/cli/tests/__init__.py` if not already present.)

### #2 · emit-skip dry-run

**File**: `phase3/backend/engine/ship.py`

Modify `_emit_outcome_safe()` (around line 575) to add an early guard:

```python
def _emit_outcome_safe(result, task, base, cycle_id):
    """Build + emit outcome row · NEVER raises.

    Skips dry-run cycles (no apply · no errors · has blocks) to avoid
    biasing v_engine_progress.avg_composite downward. Real dry-runs are
    not 'failures' — they're previews · we don't want them weighting the
    success-cycle quality metric. Intentional fails (apply=True with
    errors) and parse_error deadletters still emit normally.
    """
    if not result.applied and not result.errors and result.files_planned:
        return
    try:
        row = _build_outcome_row(result, task, base, cycle_id)
        emit_outcome(row)
    except Exception as e:
        import sys as _sys
        _sys.stderr.write(
            f"[engine.ship] outcome telemetry unexpected error: "
            f"{type(e).__name__}: {e}\n"
        )
```

**Test**: NEW `phase3/backend/engine/tests/test_ship_emit_telemetry.py`

Four cases (all using mocked `emit_outcome` to inspect call args, no DB needed):

| Test | Setup | Assertion |
|---|---|---|
| `test_emit_skipped_when_dry_run_success` | stub engine produces 1 block · checks pass · `apply=False` | `emit_outcome` NOT called |
| `test_emit_called_when_apply_fails_with_errors` | stub produces blocks · checks fail · `apply=True` | `emit_outcome` called once · row has `ship_status` != 'success' |
| `test_emit_called_when_apply_success` | stub produces blocks · checks pass · `apply=True` (no real git commit needed if we mock `_git_add_commit`) | `emit_outcome` called once |
| `test_emit_called_when_parse_error_deadletter` | stub returns no blocks (`is_deadletter` true) | `emit_outcome` called with `reason='parse_error'` row |

Uses a minimal `FakeEngine` class with `generate()` + `parse_file_blocks()` methods, plus `monkeypatch.setattr` on `engine.ship.emit_outcome` to capture calls.

### #3 · README + Nautilus Soul mention

**NEW** `README.md` at repo root (target ~50 lines):

````markdown
# Nautilus Soul

Recursive code engine with closed-loop metric telemetry.
Generate → check → audit → apply → outcome telemetry → improve next cycle.

## Install

```
cd phase3/cli && pip install -e .
```

## Quick start

```
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
export NAUTILUS_API_KEY=nau_...    # optional · audit cert dispatch
nautilus code "add a fib() function to math_utils.py" \
  --base-dir my_project --apply --commit-msg "feat: add fib util"
```

## Pipeline

- Generate code via LLM backend
- Static checks (ruff · py_compile · semantic preservation · runtime smoke)
- Audit dispatch (`/api/v1/audit/dispatch` → 3-agent council cert · optional)
- Apply files + git commit (optional)
- Outcome telemetry → `engine_cycle_outcomes` PG table
- Progress view: `SELECT * FROM v_engine_progress;`

## What is closed-loop?

Every cycle writes a row to `engine_cycle_outcomes` capturing:
spec drift · semantic preservation · test pass · composite quality score.
The view `v_engine_progress` aggregates these into daily quality trends
the engine itself can read and improve from.

## License

MIT · see `phase3/cli/setup.py`.

## Repo

https://github.com/chunxiaoxx/nautilus-core
````

**Edit** `phase3/cli/setup.py` description:
- Old: `"Nautilus CLI · multi-agent audit with stake-backed cert · github.com/chunxiaoxx/nautilus-core"`
- New: `"Nautilus CLI (product: Nautilus Soul) · multi-agent audit with stake-backed cert · github.com/chunxiaoxx/nautilus-core"`

**Edit** `phase3/cli/nautilus_cli/__init__.py` docstring:
- Old: `"""Nautilus CLI v0 · 国产 multi-agent audit CLI · 类 Claude Code 但加 audit cert + stake."""`
- New: `"""Nautilus CLI v0 (product: Nautilus Soul) · 国产 multi-agent audit CLI · 类 Claude Code 但加 audit cert + stake."""`

## Ship sequence

Three commits direct to master (no PR · solo · low risk):

1. **Commit 1** · #2 emit-skip — smallest · independent · directly closes Gap 2
   - Add `phase3/backend/engine/tests/test_ship_emit_telemetry.py`
   - Modify `phase3/backend/engine/ship.py` `_emit_outcome_safe()`
   - Run `pytest phase3/backend/engine/tests/` (expect baseline + 4 new green)
   - `git commit -m "fix(engine): Stage 1 · skip emit for dry-run cycles (closes handoff Gap 2)"`

2. **Commit 2** · #1 CLI wire
   - Add `phase3/cli/tests/test_main_cycle_id.py` (+ `__init__.py` if needed)
   - Modify `phase3/cli/nautilus_cli/__main__.py` argparse + ship call
   - Run `pytest phase3/cli/tests/ phase3/backend/engine/tests/`
   - `git commit -m "feat(cli): wire --cycle-id flag to engine ship (plan decision #5)"`

3. **Commit 3** · #3 README + mentions
   - Create `README.md` at repo root
   - Modify `phase3/cli/setup.py` description
   - Modify `phase3/cli/nautilus_cli/__init__.py` docstring
   - Run `pytest phase3/cli/tests/ phase3/backend/engine/tests/` (regression only)
   - `git commit -m "docs: introduce Nautilus Soul product name + root README"`

## Tests baseline

Stage 1 master tip: 173 tests green.
After this design: 173 + 4 (test_ship_emit_telemetry) + 2 (test_main_cycle_id) = **179 expected green**.

Stage 1 PG smoke tests require docker `nautilus-postgres` (still running per handoff).

## Risk · low

All surface-level changes:
- #2 emit guard is opt-out · all 4 corner cases unit-covered
- #1 CLI plumbing test mocks `cmd_code` · no integration touched
- #3 doc + 2 string edits · no functional code change

## Out of scope (explicit)

- Composite formula (already fixed cycle 17)
- Alembic migration to formalize Stage 1 schema (cross-dialog · handoff says defer to Stage 2)
- Root `LICENSE` file (Option A pivot scope · setup.py already declares MIT)
- Binary `nautilus-soul` alias entry_point (rejected · L2)
- `docs/ANCHOR2_OUTREACH_KIT_20260525.md` rewrite (Option A pivot scope)
- Backfill historic dry-run row in `engine_cycle_outcomes` (decision: emit-skip prevents future bias · existing 1 dogfood row keeps as evidence)
- `--cycle-id` CLI flag for any subcommand other than `code` (out of scope · only `code` invokes `ship()`)

— platform dialog · 2026-05-26 · brainstorming approved · ready for writing-plans

# Quick Wins (3 Items) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship 3 surface-level improvements: CLI `--cycle-id` flag wire, dry-run emit-skip (closes Gap 2), and Nautilus Soul product name documentation.

**Architecture:** TDD per item. 3 commits direct to master. No PR, no cross-dialog touches, no alembic. Design source: `docs/plans/2026-05-26-quick-wins-design.md`.

**Tech Stack:** Python 3.8+, pytest, argparse, MagicMock (stdlib unittest), Postgres 15 (docker `nautilus-postgres` for view smoke).

---

## Pre-flight (run once · 2 min)

**Step A · Confirm working tree clean of pending plan-related changes**

Run: `git status --short | grep -E "(plan|README|setup\.py|__main__\.py|ship\.py|test_ship_emit|test_main_cycle)"`
Expected: empty (no in-progress edits in target files).

**Step B · Confirm Stage 1 baseline tests are green**

Run: `cd phase3/backend && pytest engine/tests/ -q 2>&1 | tail -5`
Expected: 173 passed (or 173 passed + N skipped if PG tests skip without docker).

**Step C · Confirm docker postgres still up (for PG smoke in Phase 4)**

Run: `docker ps --filter "name=nautilus-postgres" --format "{{.Names}} {{.Status}}"`
Expected: `nautilus-postgres Up ...` (handoff says still running).
If empty → Phase 4 PG view check will be skipped, not blocked.

---

## Phase 1 · #2 emit-skip dry-run (~25 min · 1 commit)

**Files:**
- Modify: `phase3/backend/engine/ship.py` (function `_emit_outcome_safe`, around line 575)
- Modify: `phase3/backend/engine/tests/test_ship_outcome_hook.py` (function `test_ship_emits_outcome_on_dryrun_with_blocks`, lines 40-69)
- Create: `phase3/backend/engine/tests/test_ship_emit_telemetry.py`

### Task 1.1 · Write the failing test file (NEW)

**Step 1: Create `phase3/backend/engine/tests/test_ship_emit_telemetry.py`**

```python
"""Test emit-skip behavior for dry-run cycles · closes Gap 2 (handoff 2026-05-25).

The skip rule: if ship completes with apply=False AND no errors AND
parseable blocks → it is a dry-run preview, not a failure. Such rows
would bias v_engine_progress.avg_composite downward.
"""
from unittest.mock import MagicMock, patch

from engine.nautilus_engine import NautilusEngine
from engine.ship import ship


def _mock_llm(text: str) -> MagicMock:
    fake = MagicMock()
    fake.chat = MagicMock(return_value=text)
    return fake


_VALID_BLOCK = (
    "```python:hello.py\n"
    "def greet():\n"
    "    return 'hi'\n"
    "```\n"
)


def test_emit_skipped_when_dry_run_success(tmp_path, monkeypatch):
    """apply=False · checks pass · no errors · has blocks → NO emit."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm(_VALID_BLOCK),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        result = ship(
            eng, task="add greet to hello.py",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    assert result is not None
    assert not result.applied
    assert not result.errors, f"dry-run with passing checks should have no errors · got {result.errors}"
    assert captured == [], f"dry-run with passing checks must NOT emit · captured {len(captured)} row(s)"


def test_emit_called_when_apply_success(tmp_path, monkeypatch):
    """apply=True · checks pass → emit called once with ship_status row."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm(_VALID_BLOCK),
        base_dir=str(tmp_path),
        dry_run=True,  # engine-level dry_run · ship() apply=True writes anyway
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="add greet",
            base_dir=str(tmp_path),
            apply=True, dispatch_audit=False,
        )
    assert len(captured) == 1, f"apply=True success must emit exactly 1 row · captured {len(captured)}"
    assert captured[0].get("reason") is None
    assert "ship_status" in captured[0]


def test_emit_called_when_parse_error_deadletter(tmp_path, monkeypatch):
    """LLM returns no parseable blocks → deadletter row emitted (NOT skipped)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = NautilusEngine(
        llm_client=_mock_llm("just prose no fenced code"),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="x",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    assert len(captured) == 1
    assert captured[0].get("reason") == "parse_error", f"deadletter row · got {captured[0]}"


def test_emit_called_when_dry_run_has_errors(tmp_path, monkeypatch):
    """apply=False BUT checks fail (errors set) → emit called (intentional fail visible)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # LLM returns syntax-broken Python · check pipeline fails · errors set
    broken = (
        "```python:broken.py\n"
        "def f(:\n"  # syntax error
        "    pass\n"
        "```\n"
    )
    eng = NautilusEngine(
        llm_client=_mock_llm(broken),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    captured = []
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: captured.append(row)):
        ship(
            eng, task="x",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    # apply=False + errors set → not dry-run-success · MUST emit
    assert len(captured) == 1, f"dry-run with check failures must emit · captured {len(captured)}"
    assert captured[0].get("reason") is None  # not deadletter · normal row
    assert captured[0]["ship_status"] in ("fail", "partial")
```

**Step 2: Run new tests · verify 4 fail (RED)**

Run: `cd phase3/backend && pytest engine/tests/test_ship_emit_telemetry.py -v 2>&1 | tail -20`
Expected: 
- `test_emit_skipped_when_dry_run_success` FAIL (assertion `captured == []` fails · currently emit always called)
- `test_emit_called_when_apply_success` PASS (existing behavior · emit called)
- `test_emit_called_when_parse_error_deadletter` PASS (existing behavior · deadletter emit)
- `test_emit_called_when_dry_run_has_errors` PASS (existing behavior · emit called)

So actually only 1 of 4 is RED. The other 3 are regression-protection (will be GREEN immediately). That's fine for TDD — the 1 RED is the behavior change.

### Task 1.2 · Update conflicting existing test

**Step 1: Edit `phase3/backend/engine/tests/test_ship_outcome_hook.py` lines 40-69**

The existing `test_ship_emits_outcome_on_dryrun_with_blocks` will start failing once we implement the guard (apply=False with passing checks no longer emits). Update it to test the new behavior:

Rename function to `test_ship_skips_emit_on_dryrun_with_passing_blocks`. Replace assertion block (current lines 63-69) with:

```python
    # After Gap 2 fix (emit-skip dry-run): apply=False + passing checks + no errors
    # → row is skipped to avoid biasing v_engine_progress.avg_composite.
    assert captured == [], f"dry-run with passing blocks should be skipped · got {len(captured)} row(s)"
```

Remove the now-irrelevant assertions on `ship_status`, `composite_score`, `tests_pass`.

**Step 2: Run modified test · verify it currently FAILS (RED · because guard not yet implemented)**

Run: `cd phase3/backend && pytest engine/tests/test_ship_outcome_hook.py::test_ship_skips_emit_on_dryrun_with_passing_blocks -v 2>&1 | tail -10`
Expected: FAIL with `assert captured == []` (currently captured has 1 row).

### Task 1.3 · Implement the emit-skip guard

**Step 1: Edit `phase3/backend/engine/ship.py` function `_emit_outcome_safe` (around line 575)**

Replace existing function body with:

```python
def _emit_outcome_safe(result: ShipResult, task: str, base: Path, cycle_id: str) -> None:
    """Build + emit outcome row · NEVER raises (catches even row construction errors).

    Skips dry-run cycles (no apply · no errors · has blocks) to avoid biasing
    v_engine_progress.avg_composite. Such rows are previews, not failures —
    counting them as ship_status='fail' with composite=0 drags down the metric
    that drives Stage 2 driver agent decisions (closes handoff 2026-05-25 Gap 2).

    Still emits: applied cycles (success/fail), intentional fails (errors set),
    parse_error deadletters (no blocks).
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

**Step 2: Run both touched test files · verify GREEN**

Run: `cd phase3/backend && pytest engine/tests/test_ship_emit_telemetry.py engine/tests/test_ship_outcome_hook.py -v 2>&1 | tail -20`
Expected: All 4 new + all 7 in test_ship_outcome_hook.py (now 1 renamed) PASS.

### Task 1.4 · Full engine regression

**Step 1: Run full engine test suite**

Run: `cd phase3/backend && pytest engine/tests/ -q 2>&1 | tail -5`
Expected: `177 passed` (173 baseline + 4 new). Note: existing test was renamed, not added, so total = 173 + 4.

If anything fails that didn't fail in pre-flight Step B → STOP, the guard introduced a side effect. Debug before commit.

### Task 1.5 · Commit Phase 1

**Step 1: Stage exact files**

```bash
git add phase3/backend/engine/ship.py \
        phase3/backend/engine/tests/test_ship_emit_telemetry.py \
        phase3/backend/engine/tests/test_ship_outcome_hook.py
```

**Step 2: Verify staged set**

Run: `git diff --cached --stat`
Expected: 3 files · ship.py ~+8/-1 · test_ship_emit_telemetry.py +90 · test_ship_outcome_hook.py +/- small.

**Step 3: Commit**

```bash
git commit -m "fix(engine): Stage 1 · skip emit for dry-run cycles (closes handoff Gap 2)"
```

**Step 4: Verify commit landed**

Run: `git log --oneline -1`
Expected: new commit on top of `2fdb0c89f`.

---

## Phase 2 · #1 CLI --cycle-id flag wire (~35 min · 1 commit)

**Files:**
- Create: `phase3/cli/tests/__init__.py`
- Create: `phase3/cli/tests/conftest.py`
- Create: `phase3/cli/tests/test_main_cycle_id.py`
- Modify: `phase3/cli/nautilus_cli/__main__.py` (add `--cycle-id` argument and pass to `ship()`)

### Task 2.1 · Create test directory + conftest

**Step 1: Create `phase3/cli/tests/__init__.py`**

Content (empty file with marker):
```python
"""Tests for nautilus-cli."""
```

**Step 2: Create `phase3/cli/tests/conftest.py`**

Needed because pytest discovery from repo root won't put `phase3/cli/` on sys.path automatically. Conftest fix is local + minimal.

```python
"""Local sys.path bootstrap so `from nautilus_cli.__main__ import main` works
when pytest is invoked from outside phase3/cli/ (e.g. repo root)."""
import sys
from pathlib import Path

_CLI_ROOT = Path(__file__).resolve().parent.parent
if str(_CLI_ROOT) not in sys.path:
    sys.path.insert(0, str(_CLI_ROOT))
```

**Step 3: Verify import path works**

Run: `cd phase3/cli && python -c "from nautilus_cli.__main__ import main; print('ok')"`
Expected: `ok`

### Task 2.2 · Write failing tests

**Step 1: Create `phase3/cli/tests/test_main_cycle_id.py`**

```python
"""CLI plumbing: --cycle-id flag must reach engine.ship.ship(cycle_id=...).

Mocks cmd_code to capture the parsed argparse.Namespace · does not call
the real engine (which needs DATABASE_URL + network for audit).
"""
from unittest.mock import patch

from nautilus_cli.__main__ import main


@patch("nautilus_cli.__main__.cmd_code")
def test_cli_passes_cycle_id_when_given(mock_cmd):
    """User passes --cycle-id abc123 · args.cycle_id must equal 'abc123'."""
    mock_cmd.return_value = 0
    rc = main([
        "code", "demo task",
        "--cycle-id", "abc123",
        "--no-audit", "--no-repo-map",
        "--base-dir", ".",
    ])
    assert rc == 0
    mock_cmd.assert_called_once()
    args = mock_cmd.call_args[0][0]
    assert args.cycle_id == "abc123"


@patch("nautilus_cli.__main__.cmd_code")
def test_cli_cycle_id_default_none(mock_cmd):
    """No --cycle-id given · args.cycle_id must default to None (ship() then auto-generates)."""
    mock_cmd.return_value = 0
    rc = main([
        "code", "demo task",
        "--no-audit", "--no-repo-map",
        "--base-dir", ".",
    ])
    assert rc == 0
    args = mock_cmd.call_args[0][0]
    assert args.cycle_id is None
```

**Step 2: Run tests · verify RED**

Run: `cd phase3/cli && pytest tests/test_main_cycle_id.py -v 2>&1 | tail -15`
Expected:
- `test_cli_passes_cycle_id_when_given` FAIL with `error: unrecognized arguments: --cycle-id abc123` (argparse rejects unknown flag · `main` raises SystemExit before mock is called).
- `test_cli_cycle_id_default_none` FAIL with `AttributeError: 'Namespace' object has no attribute 'cycle_id'`.

### Task 2.3 · Add the argparse argument

**Step 1: Edit `phase3/cli/nautilus_cli/__main__.py`**

After line 415 (last `p_code.add_argument` for `--a2a-timeout`), append before `p_code.set_defaults(func=cmd_code)`:

```python
    p_code.add_argument(
        "--cycle-id", default=None,
        help="Cycle ID for outcome telemetry (default: auto YYYYMMDD_sha8(task))",
    )
```

**Step 2: Run tests · verify GREEN**

Run: `cd phase3/cli && pytest tests/test_main_cycle_id.py -v 2>&1 | tail -10`
Expected: 2 passed (argparse now accepts flag · Namespace has cycle_id attr · default None when omitted).

### Task 2.4 · Pass cycle_id to ship()

**Step 1: Edit `phase3/cli/nautilus_cli/__main__.py` `cmd_code()` ship() call**

Around line 315, the existing `ship(...)` call ends with `a2a_timeout=args.a2a_timeout,` (line 330). Add one more keyword argument before the closing `)`:

```python
        cycle_id=args.cycle_id,
```

**Step 2: Re-run CLI tests (no behavior change expected · still GREEN)**

Run: `cd phase3/cli && pytest tests/test_main_cycle_id.py -v 2>&1 | tail -10`
Expected: 2 passed.

### Task 2.5 · Full regression (engine + cli)

**Step 1: Run engine tests**

Run: `cd phase3/backend && pytest engine/tests/ -q 2>&1 | tail -5`
Expected: 177 passed (no regression vs Phase 1 baseline).

**Step 2: Run CLI tests**

Run: `cd phase3/cli && pytest tests/ -q 2>&1 | tail -5`
Expected: 2 passed.

### Task 2.6 · Commit Phase 2

**Step 1: Stage exact files**

```bash
git add phase3/cli/nautilus_cli/__main__.py \
        phase3/cli/tests/__init__.py \
        phase3/cli/tests/conftest.py \
        phase3/cli/tests/test_main_cycle_id.py
```

**Step 2: Verify staged set**

Run: `git diff --cached --stat`
Expected: 4 files · __main__.py +~6 lines · 3 new test scaffolding files.

**Step 3: Commit**

```bash
git commit -m "feat(cli): wire --cycle-id flag to engine ship (plan decision #5)"
```

---

## Phase 3 · #3 README + Nautilus Soul mention (~30 min · 1 commit)

**Files:**
- Create: `README.md` (repo root)
- Modify: `phase3/cli/setup.py` (description on line 7)
- Modify: `phase3/cli/nautilus_cli/__init__.py` (docstring on line 1)

### Task 3.1 · Create root README

**Step 1: Create `README.md` at repo root**

```markdown
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
- Outcome telemetry → `engine_cycle_outcomes` Postgres table
- Progress view: `SELECT * FROM v_engine_progress;`

## Closed-loop telemetry

Every cycle writes a row to `engine_cycle_outcomes` capturing:
spec drift · semantic preservation · test pass · composite quality score.
The view `v_engine_progress` aggregates these into daily quality trends
the engine itself can read and improve from.

## License

MIT · see `phase3/cli/setup.py`.

## Repo

https://github.com/chunxiaoxx/nautilus-core
```

(Note: the inner triple-backtick fences inside the markdown will render as code blocks. Write them as-is.)

### Task 3.2 · Edit setup.py description

**Step 1: Edit `phase3/cli/setup.py` line 7**

Replace exact string:
- Old: `description="Nautilus CLI · multi-agent audit with stake-backed cert · github.com/chunxiaoxx/nautilus-core",`
- New: `description="Nautilus CLI (product: Nautilus Soul) · multi-agent audit with stake-backed cert · github.com/chunxiaoxx/nautilus-core",`

**Step 2: Verify setup.py still imports cleanly**

Run: `cd phase3/cli && python -c "import ast; ast.parse(open('setup.py').read()); print('ok')"`
Expected: `ok`

### Task 3.3 · Edit __init__.py docstring

**Step 1: Edit `phase3/cli/nautilus_cli/__init__.py` line 1**

Replace exact string:
- Old: `"""Nautilus CLI v0 · 国产 multi-agent audit CLI · 类 Claude Code 但加 audit cert + stake."""`
- New: `"""Nautilus CLI v0 (product: Nautilus Soul) · 国产 multi-agent audit CLI · 类 Claude Code 但加 audit cert + stake."""`

**Step 2: Verify import still works**

Run: `cd phase3/cli && python -c "import nautilus_cli; print(nautilus_cli.__version__)"`
Expected: `0.1.0`

### Task 3.4 · Verify both name mentions are present

Run: `grep -l "Nautilus Soul" README.md phase3/cli/setup.py phase3/cli/nautilus_cli/__init__.py`
Expected: all 3 file paths listed.

### Task 3.5 · Full regression (no functional code change · should be no-op)

**Step 1: Engine tests**

Run: `cd phase3/backend && pytest engine/tests/ -q 2>&1 | tail -5`
Expected: 177 passed.

**Step 2: CLI tests**

Run: `cd phase3/cli && pytest tests/ -q 2>&1 | tail -5`
Expected: 2 passed.

### Task 3.6 · Commit Phase 3

**Step 1: Stage exact files**

```bash
git add README.md phase3/cli/setup.py phase3/cli/nautilus_cli/__init__.py
```

**Step 2: Verify staged set**

Run: `git diff --cached --stat`
Expected: 3 files · README.md new ~45 lines · setup.py ±1 line · __init__.py ±1 line.

**Step 3: Commit**

```bash
git commit -m "docs: introduce Nautilus Soul product name + root README"
```

---

## Phase 4 · Wrap-up verify (~10 min · no commit)

### Task 4.1 · Verify the 3 commits landed

Run: `git log --oneline -5`
Expected: top 3 are the new commits, then `2fdb0c89f` (design doc), then `e160f0d51` (handoff).

### Task 4.2 · PG view smoke (optional · if docker up)

Verify `v_engine_progress` view query still works after emit-skip change.

Run: `docker exec -i nautilus-postgres psql -U nautilus -d nautilus_dev -c "SELECT * FROM v_engine_progress;"`
Expected: returns 1+ rows of daily aggregates (existing data from 5/25). No SQL error.

If docker down → skip · acceptable.

### Task 4.3 · Confirm NO push

Per handoff hard prereq · token rotation pending. Do NOT push.

Run: `git status -b --short | head -1`
Expected: `## master...origin/master [ahead 5]` (or similar · 5 = handoff + design + 3 quick wins).

### Task 4.4 · Hand off back to user

Three commits ready locally. User runs token rotation then:
```
git push origin master
```

Do NOT invoke `finishing-a-development-branch` skill — it's already merged-equivalent (commits on master). The branch is "finished" by virtue of being committed; only the push waits.

---

## Out of scope (do not touch in this plan)

- Composite formula (already fixed cycle 17)
- Alembic migration (cross-dialog · handoff defers)
- Root `LICENSE` file (Option A pivot scope · setup.py declares MIT)
- Binary `nautilus-soul` alias entry_point (rejected · L2 scope)
- `docs/ANCHOR2_OUTREACH_KIT_20260525.md` rewrite (Option A pivot scope)
- Backfill historic dry-run row in `engine_cycle_outcomes`
- `--cycle-id` for any subcommand other than `code`

## Test count summary

| Phase | New tests | Modified | Total after |
|---|---|---|---|
| Baseline (master) | — | — | 173 |
| Phase 1 (#2 emit-skip) | +4 | 1 renamed-and-flipped | 177 (engine) |
| Phase 2 (#1 CLI wire) | +2 | — | 177 engine + 2 cli = 179 |
| Phase 3 (#3 docs) | 0 | — | 179 |

— platform dialog · 2026-05-26 · plan ready for executing-plans

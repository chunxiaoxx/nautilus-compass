# Engine Metric Closed-Loop · Stage 1 · Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire engine ship pipeline → platform DB so every cycle emits a composite metric row · enabling 30-day "0.51 → 0.80" trajectory tracking. Read-only outcomes recording. No driver agent yet.

**Architecture:** See `docs/plans/2026-05-25-engine-metric-loop-stage1-design.md` (master `ce3a8ab66`). Two tables (`engine_cycle_outcomes` + `engine_cycle_deadletter`) + one view (`v_engine_progress`). Three new modules under `phase3/backend/engine/`: `outcomes.py` (classify + compute_composite + parse_spec_meta) · `pytest_runner.py` · `outcome_emit.py`. One hook in `ship.py` (final pre-return step). Spec format gains optional `Spec-Meta:` block. Invariant: telemetry MUST NEVER raise into the ship pipeline.

**Tech Stack:** Python 3.13 · alembic · psycopg (3.x) · pytest · existing engine modules.

---

## Plan-Phase Decisions (decide BEFORE code · these resolve design § 8)

Each has a recommendation. If user disagrees, override in this section before Task 1.

| # | Question | Options | Recommendation | Locked? |
|---|---|---|---|---|
| 1 | Postgres DSN source | (a) reuse `agent_engine` `DATABASE_URL` env / (b) new `ENGINE_METRICS_DB_URL` | **(a) reuse** · same DB · minimal config surface · alembic already configured for it | ☐ |
| 2 | pytest test-file convention | (a) only `<dir>/tests/test_<basename>.py` / (b) also module-root `tests/test_<basename>.py` / (c) glob `**/test_<basename>.py` | **(a) only** · matches engine/tests/ pattern · D1 follows it · cheapest to ship | ☐ |
| 3 | `Spec-Meta:` parser strictness | (a) strict (malformed → raise) / (b) permissive (warn + NULL fields) | **(b) permissive** · honors design § 4 invariant "telemetry never breaks ship" | ☐ |
| 4 | `cycle_id` generation | (a) SHA256(task+ts)[:16] auto / (b) human-readable "D1_2026-05-25_truncate" / (c) hybrid | **(c) hybrid** · auto = `{YYYYMMDD}_{sha8}` · CLI `--cycle-id` overrides with human-readable | ☐ |
| 5 | CLI `--cycle-id` flag | yes / no | **yes** · needed for Day 5 backfill (cycle 5/9/12/15/17) | ☐ |

User confirms by ticking checkboxes (or override) before Task 1.

---

## Day 1 · Schema + spec_meta parser

### Task 1.1: Write alembic migration

**Files:**
- Create: `phase3/backend/alembic/versions/<rev>_engine_cycle_outcomes.py`

**Step 1: Generate migration skeleton**

```bash
cd phase3/backend && alembic revision -m "engine cycle outcomes + deadletter + progress view"
```

Expected: new file in `alembic/versions/<timestamp>_engine_cycle_outcomes_*.py`

**Step 2: Fill `upgrade()` with the 2 tables + view + 2 indexes**

Copy the SQL block from design § 3.2 component A. Use `op.create_table`, `op.create_index`, `op.execute("CREATE VIEW ...")`.

**Step 3: Fill `downgrade()`** — `DROP VIEW` first, then `DROP TABLE` in reverse order.

**Step 4: Verify migration parses**

```bash
cd phase3/backend && alembic upgrade head --sql > /tmp/migration.sql
```

Expected: SQL printed · no Python errors.

**Step 5: Apply migration to local DB**

```bash
cd phase3/backend && alembic upgrade head
```

Expected: "Running upgrade ... -> ..., engine cycle outcomes..."

**Step 6: Verify schema landed**

```bash
psql $DATABASE_URL -c "\d engine_cycle_outcomes" -c "\d engine_cycle_deadletter" -c "\d+ v_engine_progress"
```

Expected: 2 tables shown · 1 view shown · all columns match design § 3.2.

**Step 7: Commit**

```bash
git add phase3/backend/alembic/versions/*_engine_cycle_outcomes.py
git commit -m "feat(engine): alembic · engine_cycle_outcomes + deadletter + v_engine_progress"
```

### Task 1.2: TDD `parse_spec_meta` in outcomes.py

**Files:**
- Create: `phase3/backend/engine/outcomes.py` (module)
- Create: `phase3/backend/engine/tests/test_outcomes.py`

**Step 1: Write failing tests** (8-10 cases · `tests/test_outcomes.py::test_parse_spec_meta_*`):

```python
from engine.outcomes import parse_spec_meta

def test_parse_spec_meta_present():
    task = "do thing\n\nSpec-Meta:\n  expected_added: 2\n  expected_removed: 0\n"
    assert parse_spec_meta(task) == {"expected_added": 2, "expected_removed": 0}

def test_parse_spec_meta_absent():
    assert parse_spec_meta("just a task") == {"expected_added": None, "expected_removed": None}

def test_parse_spec_meta_partial():
    task = "x\n\nSpec-Meta:\n  expected_added: 5\n"
    assert parse_spec_meta(task) == {"expected_added": 5, "expected_removed": None}

def test_parse_spec_meta_malformed_permissive():
    task = "x\n\nSpec-Meta:\n  expected_added: not-an-int\n"
    # Permissive · per plan-phase decision #3 · warn + NULL
    assert parse_spec_meta(task) == {"expected_added": None, "expected_removed": None}

def test_parse_spec_meta_extra_whitespace():
    task = "x\n\nSpec-Meta:\n  expected_added:    2   \n  expected_removed: 0  \n"
    assert parse_spec_meta(task) == {"expected_added": 2, "expected_removed": 0}
```

**Step 2: Run · verify all FAIL**

```bash
cd phase3/backend && python -m pytest engine/tests/test_outcomes.py::test_parse_spec_meta_present -v
```

Expected: `ImportError: cannot import name 'parse_spec_meta'`

**Step 3: Implement `parse_spec_meta`** in `outcomes.py` (~20 LOC · regex on `Spec-Meta:\s*\n((?:\s+\w+:\s*\S+\n?)+)` · per-line `\s+(\w+):\s*(\S+)` · `int()` in try/except · log warn on parse fail).

**Step 4: Run · verify all PASS**

```bash
cd phase3/backend && python -m pytest engine/tests/test_outcomes.py -v -k parse_spec_meta
```

Expected: 5 passed.

**Step 5: Commit**

```bash
git add phase3/backend/engine/outcomes.py phase3/backend/engine/tests/test_outcomes.py
git commit -m "feat(engine): parse_spec_meta · permissive parser · null-degrade"
```

**Day 1 deliverable / verification gate:**
- `alembic upgrade head` clean
- `\d engine_cycle_outcomes` shows all design § 3.2 columns
- `parse_spec_meta` 5/5 tests pass

---

## Day 2 · Composite metric + classify

### Task 2.1: TDD `compute_composite`

**Files:**
- Modify: `phase3/backend/engine/outcomes.py`
- Modify: `phase3/backend/engine/tests/test_outcomes.py`

**Step 1: Write failing tests** (~6 cases):

```python
from engine.outcomes import compute_composite

def test_composite_all_three_signals_perfect():
    assert compute_composite(semantic=True, tests=True, drift=0.0) == 1.0

def test_composite_drift_capped_to_zero():
    # drift > 1 ⇒ (1-drift) < 0 ⇒ clamped to 0
    assert compute_composite(True, True, drift=2.0) == round((1+1+0)/3, 3)

def test_composite_null_degrade_two_signals():
    # tests unavailable ⇒ average over 2 signals
    assert compute_composite(True, None, drift=0.0) == round((1+1)/2, 3)

def test_composite_null_degrade_one_signal():
    assert compute_composite(True, None, None) == 1.0

def test_composite_all_null_zero():
    assert compute_composite(None, None, None) == 0.0  # nothing measured ⇒ 0

def test_composite_partial():
    assert compute_composite(True, False, drift=0.5) == round((1+0+0.5)/3, 3)
```

**Step 2: Run · verify FAIL**

**Step 3: Implement** (~15 LOC · null-degrade · clamp drift):

```python
def compute_composite(semantic, tests, drift):
    signals = []
    if semantic is not None: signals.append(1.0 if semantic else 0.0)
    if tests is not None:    signals.append(1.0 if tests else 0.0)
    if drift is not None:    signals.append(max(0.0, min(1.0, 1.0 - drift)))
    if not signals: return 0.0
    return round(sum(signals) / len(signals), 3)
```

**Step 4: Run · verify PASS**

**Step 5: Commit**

```bash
git commit -am "feat(engine): compute_composite · null-degrade + drift clamp"
```

### Task 2.2: TDD `classify`

**Files:**
- Modify: `phase3/backend/engine/outcomes.py`
- Modify: `phase3/backend/engine/tests/test_outcomes.py`

**Step 1: Write failing tests** (~7 cases · 4 statuses + edge):

```python
from engine.outcomes import classify
from engine.ship import ShipResult

def test_classify_success():
    r = ShipResult(task="x", applied=True,
                   check_result={"passed": True, "checks": [{"name":"semantic","passed":True}]},
                   errors=[])
    assert classify(r, tests_pass=True, drift=0.5) == "success"

def test_classify_partial_check_fail():
    r = ShipResult(task="x", applied=True,
                   check_result={"passed": False, "checks": []}, errors=["x"])
    assert classify(r, tests_pass=True, drift=0.5) == "partial"

def test_classify_fail_not_applied():
    r = ShipResult(task="x", applied=False, check_result={"passed": False}, errors=["check failed"])
    assert classify(r, tests_pass=None, drift=None) == "fail"

def test_classify_deadletter_no_blocks():
    r = ShipResult(task="x", applied=False,
                   errors=["LLM output had no parseable file blocks (after 1 attempt(s))"])
    assert classify(r, tests_pass=None, drift=None) == "deadletter"

def test_classify_drift_excessive_partial():
    # drift > 1.5 ⇒ partial even if applied + checks pass (over-ship signal)
    r = ShipResult(task="x", applied=True, check_result={"passed": True}, errors=[])
    assert classify(r, tests_pass=True, drift=2.0) == "partial"
```

**Step 2: Run · verify FAIL**

**Step 3: Implement** (~25 LOC):

```python
def classify(result, tests_pass, drift):
    err_str = " ".join(result.errors or "").lower()
    if "no parseable file blocks" in err_str: return "deadletter"
    if not result.applied:
        if not result.check_result.get("passed"): return "fail"
        return "fail"  # not applied for any reason ⇒ fail
    # applied=True
    if not result.check_result.get("passed"): return "partial"
    if tests_pass is False: return "partial"
    if drift is not None and drift > 1.5: return "partial"
    return "success"
```

**Step 4: Run · verify PASS**

**Step 5: Commit**

```bash
git commit -am "feat(engine): classify · 4-status outcome from ShipResult"
```

**Day 2 deliverable / verification gate:**
- `pytest engine/tests/test_outcomes.py -v` ≥ 16 tests pass (5 parse + 6 composite + 5 classify)

---

## Day 3 · pytest_runner

### Task 3.1: TDD `run_pytest_for_changed`

**Files:**
- Create: `phase3/backend/engine/pytest_runner.py`
- Create: `phase3/backend/engine/tests/test_pytest_runner.py`

**Step 1: Write failing tests** (~5 cases · isolated via `tmp_path` fixture):

```python
def test_run_pytest_pass(tmp_path):
    # Setup minimal pkg with foo.py + tests/test_foo.py · test passes
    ...
    assert run_pytest_for_changed(tmp_path, ["pkg/foo.py"]) is True

def test_run_pytest_fail(tmp_path):
    # Test asserts False · runner returns False
    ...
    assert run_pytest_for_changed(tmp_path, ["pkg/foo.py"]) is False

def test_run_pytest_no_test_file_returns_none(tmp_path):
    # foo.py exists · tests/test_foo.py does NOT · returns None (signal unavailable)
    ...
    assert run_pytest_for_changed(tmp_path, ["pkg/foo.py"]) is None

def test_run_pytest_timeout_returns_none(tmp_path):
    # Test sleeps 120s · timeout 5s · returns None (don't poison metric)
    ...

def test_run_pytest_multiple_files_any_fail(tmp_path):
    # 2 changed files · 1 test fails ⇒ overall False
    ...
```

**Step 2: Run · verify FAIL**

**Step 3: Implement** (~40 LOC):

```python
import subprocess
from pathlib import Path

def _resolve_test_paths(base: Path, applied_paths: list[str]) -> list[Path]:
    # Plan-phase decision #2: only <dir>/tests/test_<basename>.py
    test_paths = []
    for rel in applied_paths:
        p = (base / rel).resolve()
        candidate = p.parent / "tests" / f"test_{p.stem}.py"
        if candidate.exists():
            test_paths.append(candidate)
    return test_paths

def run_pytest_for_changed(base, applied_paths, timeout=60):
    tests = _resolve_test_paths(Path(base), applied_paths)
    if not tests: return None  # signal unavailable
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", "-q", "--no-header", *[str(t) for t in tests]],
            cwd=str(base), capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None  # don't bias metric on timeout
```

**Step 4: Run · verify PASS**

**Step 5: Commit**

```bash
git add phase3/backend/engine/pytest_runner.py phase3/backend/engine/tests/test_pytest_runner.py
git commit -m "feat(engine): pytest_runner · per-file test convention · timeout-safe"
```

**Day 3 deliverable / verification gate:**
- `pytest engine/tests/test_pytest_runner.py -v` ≥ 5 tests pass

---

## Day 4 · outcome_emit + ship.py hook

### Task 4.1: TDD `outcome_emit`

**Files:**
- Create: `phase3/backend/engine/outcome_emit.py`
- Create: `phase3/backend/engine/tests/test_outcome_emit.py`

**Step 1: Write failing tests** (~6 cases):

```python
def test_emit_db_success(monkeypatch, tmp_path):
    # Mock psycopg.connect · INSERT works · jsonl NOT written
    ...

def test_emit_db_fail_jsonl_fallback(monkeypatch, tmp_path):
    # psycopg raises · jsonl file appended · stderr warn
    ...

def test_emit_deadletter_table(monkeypatch):
    # row with status="deadletter" routed to engine_cycle_deadletter table
    ...

def test_emit_never_raises_on_total_failure(monkeypatch, tmp_path):
    # Both DB and jsonl write fail · function returns None · no exception
    ...

def test_emit_db_fail_also_writes_deadletter(monkeypatch):
    # DB INSERT fails · should also attempt deadletter row 'db_emit_failed'
    ...
```

**Step 2: Run · verify FAIL**

**Step 3: Implement** (~50 LOC):

```python
import json, os, sys
from pathlib import Path

JSONL_FALLBACK = Path(".engine-outcomes.jsonl")

def emit_outcome(row: dict, dsn: str | None = None) -> None:
    """Never raises. Returns None."""
    try:
        if row.get("ship_status") == "deadletter":
            _insert_deadletter(row, dsn)
        else:
            _insert_outcome(row, dsn)
        return
    except Exception as e:
        sys.stderr.write(f"[engine.outcome_emit] DB emit failed: {type(e).__name__}: {e}\n")

    # Fallback path
    try:
        with JSONL_FALLBACK.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception as e:
        sys.stderr.write(f"[engine.outcome_emit] jsonl fallback failed: {e}\n")

    try:
        _insert_deadletter({"cycle_id": row.get("cycle_id"),
                            "reason": "db_emit_failed",
                            "raw_error": str(e)[:4000]}, dsn)
    except Exception:
        pass  # best-effort · already in jsonl


def _insert_outcome(row, dsn): ...
def _insert_deadletter(row, dsn): ...
```

**Step 4: Run · verify PASS**

**Step 5: Commit**

```bash
git add phase3/backend/engine/outcome_emit.py phase3/backend/engine/tests/test_outcome_emit.py
git commit -m "feat(engine): outcome_emit · never-raise invariant · jsonl fallback"
```

### Task 4.2: Add hook to ship.py

**Files:**
- Modify: `phase3/backend/engine/ship.py` (insert `_emit_outcome` call before each `return ShipResult(...)`)
- Modify: `phase3/backend/engine/tests/test_ship.py` (verify emit called · mock outcome_emit)

**Step 1: Write integration test**

```python
def test_ship_emits_outcome(monkeypatch, ...):
    captured = []
    monkeypatch.setattr("engine.outcome_emit.emit_outcome", lambda r, dsn=None: captured.append(r))
    # ... run full ship with mock LLM that emits text_utils-like task
    result = ship(...)
    assert len(captured) == 1
    assert captured[0]["ship_status"] in ("success", "partial", "fail", "deadletter")
    assert "composite_score" in captured[0]
```

**Step 2: Run · verify FAIL** (hook doesn't exist)

**Step 3: Modify ship.py** (~20 LOC delta):

```python
# At top of ship():
import time
from engine.outcomes import classify, compute_composite, parse_spec_meta
from engine.pytest_runner import run_pytest_for_changed
from engine.outcome_emit import emit_outcome

def _build_outcome_row(result, task, base, cycle_id=None) -> dict:
    spec_meta = parse_spec_meta(task)
    semantic = _extract_semantic_pass(result.check_result)  # cycle 12 P1
    tests = run_pytest_for_changed(base, [b['path'] for b in result.files_planned]) if result.applied else None
    added, removed = _git_numstat(result.git_commit, base) if result.git_commit else (None, None)
    expected_total = (spec_meta["expected_added"] or 0) + (spec_meta["expected_removed"] or 0)
    drift = None
    if spec_meta["expected_added"] is not None and added is not None:
        drift = round((added + (removed or 0)) / max(1, expected_total), 3)
    status = classify(result, tests, drift)
    composite = compute_composite(semantic, tests, drift)
    return {
        "cycle_id": cycle_id or _auto_cycle_id(task),  # plan-phase decision #4
        "spec": task[:8000],
        "spec_expected_added": spec_meta["expected_added"],
        "spec_expected_removed": spec_meta["expected_removed"],
        "ship_status": status,
        "semantic_pass": semantic,
        "tests_pass": tests,
        "actual_lines_added": added,
        "actual_lines_removed": removed,
        "drift_ratio": drift,
        "composite_score": composite,
        "git_sha": result.git_commit,
        "cert_id": (result.audit or {}).get("cert_id"),
    }
```

Then insert `emit_outcome(_build_outcome_row(...))` before each `return ShipResult(...)` (3 sites).

**Step 4: Run all tests · verify 88 prior + new ones PASS**

```bash
cd phase3/backend && python -m pytest engine/tests/ -q
```

Expected: ≥ 96 + new D4 tests passed · 0 failed.

**Step 5: Commit**

```bash
git commit -am "feat(engine): ship.py · emit_outcome hook · 3 return sites"
```

### Task 4.3: Add `--cycle-id` CLI flag (plan-phase decision #5)

**Files:**
- Modify: `phase3/backend/engine/__main__.py`
- Modify: `phase3/cli/nautilus_cli/__main__.py` (`code` subcommand)

**Step 1-2: TDD** as above (test_main.py)

**Step 3: Implement** — argparse flag · pass through to `ship(..., cycle_id=args.cycle_id)`.

**Step 4: Verify** end-to-end:

```bash
cd phase3/backend && python -m engine "test task" --cycle-id "manual_smoke_2026-05-XX"
```

Expected: dry-run output · `cycle_id` appears in stdout / jsonl.

**Step 5: Commit**

**Day 4 deliverable / verification gate:**
- Full ship pipeline emits outcome row (verified by integration test + manual smoke)
- All 96+ engine tests pass · 0 fail
- jsonl fallback works when DB down

---

## Day 5 · Backfill 6 historical cycles

### Task 5.1: Write backfill script

**Files:**
- Create: `tools/backfill_engine_outcomes.py`
- Create: `tools/backfill_annotations.yaml` (manual spec_expected_added/removed for 6 cycles)

**Step 1: Annotate cycles** in `backfill_annotations.yaml`:

```yaml
cycles:
  - cycle_id: cycle_5_2026-05-XX
    git_sha: <lookup>
    spec_expected_added: <git show --stat>
    spec_expected_removed: <git show --stat>
    spec: <commit msg>
  # ... 5/5b/9/12P0/15/17(D1)
```

Use `git show --stat <sha>` to extract real added/removed for each commit · annotate.

**Step 2: Implement script**

```python
import yaml, subprocess
from engine.outcomes import compute_composite
from engine.outcome_emit import emit_outcome

def main():
    cfg = yaml.safe_load(open("tools/backfill_annotations.yaml"))
    for c in cfg["cycles"]:
        added, removed = c["actual_added"], c["actual_removed"]
        expected = c["spec_expected_added"] + c["spec_expected_removed"]
        drift = (added + removed) / max(1, expected)
        # Historical · no semantic_pass/tests_pass available · use None
        row = {
            "cycle_id": c["cycle_id"],
            "spec": c["spec"],
            "spec_expected_added": c["spec_expected_added"],
            "spec_expected_removed": c["spec_expected_removed"],
            "ship_status": "success",  # all 6 are historical successes
            "semantic_pass": None,
            "tests_pass": None,
            "drift_ratio": round(drift, 3),
            "composite_score": compute_composite(None, None, drift),
            "git_sha": c["git_sha"],
            ...
        }
        emit_outcome(row)
```

**Step 3: Run backfill**

```bash
python tools/backfill_engine_outcomes.py
```

**Step 4: Verify view**

```bash
psql $DATABASE_URL -c "SELECT * FROM v_engine_progress"
```

Expected: 1-6 rows · avg_composite is the **baseline** for 30-day "0.51 → 0.80" goal.

**Step 5: Document baseline** in `docs/plans/2026-05-25-engine-metric-loop-stage1-design.md` § 5.1 (append "baseline avg_composite = <value>"). Commit.

**Day 5 deliverable / verification gate:**
- `v_engine_progress` populated with 6 historical rows
- Real baseline documented in design doc (replaces "0.51 baseline" rumor)

---

## Day 6-7 · Stage 1 self-dogfood + bugfix

### Task 6.1: Compose self-dogfood spec

Spec target: add a small new feature to `outcomes.py` itself (e.g. `severity` field on deadletter rows · or `cycle_duration_ms` field on outcomes). Real spec to write in this step · ~30 LOC expected change.

**Spec-Meta:**
```
expected_added: 30
expected_removed: 0
```

### Task 6.2: Ship via PR #46 engine pipeline

**Steps:**
1. Checkout `engine-cycle-12-15-16-2026-05-25` (PR #46) into a worktree
2. From that worktree · `python -m engine "<spec>" --apply --cycle-id stage1_dogfood_self_2026-05-XX`
3. Verify cycle 15 file context injection picks up `outcomes.py` from repo_map
4. LLM produces minimal +30 LOC patch · semantic check pass · pytest pass
5. New outcome row written automatically

### Task 6.3: Verify

```bash
psql $DATABASE_URL -c "SELECT cycle_id, ship_status, composite_score, drift_ratio FROM engine_cycle_outcomes WHERE cycle_id LIKE 'stage1_dogfood%'"
```

Expected: status='success' · composite ≥ 0.85 · drift ≤ 1.2.

### Task 6.4-6.5: Bugfix + final commit

Document any issues found · fix · final regression run · push branch.

**Day 6-7 deliverable / verification gate:**
- Self-dogfood ship completes via PR #46 engine on Stage 1 code
- Outcome row auto-emitted · classified `success`
- Cycle 15 self-bootstrap pattern proven repeatable on Stage 1 components

---

## Risk Callouts

| Risk | Mitigation |
|---|---|
| `psycopg` not installed in engine env | Day 1 verify `python -c "import psycopg"` · install if missing · pin in `pyproject.toml` |
| Telemetry emit slows ship pipeline > 2s | Day 4 perf test · if slow · move emit to thread or fire-and-forget |
| `git numstat` returns 0/0 when commit had no changes | Treat as drift = 0 (matches spec_expected = 0) · not error |
| `pytest_runner` recursive pytest invocation (engine tests test engine) | Use `subprocess.run` with `cwd=base` · isolated process · no recursion |
| Spec without `Spec-Meta:` floods composite NULL after Day 5 backfill | Add Day 5 backfill annotation requires Spec-Meta-equivalent fields · all new cycles after Day 5 SHOULD include Spec-Meta (driver agent Stage 2 will enforce) |
| Cycle 12-16 (PR #46) not merged when Stage 1 lands | `semantic_pass` signal NULL until PR #46 merges · composite degrades to 2-signal (tests + drift) · acceptable until merge |

---

## Total estimate

| Day | LOC | Tests | Commits |
|---|---|---|---|
| Day 1 | 80 | 5 | 2 |
| Day 2 | 40 | 11 | 2 |
| Day 3 | 40 | 5 | 1 |
| Day 4 | 70 | 6 | 3 |
| Day 5 | 50 | 0 (script) | 1 |
| Day 6-7 | 40 (self-ship) | n/a | 2 |
| **Total** | **~320 LOC** | **~27 new** | **~11** |

---

## Approval

User must tick the 5 plan-phase decisions (or override) before Task 1.

After execution complete · plan transitions to Stage 2 (driver agent · separate plan).

— platform dialog · 2026-05-25

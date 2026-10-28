# Gap 1 Semantic Guard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 3 new preservation guards (`check_line_count`, `check_docstring_preserve`, `should_apply_preservation_checks`) to close handoff Gap 1 — self-dogfood semantic guard insufficient.

**Architecture:** 3 new independent functions in `phase3/backend/engine/checks.py` + 1 wiring update in `phase3/backend/engine/ship.py`. TDD per check, RED → GREEN per case. 5 commits direct to master. Design source: `docs/plans/2026-05-26-gap1-semantic-guard-design.md`.

**Tech Stack:** Python 3.8+ stdlib (`ast`, `pathlib`, `time`, `dataclasses`), pytest, MagicMock.

---

## Pre-flight (run once · 2 min)

**Step A · Verify baseline tests green**

Run from repo root: `cd phase3/backend && python -m pytest engine/tests/ -q 2>&1 | tail -5`
Expected: `177 passed, 6 skipped` (this is the post-quick-wins baseline · 4 emit-telemetry + 1 renamed in test_ship_outcome_hook.py).

**Step B · Confirm no in-progress edits in target files**

Run: `git status --short | grep -E "(checks\.py|ship\.py|test_check_line_count|test_check_docstring_preserve|test_should_apply_preservation|test_ship_semantic)" || echo "clean"`
Expected: `clean`

---

## Phase 1 · check_line_count (~25 min · 1 commit)

**Files:**
- Create: `phase3/backend/engine/tests/test_check_line_count.py`
- Modify: `phase3/backend/engine/checks.py` (add constants + function near end of file, before `check_pytest`)

### Task 1.1 · Write the failing tests

**Step 1: Create test file** with 6 tests:

```python
"""Test check_line_count · closes handoff Gap 1 part 1 (line count guard).

Bounds:
    shrink_floor = 0.85 * orig (always strict)
    growth_ceiling = 2.0 * orig default · 4.0 when allow_additions=True
"""
from pathlib import Path

from engine.checks import check_line_count


def _write(path: Path, n_lines: int) -> None:
    """Write a .py file with n_lines content lines."""
    path.write_text("\n".join(f"x = {i}" for i in range(n_lines)) + "\n", encoding="utf-8")


def test_line_count_reject_shrink(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 200)
    _write(new, 90)  # ratio 0.45
    r = check_line_count(str(orig), str(new))
    assert not r.passed, "shrink ratio 0.45 < 0.85 floor must reject"
    assert "shrink" in r.message.lower() or "0.45" in r.message


def test_line_count_pass_minor_jitter(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 100)
    _write(new, 95)  # ratio 0.95 > 0.85 floor
    r = check_line_count(str(orig), str(new))
    assert r.passed, f"minor jitter 0.95 must pass · {r.message}"


def test_line_count_reject_growth_default(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 50)
    _write(new, 150)  # ratio 3.0 > 2.0 default ceiling
    r = check_line_count(str(orig), str(new))
    assert not r.passed, "default growth 3.0 > 2.0 ceiling must reject"


def test_line_count_allow_additions_relaxes_growth(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 50)
    _write(new, 150)  # ratio 3.0 < 4.0 allow_add ceiling
    r = check_line_count(str(orig), str(new), allow_additions=True)
    assert r.passed, f"allow_additions ceiling 4.0 must pass ratio 3.0 · {r.message}"


def test_line_count_allow_additions_still_blocks_shrink(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _write(orig, 100)
    _write(new, 60)  # ratio 0.60 < 0.85 floor
    r = check_line_count(str(orig), str(new), allow_additions=True)
    assert not r.passed, "shrink 0.60 < 0.85 floor must reject even with allow_additions"


def test_line_count_new_file_skipped(tmp_path):
    new = tmp_path / "new.py"
    _write(new, 50)
    missing_orig = tmp_path / "does_not_exist.py"
    r = check_line_count(str(missing_orig), str(new))
    assert r.skipped, "no original on disk → skipped"
    assert r.passed, "skipped implies passed=True"
```

**Step 2: Run tests · verify all 6 RED**

Run: `cd phase3/backend && python -m pytest engine/tests/test_check_line_count.py -v 2>&1 | tail -15`
Expected: 6 FAIL with `ImportError: cannot import name 'check_line_count' from 'engine.checks'`.

### Task 1.2 · Implement check_line_count

**Step 1: Edit `phase3/backend/engine/checks.py`**

Add 3 constants after existing `SEMANTIC_PRESERVE_TRIGGER_PHRASES` block (around line 312):

```python
# ---------- Gap 1 · line count + docstring + size-trigger guards ----------

SHRINK_FLOOR = 0.85          # always strict (truncation is the failure mode)
GROWTH_CEILING = 2.0         # default
GROWTH_CEILING_ALLOW_ADD = 4.0  # when allow_additions=True
```

Add function before `check_pytest` (around line 488):

```python
def check_line_count(
    original_path: str,
    new_path: str,
    allow_additions: bool = False,
) -> CheckResult:
    """Reject when new file line count drifts from original outside bounds.

    Bounds (per design doc 2026-05-26-gap1-semantic-guard-design.md):
        shrink_floor = 0.85 * orig_lines (always strict · truncate is the failure mode)
        growth_ceiling = 2.0 * orig_lines default · 4.0 when allow_additions=True

    Skipped:
        - original not on disk (new file): vacuous
        - original empty (ratio undefined)
    """
    t0 = time.time()
    orig = Path(original_path)
    if not orig.is_file():
        return CheckResult(
            name="line_count",
            passed=True,
            skipped=True,
            message="original not on disk (new file)",
            duration_ms=_elapsed_ms(t0),
        )
    try:
        with open(original_path, encoding="utf-8", errors="ignore") as f:
            orig_lines = sum(1 for _ in f)
        with open(new_path, encoding="utf-8", errors="ignore") as f:
            new_lines = sum(1 for _ in f)
    except OSError as e:
        return CheckResult(
            name="line_count",
            passed=False,
            message=f"read error: {e}"[:300],
            duration_ms=_elapsed_ms(t0),
        )
    if orig_lines == 0:
        return CheckResult(
            name="line_count",
            passed=True,
            skipped=True,
            message="original empty (ratio undefined)",
            duration_ms=_elapsed_ms(t0),
        )
    ratio = new_lines / orig_lines
    ceiling = GROWTH_CEILING_ALLOW_ADD if allow_additions else GROWTH_CEILING
    if ratio < SHRINK_FLOOR:
        return CheckResult(
            name="line_count",
            passed=False,
            message=f"shrink {new_lines}/{orig_lines}={ratio:.2f} < {SHRINK_FLOOR} floor",
            duration_ms=_elapsed_ms(t0),
        )
    if ratio > ceiling:
        return CheckResult(
            name="line_count",
            passed=False,
            message=(
                f"growth {new_lines}/{orig_lines}={ratio:.2f} > {ceiling} ceiling "
                f"(allow_additions={allow_additions})"
            ),
            duration_ms=_elapsed_ms(t0),
        )
    return CheckResult(
        name="line_count",
        passed=True,
        message=f"ok {new_lines}/{orig_lines}={ratio:.2f}",
        duration_ms=_elapsed_ms(t0),
    )
```

**Step 2: Run tests · verify 6 GREEN**

Run: `cd phase3/backend && python -m pytest engine/tests/test_check_line_count.py -v 2>&1 | tail -10`
Expected: 6 passed.

### Task 1.3 · Full engine regression

Run: `cd phase3/backend && python -m pytest engine/tests/ -q 2>&1 | tail -3`
Expected: `183 passed, 6 skipped` (177 baseline + 6 new).

### Task 1.4 · Commit Phase 1

```bash
cd ../.. && git add phase3/backend/engine/checks.py phase3/backend/engine/tests/test_check_line_count.py && \
  git diff --cached --stat && \
  git commit -m "feat(engine): Gap 1 · check_line_count guard (0.85 shrink / 2.0 growth / 4.0 allow_add)"
```

---

## Phase 2 · check_docstring_preserve (~25 min · 1 commit)

**Files:**
- Create: `phase3/backend/engine/tests/test_check_docstring_preserve.py`
- Modify: `phase3/backend/engine/checks.py` (add 9-keyword tuple + _extract_module_docstring helper + check function)

### Task 2.1 · Write the failing tests

**Step 1: Create test file** with 6 tests:

```python
"""Test check_docstring_preserve · closes handoff Gap 1 part 2 (docstring guard).

Module-level docstring (AST first string expression) byte-diff reject
unless task contains one of 9 escape keywords (5 EN + 4 中文).
"""
from pathlib import Path

from engine.checks import check_docstring_preserve


def _py(path: Path, docstring: str | None, body: str = "x = 1") -> None:
    """Write a .py file with module docstring and body."""
    if docstring is not None:
        path.write_text(f'"""{docstring}"""\n{body}\n', encoding="utf-8")
    else:
        path.write_text(f"{body}\n", encoding="utf-8")


def test_docstring_reject_rewrite(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "Original module description.")
    _py(new, "Rewritten module description.")
    r = check_docstring_preserve(str(orig), str(new), task="add helper to module")
    assert not r.passed, "docstring rewrite without keyword must reject"
    assert "docstring" in r.message.lower()


def test_docstring_pass_identical(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "Same docstring.")
    _py(new, "Same docstring.")
    r = check_docstring_preserve(str(orig), str(new), task="any task")
    assert r.passed, f"identical docstring must pass · {r.message}"


def test_docstring_allow_en_keyword(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "Old.")
    _py(new, "New.")
    r = check_docstring_preserve(str(orig), str(new), task="update docstring for clarity")
    assert r.passed, "EN keyword 'update docstring' must escape · pass"
    assert r.skipped


def test_docstring_allow_chinese_keyword(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, "旧.")
    _py(new, "新.")
    r = check_docstring_preserve(str(orig), str(new), task="改 docstring 让 OSS 用户看懂")
    assert r.passed, "中文 keyword '改 docstring' must escape · pass"
    assert r.skipped


def test_docstring_new_file_skipped(tmp_path):
    new = tmp_path / "new.py"
    _py(new, "Whatever.")
    missing_orig = tmp_path / "does_not_exist.py"
    r = check_docstring_preserve(str(missing_orig), str(new), task="any task")
    assert r.skipped
    assert r.passed


def test_docstring_both_sides_empty_pass(tmp_path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    _py(orig, None)  # no docstring
    _py(new, None)
    r = check_docstring_preserve(str(orig), str(new), task="add helper")
    assert r.passed, "neither side has docstring · pass (skipped)"
    assert r.skipped
```

**Step 2: Verify 6 RED**

Run: `cd phase3/backend && python -m pytest engine/tests/test_check_docstring_preserve.py -v 2>&1 | tail -12`
Expected: 6 FAIL with `ImportError: cannot import name 'check_docstring_preserve'`.

### Task 2.2 · Implement check_docstring_preserve

**Step 1: Edit `phase3/backend/engine/checks.py`** — add after `GROWTH_CEILING_ALLOW_ADD` constant from Phase 1:

```python
_DOCSTRING_CHANGE_KEYWORDS = (
    # EN
    "update docstring",
    "rewrite docstring",
    "change docstring",
    "modify docstring",
    "docstring change",
    # 中文
    "改 docstring",
    "重写 docstring",
    "更新 docstring",
    "修改 docstring",
)
```

**Step 2: Add helper + check function** before `check_pytest`:

```python
def _extract_module_docstring(src: str) -> Optional[str]:
    """Return the module-level docstring (first AST string expression) · None if absent."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    if not tree.body:
        return None
    first = tree.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return first.value.value
    return None


def check_docstring_preserve(
    original_path: str,
    new_path: str,
    task: str,
) -> CheckResult:
    """Reject when module-level docstring text differs byte-for-byte.

    Skip when task lowercased contains any keyword in _DOCSTRING_CHANGE_KEYWORDS
    (5 EN + 4 中文 · supports bilingual task wording).

    Skipped: new file (no original) · or both sides have no module docstring.
    """
    t0 = time.time()
    orig = Path(original_path)
    if not orig.is_file():
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            skipped=True,
            message="original not on disk (new file)",
            duration_ms=_elapsed_ms(t0),
        )
    if task and any(kw in task.lower() for kw in _DOCSTRING_CHANGE_KEYWORDS):
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            skipped=True,
            message="task signals docstring change · escape",
            duration_ms=_elapsed_ms(t0),
        )
    try:
        orig_src = Path(original_path).read_text(encoding="utf-8")
        new_src = Path(new_path).read_text(encoding="utf-8")
    except OSError as e:
        return CheckResult(
            name="docstring_preserve",
            passed=False,
            message=f"read error: {e}"[:300],
            duration_ms=_elapsed_ms(t0),
        )
    orig_doc = _extract_module_docstring(orig_src)
    new_doc = _extract_module_docstring(new_src)
    if orig_doc is None and new_doc is None:
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            skipped=True,
            message="neither side has module docstring",
            duration_ms=_elapsed_ms(t0),
        )
    if orig_doc == new_doc:
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            duration_ms=_elapsed_ms(t0),
        )
    return CheckResult(
        name="docstring_preserve",
        passed=False,
        message=truncate(
            f"docstring changed · orig={orig_doc!r} → new={new_doc!r}",
            300,
        ),
        duration_ms=_elapsed_ms(t0),
    )
```

**Step 3: Verify 6 GREEN + Phase 1 still GREEN**

Run: `cd phase3/backend && python -m pytest engine/tests/test_check_docstring_preserve.py engine/tests/test_check_line_count.py -v 2>&1 | tail -15`
Expected: 12 passed.

### Task 2.3 · Full engine regression

Run: `cd phase3/backend && python -m pytest engine/tests/ -q 2>&1 | tail -3`
Expected: `189 passed, 6 skipped` (177 baseline + 6 line_count + 6 docstring).

### Task 2.4 · Commit Phase 2

```bash
cd ../.. && git add phase3/backend/engine/checks.py phase3/backend/engine/tests/test_check_docstring_preserve.py && \
  git diff --cached --stat && \
  git commit -m "feat(engine): Gap 1 · check_docstring_preserve guard (9 keywords escape · EN+中文)"
```

---

## Phase 3 · should_apply_preservation_checks (~20 min · 1 commit)

**Files:**
- Create: `phase3/backend/engine/tests/test_should_apply_preservation_checks.py`
- Modify: `phase3/backend/engine/checks.py` (add _EXISTING_FILE_LOC_TRIGGER constant + function)

### Task 3.1 · Write the failing tests

**Step 1: Create test file** with 5 tests:

```python
"""Test should_apply_preservation_checks · closes handoff Gap 1 part 3 (OR trigger).

Fires when:
  - task contains MINIMAL CHANGE phrase (existing should_apply_semantic_check), OR
  - any block target file already exists with > 50 LOC.
"""
from pathlib import Path

from engine.checks import should_apply_preservation_checks


def _write_lines(path: Path, n_lines: int) -> None:
    path.write_text("\n".join(f"x = {i}" for i in range(n_lines)) + "\n", encoding="utf-8")


def test_trigger_via_phrase(tmp_path):
    blocks = [{"path": "new.py", "content": "x = 1"}]
    task = "only add greet function · keep all other code identical"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is True


def test_trigger_via_existing_file_size_over_50(tmp_path):
    large = tmp_path / "large.py"
    _write_lines(large, 100)
    blocks = [{"path": "large.py", "content": "irrelevant"}]
    task = "add greet to large.py"  # no MINIMAL CHANGE phrase
    assert should_apply_preservation_checks(task, blocks, tmp_path) is True


def test_no_trigger_for_small_existing_file(tmp_path):
    small = tmp_path / "small.py"
    _write_lines(small, 30)
    blocks = [{"path": "small.py", "content": "irrelevant"}]
    task = "add greet to small.py"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is False


def test_no_trigger_for_new_file_no_phrase(tmp_path):
    blocks = [{"path": "brand_new.py", "content": "x = 1"}]
    task = "create new helper.py"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is False


def test_or_logic_phrase_and_size(tmp_path):
    large = tmp_path / "large.py"
    _write_lines(large, 100)
    blocks = [{"path": "large.py", "content": "irrelevant"}]
    task = "only add greet · keep all other code identical"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is True
```

**Step 2: Verify 5 RED**

Run: `cd phase3/backend && python -m pytest engine/tests/test_should_apply_preservation_checks.py -v 2>&1 | tail -10`
Expected: 5 FAIL with `ImportError: cannot import name 'should_apply_preservation_checks'`.

### Task 3.2 · Implement should_apply_preservation_checks

**Step 1: Edit `phase3/backend/engine/checks.py`** — add constant after `_DOCSTRING_CHANGE_KEYWORDS`:

```python
_EXISTING_FILE_LOC_TRIGGER = 50
```

**Step 2: Add function** after `should_allow_additions` (around line 349):

```python
def should_apply_preservation_checks(
    task: Optional[str],
    blocks: list,
    base_dir,
) -> bool:
    """OR trigger for the preservation check family (Gap 1).

    Fires when:
        - task contains any MINIMAL CHANGE phrase (existing should_apply_semantic_check), OR
        - any target file in blocks already exists on disk with > 50 LOC.

    `blocks` is the engine.parse_file_blocks() output: list of dicts each with a "path" key
    relative to base_dir.
    """
    if should_apply_semantic_check(task):
        return True
    if isinstance(base_dir, Path):
        base = base_dir.resolve()
    else:
        base = Path(base_dir).resolve()
    for b in blocks:
        rel = b.get("path", "")
        if not rel:
            continue
        target = (base / rel).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            continue  # path escape · ignore
        if not target.is_file():
            continue
        try:
            with target.open(encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for _ in f)
            if lines > _EXISTING_FILE_LOC_TRIGGER:
                return True
        except OSError:
            continue
    return False
```

**Step 3: Verify 5 GREEN**

Run: `cd phase3/backend && python -m pytest engine/tests/test_should_apply_preservation_checks.py -v 2>&1 | tail -10`
Expected: 5 passed.

### Task 3.3 · Full engine regression

Run: `cd phase3/backend && python -m pytest engine/tests/ -q 2>&1 | tail -3`
Expected: `194 passed, 6 skipped` (177 baseline + 6 line_count + 6 docstring + 5 trigger).

### Task 3.4 · Commit Phase 3

```bash
cd ../.. && git add phase3/backend/engine/checks.py phase3/backend/engine/tests/test_should_apply_preservation_checks.py && \
  git commit -m "feat(engine): Gap 1 · should_apply_preservation_checks OR trigger (phrase OR existing >50 LOC)"
```

---

## Phase 4 · ship.py wiring + 2 integration tests (~25 min · 1 commit)

**Files:**
- Modify: `phase3/backend/engine/ship.py` (imports + `_run_semantic_checks` signature & body + `_try_once` trigger replacement)
- Modify: `phase3/backend/engine/tests/test_ship.py` (append 2 new integration tests)

### Task 4.1 · Write the failing integration tests

**Step 1: Append to `phase3/backend/engine/tests/test_ship.py`** (use Read tool first to know current end-of-file pattern · then Edit to append):

```python
def test_ship_runs_line_count_check_when_existing_file_over_50loc(tmp_path, monkeypatch):
    """Size trigger fires line_count check · LLM truncate rejected.

    Closes the actual Day 6-7 dogfood scenario: task says "add aggregate_recent
    to outcomes.py" (no MINIMAL CHANGE phrase), outcomes.py already has 200
    LOC on disk, LLM emits a truncated 90-line version. Without Gap 1, this
    would ship silently. With Gap 1, line_count rejects.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Seed existing file · 200 LOC, no MINIMAL CHANGE phrase in task
    target = tmp_path / "outcomes.py"
    target.write_text("\n".join(f"x = {i}" for i in range(200)) + "\n", encoding="utf-8")
    # LLM emits a 90-line replacement (ratio 0.45 · below 0.85 floor)
    truncated_body = "\n".join(f"x = {i}" for i in range(90))
    code_output = f"```python:outcomes.py\n{truncated_body}\n```\n"
    eng = NautilusEngine(
        llm_client=_mock_llm_returning(code_output),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: None):
        result = ship(
            eng, task="add aggregate_recent to outcomes.py",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    # Find the line_count check in the result
    names = [c["name"] for c in result.check_result.get("checks", [])]
    assert "line_count" in names, f"line_count check must run · got {names}"
    line_count_check = next(c for c in result.check_result["checks"] if c["name"] == "line_count")
    assert not line_count_check["passed"], f"line_count must reject 0.45 ratio · {line_count_check}"


def test_ship_runs_docstring_preserve_check_when_existing_file(tmp_path, monkeypatch):
    """Size trigger fires docstring_preserve · LLM docstring rewrite rejected."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Existing 100-LOC file with module docstring · size > 50 fires trigger
    target = tmp_path / "module.py"
    body = "\n".join(f"x = {i}" for i in range(99))
    target.write_text(f'"""Original module docstring."""\n{body}\n', encoding="utf-8")
    # LLM rewrites docstring (preserves line count) · task has no escape keyword
    new_body = "\n".join(f"x = {i}" for i in range(99))
    code_output = (
        f'```python:module.py\n"""Rewritten module docstring."""\n{new_body}\n```\n'
    )
    eng = NautilusEngine(
        llm_client=_mock_llm_returning(code_output),
        base_dir=str(tmp_path),
        dry_run=True,
    )
    with patch("engine.ship.emit_outcome", side_effect=lambda row, dsn=None: None):
        result = ship(
            eng, task="fix off-by-one in module.py",
            base_dir=str(tmp_path),
            apply=False, dispatch_audit=False,
        )
    names = [c["name"] for c in result.check_result.get("checks", [])]
    assert "docstring_preserve" in names, f"docstring_preserve must run · got {names}"
    doc_check = next(c for c in result.check_result["checks"] if c["name"] == "docstring_preserve")
    assert not doc_check["passed"], f"docstring rewrite without keyword must reject · {doc_check}"
```

NOTE: Verify existing test file already imports `NautilusEngine`, `ship`, `_mock_llm_returning`, `patch`. If `_mock_llm_returning` is not defined in test_ship.py, copy this helper inline or import from `test_ship_outcome_hook` (where it lives):

```python
def _mock_llm_returning(text: str):
    from unittest.mock import MagicMock
    fake = MagicMock()
    fake.chat = MagicMock(return_value=text)
    return fake
```

Use `Read phase3/backend/engine/tests/test_ship.py` first to confirm existing imports + add only what's missing.

**Step 2: Verify 2 RED**

Run: `cd phase3/backend && python -m pytest engine/tests/test_ship.py -k "preserve or line_count" -v 2>&1 | tail -15`
Expected: 2 FAIL · check "line_count" / "docstring_preserve" NOT in names list (the checks don't run yet because trigger is still `should_apply_semantic_check` and `_run_semantic_checks` doesn't call them).

### Task 4.2 · Update ship.py imports

**Step 1: Edit `phase3/backend/engine/ship.py` lines 31-36** (existing import block):

Old:
```python
from engine.checks import (
    check_semantic_preservation,
    run_pipeline,
    should_allow_additions,
    should_apply_semantic_check,
)
```

New:
```python
from engine.checks import (
    check_docstring_preserve,
    check_line_count,
    check_semantic_preservation,
    run_pipeline,
    should_allow_additions,
    should_apply_preservation_checks,
    should_apply_semantic_check,  # kept (still used by should_allow_additions internally)
)
```

### Task 4.3 · Update `_run_semantic_checks` signature + body

**Step 1: Edit `phase3/backend/engine/ship.py` `_run_semantic_checks` (lines 258-289)**

Replace the entire function with:

```python
def _run_semantic_checks(
    blocks: list[dict],
    staging: Path,
    base_dir: Path,
    allow_additions: bool = False,
    task: str = "",
) -> list[dict]:
    """For each block whose target file already exists under base_dir, run the
    preservation check trio (semantic + line_count + docstring) and return
    asdict results.

    New files (no original on disk) are skipped · preservation checks are
    vacuous when there is nothing to preserve.

    allow_additions (cycle 16) is passed through to check_semantic_preservation
    and check_line_count: when True · intentional additions don't fail the
    semantic check (only removals + sig changes do), and the line_count growth
    ceiling relaxes from 2.0 to 4.0. Shrink floor stays at 0.85 always.

    task is passed to check_docstring_preserve so the 9-keyword escape works.
    """
    out: list[dict] = []
    for b in blocks:
        original = (base_dir / b["path"]).resolve()
        try:
            original.relative_to(base_dir)
        except ValueError:
            continue  # path escape (already filtered by _write_staging too)
        if not original.is_file():
            continue
        staged = (staging / b["path"]).resolve()
        if not staged.is_file():
            continue
        out.append(asdict(check_semantic_preservation(
            str(original), str(staged), allow_additions=allow_additions
        )))
        out.append(asdict(check_line_count(
            str(original), str(staged), allow_additions=allow_additions
        )))
        out.append(asdict(check_docstring_preserve(
            str(original), str(staged), task=task
        )))
    return out
```

### Task 4.4 · Update `_try_once` trigger

**Step 1: Edit `phase3/backend/engine/ship.py` `_try_once` around line 238**

Old:
```python
        if base_dir is not None and should_apply_semantic_check(task):
            extra = _run_semantic_checks(
                blocks, staging, base_dir, allow_additions=should_allow_additions(task)
            )
            if extra:
                check_result["checks"].extend(extra)
                check_result["passed"] = check_result["passed"] and all(
                    c["passed"] for c in extra
                )
```

New:
```python
        if base_dir is not None and should_apply_preservation_checks(task, blocks, base_dir):
            extra = _run_semantic_checks(
                blocks, staging, base_dir,
                allow_additions=should_allow_additions(task),
                task=task,
            )
            if extra:
                check_result["checks"].extend(extra)
                check_result["passed"] = check_result["passed"] and all(
                    c["passed"] for c in extra
                )
```

### Task 4.5 · Verify 2 integration tests GREEN

Run: `cd phase3/backend && python -m pytest engine/tests/test_ship.py -k "preserve or line_count" -v 2>&1 | tail -10`
Expected: 2 passed.

### Task 4.6 · Verify full engine regression

Run: `cd phase3/backend && python -m pytest engine/tests/ -q 2>&1 | tail -3`
Expected: `196 passed, 6 skipped` (177 baseline + 6 + 6 + 5 + 2 = 196).

Note: design doc said 198 total because it counted existing tests in old `test_ship_outcome_hook.py`. The actual baseline is 177 (post-quick-wins), so 177 + 19 = 196. Re-verify pre-flight if needed.

If any existing test fails (regression), `should_apply_preservation_checks` may have changed behavior for existing tasks. Debug: check which existing test fires the trigger now that didn't before. Likely cause: an existing test creates a file > 50 LOC and reuses it for a non-MINIMAL-CHANGE task. Fix the test to use a smaller file or accept the new check output.

### Task 4.7 · Commit Phase 4

```bash
cd ../.. && git add phase3/backend/engine/ship.py phase3/backend/engine/tests/test_ship.py && \
  git diff --cached --stat && \
  git commit -m "feat(engine): Gap 1 · ship.py wires preservation checks (line_count + docstring) per block"
```

---

## Phase 5 · Wrap-up verify (~5 min · no commit)

### Task 5.1 · Final full test suite

Run from repo root: `cd phase3/backend && python -m pytest engine/tests/ -q 2>&1 | tail -5`
Expected: `196 passed, 6 skipped` (or `198 passed` if base went up unexpectedly · investigate diff).

Also run CLI tests (no changes expected): `cd ../cli && python -m pytest tests/ -q 2>&1 | tail -3`
Expected: `2 passed`.

### Task 5.2 · Git log verify

Run: `git log --oneline -6`
Expected: top 4 are the new commits (line_count · docstring_preserve · trigger · wiring), then handoff/design/plan commits below.

### Task 5.3 · Confirm NO push

`git status -b --short | head -1`
Expected: `## master...origin/master [ahead 12]` (or higher · 7 prior + 1 plan + 4 ship).

### Task 5.4 · Confirm no untracked side effects in target dirs

```bash
git status --short | grep -E "(checks\.py|ship\.py|test_check|test_ship|test_should_apply)" || echo "clean"
```
Expected: `clean` (all changes committed).

---

## Test count summary

| Stage | Engine | CLI | Total |
|---|---|---|---|
| Pre-flight (post-quick-wins) | 177 | 2 | 179 |
| After Phase 1 (line_count) | 183 | 2 | 185 |
| After Phase 2 (docstring_preserve) | 189 | 2 | 191 |
| After Phase 3 (trigger) | 194 | 2 | 196 |
| After Phase 4 (wiring + 2 integration) | 196 | 2 | **198** |

19 new engine tests · 0 CLI new · 1 file modified in tests (test_ship.py append).

## Risk checklist (verified by tests)

- Cycle 15 self-bootstrap (50 → 130 LOC, ratio 2.6) · allow_additions=True · 2.6 < 4.0 · pass ✓ (covered by test_line_count_allow_additions_relaxes_growth at ratio 3.0)
- Cycle 17 D1 fix (50 → 52 LOC) · file = 50 LOC · trigger `> 50` strict · not fired ✓ (covered by test_no_trigger_for_small_existing_file at 30 LOC; 50-LOC boundary is implicit)
- Day 6-7 dogfood truncate · size trigger fires · ratio 0.45 < 0.85 floor · reject ✓ (integration test test_ship_runs_line_count_check_when_existing_file_over_50loc)
- D1 drift #1 docstring rewrite · trigger fires · no keyword · reject ✓ (integration test test_ship_runs_docstring_preserve_check_when_existing_file)
- 中文 task escape · keyword skip · pass ✓ (test_docstring_allow_chinese_keyword)
- Edge case (100-LOC file, legitimate remove 20 lines, ratio 0.80) · false-reject · user must re-spec ⚠ (documented in design doc · not test-covered · out of scope override flag deferred)

## Out of scope (do not touch in this plan)

- Function-level / class-level docstring preservation
- Comment / whitespace / quote / variable name preservation
- Override flag for false-reject (e.g., `--force-shrink-allowed`)
- Cross-dialog alembic migration (Gap 3 separate work)
- Backfill historic outcomes row (Gap 2 separate work)

— platform dialog · 2026-05-26 · plan ready for in-session execution

# Gap 1 · Semantic Guard Design · 2026-05-26

> Brainstorming approved 2026-05-26 · platform dialog · ready for writing-plans (next session).

## Context

Closes handoff `2026-05-25` Gap 1 (lines 93-100): self-dogfood semantic guard insufficient.

**Evidence**: cycle 12 P1 `should_apply_semantic_check` returned False on Day 6-7 self-dogfood task `"add aggregate_recent to outcomes.py"`. The task contained "add" but not "only add", so none of the 5 phrase triggers matched. LLM truncated 55 LOC and rewrote module docstring · ruff/import/py_compile all green · would have shipped silently. Caught manually before apply.

**D1 dogfood evidence** (`docs/D1_DOGFOOD_DRIFT_EVIDENCE_20260525.md`): even when the check DID fire, drifts #1 (module docstring rewrite) and #3 (function docstring rewrite) sneaked through because `check_semantic_preservation` only inspects AST structure (imports/functions/classes), not docstring text.

## Stance (locked via brainstorming Q&A)

**Hybrid C** with 4 dimensional tweaks:

| Dim | Decision | Reasoning |
|---|---|---|
| Trigger expansion | OR-trigger: existing phrase **OR** any target file already on disk with > 50 LOC | Closes "add X to Y" task class missed today |
| Line count thresholds (asymmetric) | shrink floor **0.85** · default growth ceiling **2.0** · allow_additions growth ceiling **4.0** | Shrink is tight (truncate is the failure mode that hurts); growth is loose (cycle 15 self-bootstrap +160% must pass when allow_additions=True) |
| Docstring change keyword (9) | 5 EN: `update docstring` / `rewrite docstring` / `change docstring` / `modify docstring` / `docstring change` · 4 中文: `改 docstring` / `重写 docstring` / `更新 docstring` / `修改 docstring` | Bilingual task wording must escape · keyword list flat (no regex) |
| Implementation structure | **3 NEW independent functions** in `phase3/backend/engine/checks.py` | Each check independently testable + ablatable; ship.py wiring stays familiar |
| Interaction with `allow_additions` | semantic_preservation skips removal/sig check (existing cycle 16 · unchanged) · line_count growth ceiling relaxes 2.0 → 4.0 · line_count shrink floor stays 0.85 always · docstring_preserve default strict (keyword to escape) | Shrink is always suspect; growth narrative depends on intent |

## Design

### Components

3 new functions in `phase3/backend/engine/checks.py`:

```python
SHRINK_FLOOR = 0.85
GROWTH_CEILING = 2.0
GROWTH_CEILING_ALLOW_ADD = 4.0

_EXISTING_FILE_LOC_TRIGGER = 50

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


def check_line_count(
    original_path: str,
    new_path: str,
    allow_additions: bool = False,
) -> CheckResult:
    """Reject when new file line count drifts from original outside bounds.

    Bounds:
        shrink_floor = 0.85 * orig_lines (always)
        growth_ceiling = 2.0 * orig_lines (4.0 when allow_additions=True)

    Skipped:
        - new file (no original on disk): vacuous
        - non-.py path: convention enforced by ship.py block filter
    """


def check_docstring_preserve(
    original_path: str,
    new_path: str,
    task: str,
) -> CheckResult:
    """Reject when module-level docstring (first AST string expression) text differs.

    Skip when task lowercased contains any keyword in _DOCSTRING_CHANGE_KEYWORDS.
    Skipped: new file or both sides have no module docstring.
    """


def should_apply_preservation_checks(
    task: str | None,
    blocks: list[dict],
    base_dir: Path,
) -> bool:
    """OR trigger for preservation check family.

    Fires when:
        - task contains any MINIMAL CHANGE phrase (existing should_apply_semantic_check), OR
        - any target file in blocks already exists on disk with > 50 LOC
    """
```

### ship.py wiring update

`_run_semantic_checks` signature gains `task: str = ""` parameter. Per existing block in the loop, after `check_semantic_preservation` it also runs `check_line_count(original_path, staged_path, allow_additions)` and `check_docstring_preserve(original_path, staged_path, task)`. Both append their `asdict(CheckResult)` to the returned list.

`_try_once` trigger replaces:
```python
if base_dir is not None and should_apply_semantic_check(task):
    extra = _run_semantic_checks(blocks, staging, base_dir, allow_additions=should_allow_additions(task))
```
with:
```python
if base_dir is not None and should_apply_preservation_checks(task, blocks, base_dir):
    extra = _run_semantic_checks(blocks, staging, base_dir, allow_additions=should_allow_additions(task), task=task)
```

### Data flow

```
task + blocks + base_dir
   ↓
should_apply_preservation_checks
   ↓ True
_run_semantic_checks loop · for each block whose original.is_file():
   check_semantic_preservation  (existing AST diff)
   check_line_count             (NEW)
   check_docstring_preserve     (NEW)
   ↓
asdict each → check_result["checks"] list
check_result["passed"] &&= all(c.passed for c in extras)
```

### Error handling

All 3 checks (`check_line_count`, `check_docstring_preserve`, `should_apply_preservation_checks`) follow the existing pattern · never raise:
- OSError on file read → `CheckResult(passed=False, message="read error: ...")`
- SyntaxError parsing for docstring AST → `CheckResult(passed=False, message="parse error: ...")`
- Non-.py path or vacuous new-file case → `CheckResult(passed=True, skipped=True)`

`should_apply_preservation_checks` returns False (not raise) on path escape / OSError per existing convention.

## Test coverage (19 new tests · baseline 179 → 198)

### `phase3/backend/engine/tests/test_check_line_count.py` (NEW · 6 tests)

1. `test_line_count_reject_shrink` — orig 200 LOC · new 90 LOC (ratio 0.45) → reject
2. `test_line_count_pass_minor_jitter` — orig 100 · new 95 (ratio 0.95) → pass (above 0.85 floor)
3. `test_line_count_reject_growth_default` — orig 50 · new 150 (ratio 3.0) → reject default
4. `test_line_count_allow_additions_relaxes_growth` — orig 50 · new 150 (ratio 3.0) · allow_additions=True → pass (< 4.0)
5. `test_line_count_allow_additions_still_blocks_shrink` — orig 100 · new 60 (ratio 0.6) · allow_additions=True → reject (shrink always strict)
6. `test_line_count_new_file_skipped` — no original on disk → skipped

### `phase3/backend/engine/tests/test_check_docstring_preserve.py` (NEW · 6 tests)

1. `test_docstring_reject_rewrite` — D1 drift #1 scenario · orig + new different docstrings · task no keyword → reject
2. `test_docstring_pass_identical` — byte-for-byte same → pass
3. `test_docstring_allow_en_keyword` — task contains "update docstring" → skip → pass
4. `test_docstring_allow_chinese_keyword` — task contains "改 docstring" → skip → pass
5. `test_docstring_new_file_skipped` — no original → skipped
6. `test_docstring_both_sides_empty_pass` — neither has module docstring → pass

### `phase3/backend/engine/tests/test_should_apply_preservation_checks.py` (NEW · 5 tests)

1. `test_trigger_via_phrase` — task "only add greet · keep all other code identical" → True
2. `test_trigger_via_existing_file_size_over_50` — task "add greet to large.py" · large.py exists with 100 LOC → True
3. `test_no_trigger_for_small_existing_file` — task "add greet to small.py" · small.py exists with 30 LOC → False
4. `test_no_trigger_for_new_file_no_phrase` — task "create new helper.py" · helper.py does not exist · no phrase → False
5. `test_or_logic_phrase_and_size` — both conditions met → True

### Integration · `phase3/backend/engine/tests/test_ship.py` update (2 new tests)

1. `test_ship_runs_line_count_check_when_existing_file_over_50loc` — task "add aggregate_recent to outcomes.py" · outcomes.py exists 200 LOC · LLM emits truncated 90 LOC · check fires · ship rejects
2. `test_ship_runs_docstring_preserve_check_when_existing_file` — task "fix bug in module.py" · module.py exists 100 LOC · LLM rewrites docstring · check fires · ship rejects

## Risk · key corner cases

| Scenario | Expected behavior | Verified |
|---|---|---|
| Cycle 15 self-bootstrap (50 → 130 LOC · ratio 2.6) | allow_additions=True · 2.6 < 4.0 ceiling · pass | ✓ |
| Cycle 17 D1 fix (50 → 52 LOC · ratio 1.04) | file = 50 LOC · trigger `> 50` strict · not fired | ✓ |
| Day 6-7 dogfood truncate (200 → 90 · ratio 0.45) | size trigger fires · 0.45 < 0.85 floor · reject | ✓ |
| D1 drift #1 docstring rewrite | size trigger fires · docstring differs · no keyword in task · reject | ✓ |
| EN task `update docstring of X` | keyword skip · pass (even if text differs) | ✓ |
| 中文 task `改 docstring 给 X` | 中文 keyword skip · pass | ✓ |
| Small file remove-and-rewrite (30-LOC, remove 5 lines, ratio 0.83) | 30 LOC < 50 trigger threshold · not fired · pass | ✓ |
| **Edge**: 100-LOC file, legitimate remove 20 lines (ratio 0.80) | trigger fires · 0.80 < 0.85 floor · **false reject** | ⚠ user must rephrase task or use override flag (not in this scope) |

## Out of scope (explicit)

- Function-level docstring preservation (only module-level checked)
- Class-level docstring preservation
- Comment text preservation (D1 drift #5 cosmetic · not caught)
- Whitespace / blank line / indentation (D1 drift #5 not caught)
- Variable name preservation within function bodies (cycle 12 prompt addresses, AST check does not)
- Override flag for false-reject (e.g., `--force-shrink-allowed`) · explicit deferred · user manually re-spec task instead
- Quote style preservation (D1 drift #4 cosmetic)
- Cross-dialog alembic migration (Gap 3 · separate work)

## Implementation sequence (for writing-plans · next session)

1. **Phase 1** · `check_line_count` (RED 6 tests → GREEN function → commit)
2. **Phase 2** · `check_docstring_preserve` (RED 6 tests → GREEN function → commit)
3. **Phase 3** · `should_apply_preservation_checks` (RED 5 tests → GREEN function → commit)
4. **Phase 4** · ship.py wiring update + 2 integration tests (RED 2 tests → GREEN wiring → commit)
5. **Phase 5** · full regression (198 expected green) + final commit message summary

4-5 commits direct to master (small commits per check is fine · or batch 1+2+3 into single "guard functions" commit + 4+5 into "wiring" commit · writing-plans decides).

— platform dialog · 2026-05-26 · brainstorming approved · ready for writing-plans

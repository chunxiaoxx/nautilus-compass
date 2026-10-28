# Phase 3 Expert Form CLI Recovery Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Recover only the public Phase 3 expert-information Form through a
fail-closed Feishu CLI, without reading Bitable records or touching the task
Form.

**Architecture:** Extend the existing `FormPublisher` with expert-only probe
and reconfiguration methods that resolve one fixed configuration. Add a
dedicated CLI with no task-Form selector. It reuses the existing Form API
adapter and protected credential loader while emitting sanitized metadata.

**Tech Stack:** Python 3.13, pytest, existing Feishu Bitable/Form API adapter.

---

### Task 1: Add failing expert-only publisher tests

**Files:**
- Modify: `phase3/backend/tests/test_fde_phase3_single_submission_forms.py`

**Step 1: Write a failing probe test**

Call the new expert-only probe API through `FakeFormClient`. Assert that it
returns only the Form name, publication settings, and total/visible question
counts. Assert its client calls have no task table ID and no `/records` path.

**Step 2: Run the focused test**

Run:

```powershell
python -m pytest tests/test_fde_phase3_single_submission_forms.py -q -k expert_form_probe
```

Expected: FAIL because the expert-only probe does not exist.

**Step 3: Write a failing refresh test**

Make the expert Form public and one expert question stale. Call the new
expert-only refresh method. Assert call order is private -> question patch ->
public, with no task-table or record calls. Add a separate missing-confirmation
test that performs no PATCH.

**Step 4: Run the focused test**

Run:

```powershell
python -m pytest tests/test_fde_phase3_single_submission_forms.py -q -k expert_form_refresh
```

Expected: FAIL because the method does not exist.

### Task 2: Implement the scoped publisher capability

**Files:**
- Modify: `phase3/backend/services/fde_phase3_single_submission_forms.py`

**Step 1: Add a sanitized immutable probe result**

Add a dataclass containing exactly `form_name`, `shared`, `shared_limit`,
`submit_limit_once`, `question_count`, and `visible_question_count`. It must
not include URLs, IDs, field names, or record values.

**Step 2: Add a fixed expert-configuration resolver**

Select the sole configuration for `第三期专家`, then resolve only its table
metadata, fields, Form view, Form metadata, and Form questions. It must not
call the full two-Form `plan()` or `_published_forms()` paths.

**Step 3: Implement probe and refresh**

The probe returns the sanitized result. The refresh requires `confirmed=True`,
unshares only the expert Form, verifies it is private, patches only differing
expert questions, validates the expert field contract, republishes with the
approved public metadata, and verifies the result. A failure after the pause
leaves the Form private.

**Step 4: Run focused tests**

Run:

```powershell
python -m pytest tests/test_fde_phase3_single_submission_forms.py -q -k "expert_form_probe or expert_form_refresh"
```

Expected: PASS.

### Task 3: Add the dedicated no-record CLI

**Files:**
- Create: `phase3/backend/scripts/refresh_phase3_expert_form.py`
- Modify: `phase3/backend/tests/test_fde_phase3_single_submission_forms.py`

**Step 1: Write failing CLI tests**

Assert that `--help` exposes only `--probe`, `--apply`, `--confirm`, Base
token, and secret-file controls; it has no task target, record, or
legacy-retirement option. Assert apply requires exactly
`FDE_PHASE3_EXPERT_FORM_REFRESH`, the output is sanitized, and adapter calls
contain no `/records` endpoint.

**Step 2: Run the focused test**

Run:

```powershell
python -m pytest tests/test_fde_phase3_single_submission_forms.py -q -k expert_form_cli
```

Expected: FAIL because the script does not exist.

**Step 3: Implement the CLI**

Reuse the canonical publisher's protected credential loader and Form API
adapter. Default to `--probe`; require `--apply --confirm
FDE_PHASE3_EXPERT_FORM_REFRESH` for refresh. Do not add a task target option.

**Step 4: Run all Form tests and static checks**

Run:

```powershell
python -m pytest tests/test_fde_phase3_single_submission_forms.py -q -p no:cacheprovider
python -m py_compile services/fde_phase3_single_submission_forms.py scripts/refresh_phase3_expert_form.py
ruff check --ignore E402 services/fde_phase3_single_submission_forms.py scripts/refresh_phase3_expert_form.py tests/test_fde_phase3_single_submission_forms.py
git diff --check
```

Expected: all commands succeed.

### Task 4: Perform authorized expert-only operational validation

**Files:**
- No source changes expected.

**Step 1: Run a live read-only probe**

Run the dedicated CLI with the configured Base token and `--probe`. Inspect
only its sanitized result. Stop if the expert Form identity or field contract
does not match.

**Step 2: Run the authorized refresh and re-probe**

Run the dedicated CLI with `--apply --confirm
FDE_PHASE3_EXPERT_FORM_REFRESH`, then run `--probe` again. It may temporarily
make only the expert Form private. It must not inspect any task, review,
export, or record data.

**Step 3: Commit implementation**

```powershell
git add phase3/backend/services/fde_phase3_single_submission_forms.py phase3/backend/scripts/refresh_phase3_expert_form.py phase3/backend/tests/test_fde_phase3_single_submission_forms.py docs/plans/2026-07-23-phase3-expert-form-cli-recovery-plan.md
git commit -m "feat(fde): add expert form recovery cli"
```

Do not push or merge. The separate task-table maintenance command remains
blocked pending its own explicit maintenance-window authorization.

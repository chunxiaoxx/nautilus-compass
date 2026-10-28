# Phase 3 Native Form Publication Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Make the expert-information Form genuinely available to external
experts through Feishu's native Form-sharing flow and establish an evidence
standard that distinguishes UI accessibility from API metadata.

**Architecture:** The authenticated Base owner configures the native Form-share
dialog through controlled UI interaction. Existing CLI tools remain metadata
probes only. An anonymous browser acceptance check is the release gate. The
task Form and all post-submit automation remain separate gates.

**Tech Stack:** Feishu native Base/Form UI, controlled browser interaction,
existing Phase 3 Python CLI, pytest.

---

### Task 1: Guard the CLI against false publication claims

**Files:**
- Modify: `phase3/backend/scripts/refresh_phase3_expert_form.py`
- Modify: `phase3/backend/tests/test_fde_phase3_single_submission_forms.py`
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Write a failing test**

Assert the expert Form CLI labels its result as `metadata_probe` or
`metadata_refresh`, never as `published` or externally available. The test must
also assert its help text says native Form sharing remains subject to browser
acceptance.

**Step 2: Run the focused test**

Run:

```powershell
python -m pytest tests/test_fde_phase3_single_submission_forms.py -q -k expert_form_cli
```

Expected: FAIL because the current wording can be misread as publication proof.

**Step 3: Implement the narrow wording and registry correction**

Keep the metadata endpoint available for incident recovery, but label it as a
metadata operation. Change the asset registry's Form status to
`native_share_unverified` until the browser acceptance gate passes. Do not add
public links, credentials, IDs, or record data.

**Step 4: Run the focused test**

Run the same command. Expected: PASS.

### Task 2: Configure the expert Form using the native Feishu share dialog

**Files:**
- No repository source changes expected.

**Step 1: Preflight the authenticated owner session**

Open the current Phase 3 Base in the authenticated owner browser. Confirm the
target table is `第三期专家` and the target view is
`第三期专家信息采集（正式）`. Do not open a legacy Form.

**Step 2: Use native Form sharing**

In the Form view, open the native share dialog, turn sharing off and on if
needed, select the external scope equivalent to "internet users with the link
can fill", and ensure the action does not grant Base view access.

**Step 3: Capture controlled publication evidence**

Open the resulting Form link in a clean anonymous browser context. Verify that
the actual question controls and submit button render. Do not submit a row.

**Step 4: Record a safe operator receipt**

Record only timestamp, Form name, scope category, and pass/fail outcome in the
asset registry after the browser check. Never commit the link.

### Task 3: Correlate UI acceptance with metadata read-back

**Files:**
- No repository source changes expected.

**Step 1: Run the expert Form metadata probe**

Run `refresh_phase3_expert_form.py --probe` against the configured Base.
Confirm the expected question counts and Form identity.

**Step 2: Check external transport behavior**

Run the bounded anonymous HTTP probe. It may provide supporting evidence, but
the clean-browser Form rendering remains the authority because Feishu may use
client-side routing.

**Step 3: Stop on discrepancy**

If browser acceptance fails, leave the Form unpublished, preserve the UI error
category and developer-console operation log, and do not retry undocumented
metadata publication calls.

### Task 4: Re-enter the unified task and automation path only through gates

**Files:**
- No immediate source changes expected.

**Step 1: Keep task Form blocked**

Reconfirm the seven-field maintenance dry-run. Do not run it without a new
explicit `FDE_PHASE3_MAINTENANCE_WINDOW` authorization.

**Step 2: Require a fresh automation implementation plan**

Before enabling any Bitable automation extension, write and approve a separate
plan for the Nautilus event receiver, idempotent read-back, P0 write path,
Mentor projection, failure handling, and one authorized synthetic record.

**Step 3: Commit the completed publication work**

Run focused tests, static checks, `git diff --check`, and commit only the CLI,
test, registry, and plan/doc changes. Do not push or merge.

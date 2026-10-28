# FDE Phase 3 Single-Submission Flywheel Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Replace the split Phase 3 intake with one full task-and-trajectory Form, automatic QC routing, and a narrow 智涌导师 knowledge/status projection while retaining Bitable read-back as the only business authority.

**Architecture:** A new canonical four-table schema is created in the existing empty Base. Two public Forms write only expert profile or a complete task trajectory. 智涌Nautilus receives controlled Bitable events, records automatic review decisions, and exposes a small projection to 智涌导师. Old source tables and Forms are archived only after the new schema and a synthetic record pass read-back verification.

**Tech Stack:** Python 3.13, pytest, existing `ecc-shared` Feishu Bitable client, Feishu Bitable/Form APIs, existing 智涌Nautilus and 智涌导师 applications.

---

### Task 1: Define the canonical schema contract

**Files:**
- Create: `phase3/backend/services/fde_phase3_single_submission_schema.py`
- Create: `phase3/backend/tests/test_fde_phase3_single_submission_schema.py`

**Step 1: Write failing schema tests**

Cover these exact conditions:
- four canonical tables have the approved names;
- exactly two public Forms exist;
- the task Form includes all buyer-required task and interaction fields;
- `revision_of` is an internal self-link and is not public;
- expert field enums remain constrained;
- no public field is an internal state, feedback, verdict, export, or receipt field.

**Step 2: Run the focused test file**

Run: `python -m pytest tests/test_fde_phase3_single_submission_schema.py -q`

Expected: FAIL because the schema module does not exist.

**Step 3: Implement the minimum immutable schema specification**

Use `FieldSpec` and `TableSpec` patterns from
`services/fde_phase3_20260722_schema.py`. Keep the Phase 3 primary category
options in one place and make all internal fields explicitly non-public.

**Step 4: Re-run focused tests**

Run: `python -m pytest tests/test_fde_phase3_single_submission_schema.py -q`

Expected: PASS.

**Step 5: Commit**

```powershell
git add phase3/backend/services/fde_phase3_single_submission_schema.py phase3/backend/tests/test_fde_phase3_single_submission_schema.py
git commit -m "feat(fde): define single-submission phase3 schema"
```

### Task 2: Implement automatic QC and Mentor projection contracts

**Files:**
- Create: `phase3/backend/services/fde_phase3_single_submission_qc.py`
- Create: `phase3/backend/services/fde_phase3_mentor_projection.py`
- Create: `phase3/backend/tests/test_fde_phase3_single_submission_qc.py`
- Create: `phase3/backend/tests/test_fde_phase3_mentor_projection.py`

**Step 1: Write failing tests**

Test deterministic gates for tool mode, six or more rounds, required evidence,
share reference, log ID, and attestation. Test three outcomes:
`buyer_ready`, `repair_required`, and `blocked`. Test that a projection only
contains the requesting expert's task status, next action, authorized feedback
summary, and knowledge-pack version.

**Step 2: Run focused tests**

Run: `python -m pytest tests/test_fde_phase3_single_submission_qc.py tests/test_fde_phase3_mentor_projection.py -q`

Expected: FAIL because modules do not exist.

**Step 3: Implement pure, no-I/O logic**

The QC module must record policy/model version and reason codes. It must never
write a buyer verdict. The Mentor projection must reject cross-expert access
and raw attachment or raw feedback fields.

**Step 4: Re-run focused tests**

Run: `python -m pytest tests/test_fde_phase3_single_submission_qc.py tests/test_fde_phase3_mentor_projection.py -q`

Expected: PASS.

**Step 5: Commit**

```powershell
git add phase3/backend/services/fde_phase3_single_submission_qc.py phase3/backend/services/fde_phase3_mentor_projection.py phase3/backend/tests/test_fde_phase3_single_submission_qc.py phase3/backend/tests/test_fde_phase3_mentor_projection.py
git commit -m "feat(fde): add automatic qc and mentor projection contracts"
```

### Task 3: Build a guarded Bitable reconciliation adapter

**Files:**
- Create: `phase3/backend/services/fde_phase3_single_submission_provisioning.py`
- Create: `phase3/backend/scripts/reconcile_phase3_single_submission_base.py`
- Create: `phase3/backend/tests/test_fde_phase3_single_submission_provisioning.py`

**Step 1: Write failing tests**

Test that dry-run performs no remote mutation, apply requires the exact
confirmation string, canonical tables and Form views are created before any
old Form is retired, and legacy table archival is rename-only. Test read-back
rejects field or form drift.

**Step 2: Run focused test**

Run: `python -m pytest tests/test_fde_phase3_single_submission_provisioning.py -q`

Expected: FAIL because the adapter does not exist.

**Step 3: Implement the adapter and CLI**

Use the existing `LarkHttpClient` and add only the required table, field, view,
and Form operations. Never read business records in the schema reconciler.
Require `--apply --confirm FDE_PHASE3_SINGLE_SUBMISSION`. The default mode must
print only a schema plan and names, never credentials or record content.

**Step 4: Run focused test**

Run: `python -m pytest tests/test_fde_phase3_single_submission_provisioning.py -q`

Expected: PASS.

**Step 5: Run a live dry run against the explicit Base**

Run: `python scripts/reconcile_phase3_single_submission_base.py --base-token <explicit-token>`

Expected: JSON plan only; zero record reads and zero mutations.

**Step 6: Commit**

```powershell
git add phase3/backend/services/fde_phase3_single_submission_provisioning.py phase3/backend/scripts/reconcile_phase3_single_submission_base.py phase3/backend/tests/test_fde_phase3_single_submission_provisioning.py
git commit -m "feat(fde): add guarded single-submission base reconciler"
```

### Task 4: Implement and test the two native Form contracts

**Files:**
- Create: `phase3/backend/services/fde_phase3_single_submission_forms.py`
- Create: `phase3/backend/scripts/publish_phase3_single_submission_forms.py`
- Create: `phase3/backend/tests/test_fde_phase3_single_submission_forms.py`

**Step 1: Write failing tests**

Test that the expert Form exposes only expert fields; the task Form exposes
the full task-and-interaction pack; both Forms hide internal fields before
public sharing; old three public Forms are unshared only after the new two
Forms verify.

**Step 2: Run focused test**

Run: `python -m pytest tests/test_fde_phase3_single_submission_forms.py -q`

Expected: FAIL because the Form module does not exist.

**Step 3: Implement native Form metadata and field updates**

Use only Bitable Form APIs. Publish with `anyone_editable` and no Base read
access. The task Form instructions must explicitly require the approved Doubao
Office Task mode, six relevant rounds, screenshots, share reference, and log
ID.

**Step 4: Re-run focused test**

Run: `python -m pytest tests/test_fde_phase3_single_submission_forms.py -q`

Expected: PASS.

**Step 5: Commit**

```powershell
git add phase3/backend/services/fde_phase3_single_submission_forms.py phase3/backend/scripts/publish_phase3_single_submission_forms.py phase3/backend/tests/test_fde_phase3_single_submission_forms.py
git commit -m "feat(fde): publish two single-submission forms"
```

### Task 5: Add the application integration contract

**Files:**
- Create: `docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md`
- Create: `phase3/backend/services/fde_phase3_feishu_runtime_contract.py`
- Create: `phase3/backend/tests/test_fde_phase3_feishu_runtime_contract.py`

**Step 1: Write failing tests**

Test that only 智涌Nautilus can issue canonical Base mutations, that Mentor
calls consume a projection rather than raw Base rows, and that a callback
event is idempotent by Bitable record identity plus version.

**Step 2: Run focused test**

Run: `python -m pytest tests/test_fde_phase3_feishu_runtime_contract.py -q`

Expected: FAIL because the runtime contract does not exist.

**Step 3: Implement pure contract and runbook**

Define the signed event payload, idempotency key, allowed updates, card action
types, knowledge-pack version fields, and permissions to remove from Mentor.
Do not create a web UI or use chat sessions as runtime transport.

**Step 4: Re-run focused test**

Run: `python -m pytest tests/test_fde_phase3_feishu_runtime_contract.py -q`

Expected: PASS.

**Step 5: Commit**

```powershell
git add docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md phase3/backend/services/fde_phase3_feishu_runtime_contract.py phase3/backend/tests/test_fde_phase3_feishu_runtime_contract.py
git commit -m "feat(fde): define feishu app runtime contract"
```

### Task 6: Apply the empty-Base schema and publish the new Forms

**Files:**
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Snapshot metadata only**

Run the reconciliation script in dry-run mode and store only table, field, and
view names plus a schema hash. Do not read raw records.

**Step 2: Apply schema with explicit confirmation**

Run the reconciler with `--apply --confirm FDE_PHASE3_SINGLE_SUBMISSION`.
It must create canonical tables and Forms, archive legacy tables by renaming,
and leave old tables intact.

**Step 3: Verify read-back**

Confirm four canonical tables, two Form views, no public legacy Forms, and no
business records in the archived legacy tables.

**Step 4: Publish Forms with explicit confirmation**

Run the Form publisher with `--apply --confirm FDE_PHASE3_SINGLE_SUBMISSION`.
Verify public URLs return 200 without granting Base view access.

**Step 5: Record only safe asset metadata and commit**

Do not commit Base tokens, shared URLs, raw records, or app secrets.

### Task 7: Bind applications and verify one synthetic end-to-end record

**Files:**
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`
- Modify: `docs/business/FDE_PHASE3_BITABLE_AUTHORITY.md`

**Step 1: Apply least-privilege app configuration**

Keep 智涌Nautilus as the canonical Base app. Remove direct Base access from
智涌导师 after the projection endpoint and card callback are ready. Bind the
existing automation extension only to the new task submission trigger.

**Step 2: Configure the four event routes**

`submission_created`, `qc_completed`, `repair_required`, and
`buyer_feedback_recorded`. Each route must carry Bitable record identity,
idempotency key, and no raw buyer material.

**Step 3: Run a synthetic record**

Use an authorized synthetic record. Verify Form submission, automatic QC,
linked review, Mentor next-action projection, revision lineage, and read-back.

**Step 4: Stop at the export boundary**

Do not enable buyer sync, V5 export, Compass import, settlement, or model
training in this task. Record their remaining gates.

**Step 5: Run full focused suite and commit**

Run:

```powershell
python -m pytest tests/test_fde_phase3_single_submission_schema.py tests/test_fde_phase3_single_submission_qc.py tests/test_fde_phase3_mentor_projection.py tests/test_fde_phase3_single_submission_provisioning.py tests/test_fde_phase3_single_submission_forms.py tests/test_fde_phase3_feishu_runtime_contract.py -q
```

Commit the asset registry and authority updates only after all tests and live
read-back gates pass.

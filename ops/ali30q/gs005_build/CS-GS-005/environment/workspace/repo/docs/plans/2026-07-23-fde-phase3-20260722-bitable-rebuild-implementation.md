# Phase 3 20260722 Bitable Rebuild Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Provision the approved Phase 3 Bitable schema and three external form views from the verified 2026-07-22 buyer field contract.

**Architecture:** One existing internal Base remains the operational authority. Three new intake tables accept expert details, task pre-screening, and post-interaction evidence; internal task, attempt, review, and export tables remain the only lifecycle and receipt authority. No buyer Sheet record is read, copied, or written by this workflow.

**Tech Stack:** Python 3, standard-library HTTP, existing Zhiyong Nautilus tenant credentials, Feishu Bitable v1 API, pytest.

---

### Task 1: Encode the verified field contract

**Files:**
- Create: `phase3/backend/services/fde_phase3_20260722_schema.py`
- Create: `phase3/backend/tests/test_fde_phase3_20260722_schema.py`

**Step 1: Write failing contract tests**

Assert the exact ten expert fields, the two verified expert dropdowns, the seven pre-screen fields, the verified first-level category list, and the UID-plus-five-field interaction result contract. Assert that public forms contain no P0, buyer verdict, export, or Compass fields.

**Step 2: Run the focused test**

Run: `python -m pytest phase3/backend/tests/test_fde_phase3_20260722_schema.py -q`

Expected: FAIL because the contract module does not exist.

**Step 3: Implement the immutable schema contract**

Use small frozen dataclasses and explicit Feishu field type definitions. Keep internal fields separate from public field lists. Preserve the buyer's free-text lower category and work-domain fields.

**Step 4: Run the focused test**

Expected: PASS.

**Step 5: Commit**

Commit the contract, test, and plan before any remote write.

### Task 2: Add an idempotent provisioner

**Files:**
- Create: `phase3/backend/scripts/provision_phase3_20260722_bitable.py`
- Create: `phase3/backend/services/fde_phase3_20260722_provisioning.py`
- Modify: `phase3/backend/tests/test_fde_phase3_20260722_schema.py`

**Step 1: Write failing provision-plan tests**

Assert dry-run is the default, the script has an explicit confirmation flag for writes, it creates only the three named source tables and form views, and it cannot create business records.

**Step 2: Run the focused test**

Expected: FAIL because the provisioner does not exist.

**Step 3: Implement the minimum provisioner**

Reuse the established tenant-token and post-write read-back pattern. Discover existing tables and views by name, create only missing tables or form views, and print non-sensitive names plus IDs only. Never call a records endpoint.

**Step 4: Run focused tests and static checks**

Run: `python -m pytest phase3/backend/tests/test_fde_phase3_20260722_schema.py -q`

Expected: PASS.

### Task 3: Provision and verify the approved online structure

**Files:**
- No repository source changes required.

**Step 1: Run the provisioner in dry-run mode**

Verify the target Base schema and planned table/view names. Stop if an existing name has a different schema.

**Step 2: Run the explicit apply command**

Create only the approved source tables and native Form views inside the current Base. Do not create records, buyer synchronization, V5 export, or Compass import.

**Step 3: Read back table, field, and view metadata**

Compare against the verified field contract. Record only names and schema hashes in the operational handoff.

### Task 4: Publish safely and retire the incorrect public forms

**Files:**
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Configure each native Form view through the supported Feishu Form API**

Expose only its public field list. Mark required fields, add the verified dropdowns, and add field-level guidance derived from the interaction protocol. Publish with “anyone with the link can submit” and no Base viewing permission. Apply field visibility before enabling public sharing and read back both Form metadata and Form-question metadata.

**Step 2: Validate anonymous access without submitting a business record**

Verify the published page is reachable and its visible labels match the contract. Do not perform a test submission containing personal or task material.

**Step 3: Disable the two obsolete public form links**

Keep their underlying Base records untouched. Mark only the public form links as retired after the replacement links pass reachability checks.

**Step 4: Commit the updated registry**

Record only publication state and form purposes, never URLs, tokens, personal data, buyer material, or credentials.

### Task 5: Keep automation gated

**Files:**
- Modify: `docs/business/FDE_PHASE3_INTERACTIVE_PROTOCOL_20260722.md`

**Step 1: Record the post-form state boundary**

The automation extension may normalize a submitted source record only after a separately approved, read-back-verified mapping. It cannot decide P0, buyer verdict, Repair, or create a V5/Compass export.

**Step 2: Commit the boundary update**

Do not enable automation, buyer synchronization, V5 export, or Compass import as part of this implementation.

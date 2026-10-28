# Phase 3 Single-Chain Agent Workflow Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Turn the approved Phase 3 design into one auditable Bitable-led expert workflow, with two external Forms, Nautilus-controlled automation, Mentor guidance, and a clear operating package for the team.

**Architecture:** Bitable remains the only business authority. Feishu Forms create initial records; the automation extension sends a non-content event to Nautilus; Nautilus reads back, applies an idempotent rule version, and makes the narrow permitted write. Mentor receives a redacted expert-scoped projection. V5 and Compass are separately owned deidentified downstream consumers and do not share this worktree's write scope.

**Tech Stack:** Python 3.13, pytest, FastAPI, existing Feishu/Lark adapter, Feishu Bitable and native Forms, existing Zhiyong Nautilus and Zhiyong Mentor apps.

---

### Task 1: Finish the team operations package without creating a second ledger

**Files:**
- Create: `docs/business/phase3_expert_operations/README.md`
- Create: `docs/business/phase3_expert_operations/01_RECRUITING_KIT.md`
- Create: `docs/business/phase3_expert_operations/02_EXPERT_ONBOARDING.md`
- Create: `docs/business/phase3_expert_operations/03_OPERATOR_SOP.md`
- Modify: `phase3/backend/tests/test_fde_phase3_expert_operations_kit.py`

**Step 1: Preserve the existing failing coverage test**

Run:

```powershell
python -m pytest tests/test_fde_phase3_expert_operations_kit.py -q
```

Expected: FAIL because the operation-package documents do not exist.

**Step 2: Create the four audience-specific documents**

Document the single Wiki/cloud-document entry point, recruiter copy, expert onboarding, six-turn Office Task instructions, evidence-submission checklist, FAQ, repair notices, and the operator exception-only SOP. Use the payment wording `200 元` and `验收通过后 3 个工作日内` but state that P0 is not buyer acceptance.

**Step 3: Keep expert-facing material safe**

Extend the test so expert-facing files reject internal-only names including `revision_of`, `payload_hash`, `manifest_hash`, record identifiers, and any buyer raw-feedback marker. The operator document may explain ownership but cannot create a manual status ledger.

**Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_fde_phase3_expert_operations_kit.py tests/test_fde_phase3_single_submission_forms.py -q
```

Expected: PASS.

**Step 5: Commit**

```powershell
git add docs/business/phase3_expert_operations phase3/backend/tests/test_fde_phase3_expert_operations_kit.py
git commit -m "docs(fde): add phase3 team operations kit"
```

### Task 2: Add a fail-closed obsolete-table cleanup command

**Files:**
- Create: `phase3/backend/services/fde_phase3_archive_cleanup.py`
- Create: `phase3/backend/scripts/prune_phase3_archives.py`
- Create: `phase3/backend/tests/test_fde_phase3_archive_cleanup.py`
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Write the failing cleanup tests**

Use a fake metadata client. Verify that the cleanup plan selects only tables whose names start with `归档_20260723_`, refuses any of the four canonical table names, refuses a table with a currently shared Form or active automation binding, and never invokes deletion in dry-run mode.

**Step 2: Implement a narrow protocol and plan object**

Define `ArchiveCleanupClient` with metadata-only reads and an explicit `delete_table(table_id)` operation. The planner returns names only; it never prints tokens, table IDs, records, attachments, or Form URLs.

```python
plan = cleanup.plan()
assert plan.deletable_table_names == expected_archive_names
receipt = cleanup.apply(confirmed=True)
assert receipt.remaining_table_names == CANONICAL_TABLE_NAMES
```

**Step 3: Add a guarded CLI**

`prune_phase3_archives.py` accepts an explicit Base token, has dry-run as its default, and requires both `--apply` and `--confirm FDE_PHASE3_DELETE_ARCHIVES`. On apply it re-reads metadata after each deletion and stops on the first unexpected table set.

**Step 4: Verify local behavior**

Run:

```powershell
python -m pytest tests/test_fde_phase3_archive_cleanup.py -q
python scripts/prune_phase3_archives.py --help
```

Expected: tests pass and the help text states the confirmation phrase.

**Step 5: Commit**

```powershell
git add phase3/backend/services/fde_phase3_archive_cleanup.py phase3/backend/scripts/prune_phase3_archives.py phase3/backend/tests/test_fde_phase3_archive_cleanup.py docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md
git commit -m "feat(fde): add guarded archive cleanup"
```

### Task 3: Remove obsolete Base assets and restore the full canonical schema

**Files:**
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`
- Modify: `LOOP_STATE_SSOT.md`

**Step 1: Obtain a metadata-only cleanup dry run**

Run the new cleanup CLI with the explicit Base token but without `--apply`. Confirm it selects all and only obsolete archive tables. Inspect only names, view sharing state, automation-binding state, and canonical table names.

**Step 2: Execute user-approved deletion**

Run:

```powershell
python scripts/prune_phase3_archives.py --base-token <approved-token> --apply --confirm FDE_PHASE3_DELETE_ARCHIVES
```

Expected: the read-back table list contains only the four canonical tables; the command prints no record data or external URLs.

**Step 3: Execute the existing maintenance window**

Run:

```powershell
python scripts/maintain_phase3_single_submission.py --base-token <approved-token> --apply --confirm FDE_PHASE3_MAINTENANCE_WINDOW
```

Expected: the task Form is private during the operation, the seven approved fields are created, schema/Form metadata reads back successfully, and the task Form returns to its approved publication state only on success.

**Step 4: Perform native Form acceptance checks**

In the Feishu native Form-share UI, verify exactly two official Forms. Set each to internet link holders can fill without Base-view access. Use a fresh external browser context to inspect visible questions and the Submit action; do not create a test row solely for this check.

**Step 5: Record only non-sensitive status**

Update the asset registry and `LOOP_STATE_SSOT.md` with deletion/maintenance result, date, remaining table count, field-readback status, and the next runtime gate. Do not put IDs, links, credentials, or user data in Git.

**Step 6: Commit documentation-only result**

```powershell
git add docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md LOOP_STATE_SSOT.md
git commit -m "docs(fde): record canonical Base cleanup"
```

### Task 4: Implement the Nautilus event orchestrator behind existing contracts

**Files:**
- Create: `phase3/backend/services/fde_phase3_event_orchestrator.py`
- Create: `phase3/backend/tests/test_fde_phase3_event_orchestrator.py`
- Modify: `phase3/backend/services/fde_phase3_feishu_runtime_contract.py`
- Modify: `phase3/backend/services/fde_phase3_mentor_projection.py`
- Modify: `phase3/backend/tests/test_fde_phase3_feishu_runtime_contract.py`

**Step 1: Write failing orchestration tests**

Cover an authenticated event envelope, a pre-write read-back, exactly one controlled mutation, a post-write read-back, idempotent replay, stale-version rejection, and a rejected non-Nautilus actor.

```python
result = orchestrator.handle(envelope)
assert result.outcome == "written_and_read_back"
assert repository.write_count == 1
assert orchestrator.handle(envelope).outcome == "already_processed"
assert repository.write_count == 1
```

**Step 2: Introduce explicit repository and projection protocols**

The orchestrator receives an `EventEnvelope`, a Bitable read/write repository, the existing pure rule contract, an idempotency store, and a Mentor projection publisher. Its public interface accepts only the five approved runtime routes; it does not accept raw chat text or arbitrary Bitable field updates.

**Step 3: Keep the Mentor projection opaque**

Replace `MentorTaskGuidance.submission_record_id` with an opaque task handle. Require the handle generator to be deterministic per expert/task scope and reject internal record identifiers in serialized Mentor payloads.

**Step 4: Implement route-specific behavior**

- `submission_created`: initialize approved task fields after read-back.
- `qc_completed`: write P0 outcome and create/update its review record.
- `repair_required`: issue or consume only a valid single-use repair reference and create lineage through the controlled gate.
- `buyer_feedback_recorded`: normalize approved feedback category but never invent buyer acceptance.
- `compass_receipt_recorded`: require the existing dual-signature verifier and exact task/event/payload/manifest binding.

**Step 5: Verify**

Run:

```powershell
python -m pytest tests/test_fde_phase3_event_orchestrator.py tests/test_fde_phase3_feishu_runtime_contract.py tests/test_fde_phase3_single_submission_qc.py -q
ruff check --ignore E402 services/fde_phase3_event_orchestrator.py services/fde_phase3_feishu_runtime_contract.py services/fde_phase3_mentor_projection.py
```

Expected: all tests and lint pass.

**Step 6: Commit**

```powershell
git add phase3/backend/services/fde_phase3_event_orchestrator.py phase3/backend/services/fde_phase3_feishu_runtime_contract.py phase3/backend/services/fde_phase3_mentor_projection.py phase3/backend/tests/test_fde_phase3_event_orchestrator.py phase3/backend/tests/test_fde_phase3_feishu_runtime_contract.py
git commit -m "feat(fde): orchestrate canonical phase3 events"
```

### Task 5: Expose authenticated Nautilus runtime endpoints

**Files:**
- Create: `phase3/backend/api/fde_phase3_runtime.py`
- Create: `phase3/backend/tests/test_api_fde_phase3_runtime.py`
- Modify: `phase3/backend/main.py`
- Modify: `docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md`

**Step 1: Write FastAPI tests first**

Test the Feishu verification challenge, rejected missing/invalid event authentication, supported route dispatch, duplicate acknowledgment, and fail-closed error response. The endpoint must not echo event body content, record identifiers, secret data, or internal exceptions.

**Step 2: Implement the router**

Create `POST /api/platform/fde/phase3/events`. It validates the Feishu event signature/challenge through a configurable verifier, converts only the approved metadata fields into an event envelope, invokes the orchestrator, and returns a minimal status code. Register the router in `main.py` with the existing Phase 3 API family.

**Step 3: Add mentor projection and status endpoints**

Expose application-authenticated, expert-scoped endpoints only. Authentication must bind the caller to an opaque expert scope before returning a mentor projection. No endpoint accepts a raw Bitable record ID from the client.

**Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_api_fde_phase3_runtime.py tests/test_fde_phase3_event_orchestrator.py -q
python -m py_compile api/fde_phase3_runtime.py
```

Expected: PASS.

**Step 5: Commit**

```powershell
git add phase3/backend/api/fde_phase3_runtime.py phase3/backend/tests/test_api_fde_phase3_runtime.py phase3/backend/main.py docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md
git commit -m "feat(fde): add authenticated phase3 runtime api"
```

### Task 6: Bind the existing Feishu applications and automation extension

**Files:**
- Create: `docs/business/FDE_PHASE3_FEISHU_BINDING_RUNBOOK.md`
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Document exact live configuration checks**

The runbook lists the two existing application identities by role only, the required Bitable scopes, event subscription route, message-card permission, Mentor scopes, automation-extension trigger condition, disabled legacy automations, and failure-log location. It contains no secrets, IDs, or URLs.

**Step 2: Configure in Feishu developer console and Base**

Use the existing Nautilus app for the two Form-created triggers and the existing Mentor app for expert-scoped messages. The extension forwards only route/record/version metadata to Nautilus. Verify published versions and callback reachability; do not add another app.

**Step 3: Test sandbox event delivery**

Use the Feishu developer console's event verification/test mechanism where it does not create a business record. Confirm Nautilus authenticates the request, returns the verification response, and logs a sanitized result.

**Step 4: Commit the redacted runbook**

```powershell
git add docs/business/FDE_PHASE3_FEISHU_BINDING_RUNBOOK.md docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md
git commit -m "docs(fde): add phase3 app binding runbook"
```

### Task 7: Complete V5/Compass handoff without cross-repository writes

**Files:**
- Modify: `LOOP_STATE_SSOT.md`
- Modify: `docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md`

**Step 1: Specify the sole downstream artifact contract**

Record the Core-owned required fields: `task_v3_*`, `sha256:<64 hex>`, `event_id`, `payload_hash`, `manifest_hash`, signer key IDs, and signatures. Record that Compass signs its receipt over the same four-value binding.

**Step 2: Issue a bounded development handoff**

Send V5 and Compass the canonical input/output/blocker/acceptance list. Their threads own their repositories and must not change Bitable, Forms, or Core runtime code.

**Step 3: Require independent test evidence**

V5/Compass must show rejection of altered JSONL, manifest, receipt, hash format, missing signature, and incorrect four-value binding before Core turns on receipt handling.

**Step 4: Commit canonical coordination update**

```powershell
git add LOOP_STATE_SSOT.md docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md
git commit -m "docs(fde): bind downstream signature contract"
```

### Task 8: Run one authorized end-to-end operational rehearsal and publish the guide

**Files:**
- Create: `docs/business/FDE_PHASE3_LAUNCH_ACCEPTANCE.md`
- Modify: `LOOP_STATE_SSOT.md`
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Define the rehearsal record and permissions**

Obtain a user-authorized, non-sensitive test or real expert record. Do not fabricate a buyer verdict or upload raw acceptance materials. Name the exact operator, expected route, and cleanup policy in the launch checklist without putting personal data in Git.

**Step 2: Exercise the available chain**

Verify Form ingress -> Bitable read-back -> event authentication -> Nautilus P0 -> Bitable read-back -> Mentor projection -> status/repair card. If buyer feedback and dual signatures are approved and ready, extend to V5/Compass; otherwise record that boundary as pending rather than simulating it.

**Step 3: Publish the team guide**

Create one internal Feishu Wiki/cloud-document parent and add the operation package sections. Link the two official Forms and filtered Base views; do not copy task status into the guide. Give recruiting, training, operator, buyer liaison, and technical owners a one-page start path.

**Step 4: Independently verify and record the result**

Capture only sanitized completion evidence: read-back statuses, route result, idempotency outcome, and the remaining blocker if any. Update launch acceptance and canonical state. Never call the workflow complete because of a unit test or an agent self-report.

**Step 5: Commit**

```powershell
git add docs/business/FDE_PHASE3_LAUNCH_ACCEPTANCE.md LOOP_STATE_SSOT.md docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md
git commit -m "docs(fde): record phase3 launch acceptance"
```

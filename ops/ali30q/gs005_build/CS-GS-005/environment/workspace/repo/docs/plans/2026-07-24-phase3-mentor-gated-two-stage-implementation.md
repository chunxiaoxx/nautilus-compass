# Phase 3 Mentor-Gated Two-Stage Flow Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Replace the unified task-and-interaction intake with an agent-gated
question-precheck flow and a Mentor-launched interaction continuation, without
making experts match records or exposing internal identifiers.

**Architecture:** Bitable remains the only business authority. A public
question-precheck Form creates a question row. Nautilus read-backs and decides
whether to issue an opaque continuation through Zhiyong Mentor. The authenticated
Mentor continuation creates one linked interaction row through the controlled
Nautilus writer. Review, buyer feedback, V5 and Compass stay downstream of the
linked interaction result.

**Tech Stack:** Python 3.13, pytest, FastAPI, existing Feishu/Lark adapter,
existing Zhiyong Nautilus and Zhiyong Mentor applications, Bitable native Forms
for registration and question precheck, and an authenticated Mentor continuation
page for interaction evidence.

---

### Task 1: Add a metadata-only two-stage migration inventory

**Files:**
- Create: `phase3/backend/services/fde_phase3_two_stage_migration.py`
- Create: `phase3/backend/tests/test_fde_phase3_two_stage_migration.py`
- Modify: `phase3/backend/scripts/prune_phase3_archives.py`
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Write failing migration tests**

Create fake metadata clients that prove the inventory:

- reads only table, field and Form-view metadata;
- recognizes `数据表` as deletable only when its exact empty default schema,
  no shared Form and no active automation are verified;
- recognizes archived `第三期题目预审` and `第三期交互成果` as reuse candidates,
  never as deletion targets before a migration plan is accepted;
- rejects a missing canonical expert/review/export table or unverified
  automation state.

**Step 2: Run the tests to verify failure**

```powershell
python -m pytest tests/test_fde_phase3_two_stage_migration.py -q
```

Expected: FAIL because the migration inventory does not exist.

**Step 3: Implement the metadata-only planner**

Define a plan that reports names and field-name diffs only. It must have two
independent destructive confirmations:

- `FDE_PHASE3_DELETE_DEFAULT_TABLE` for the user-authorized default table;
- a later migration confirmation for tables that have been superseded after
  successful two-stage read-back.

Never inspect records, attachments, submitted Forms, or buyer material.

**Step 4: Verify and commit**

```powershell
python -m pytest tests/test_fde_phase3_two_stage_migration.py tests/test_fde_phase3_archive_cleanup.py -q
git add phase3/backend/services/fde_phase3_two_stage_migration.py phase3/backend/scripts/prune_phase3_archives.py phase3/backend/tests/test_fde_phase3_two_stage_migration.py docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md
git commit -m "feat(fde): plan two-stage Base migration"
```

### Task 2: Define the five-table two-stage schema and field maps

**Files:**
- Create: `phase3/backend/services/fde_phase3_two_stage_schema.py`
- Create: `phase3/backend/tests/test_fde_phase3_two_stage_schema.py`
- Modify: `phase3/backend/services/fde_phase3_feishu_runtime_contract.py`
- Modify: `docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md`

**Step 1: Write failing schema tests**

Test the five canonical tables, public question fields, private interaction
fields, required relations, and prohibited public exposure. Assert that neither
`record_id`, relation field, continuation handle, raw buyer feedback nor V5/
Compass fields appear in a public Form contract.

**Step 2: Implement immutable schema specifications**

Define:

- `第三期专家`;
- `第三期题目预审` with expert relation, precheck state and lifecycle fields;
- `第三期交互成果` with question relation, inherited expert relation,
  interaction evidence and interaction QC state;
- `第三期审核与反馈` linked to root question and optional interaction;
- `第三期导出与回执` linked to root question and accepted interaction.

Keep `豆包UID` as a public consistency field only. Define initial question
states and interaction states separately.

**Step 3: Add route-specific field ownership**

Extend the runtime contract so only Nautilus can write the question-to-
interaction relation and state fields after Bitable read-back. Neither Mentor,
the automation extension nor a client can supply an internal relation target.

**Step 4: Verify and commit**

```powershell
python -m pytest tests/test_fde_phase3_two_stage_schema.py tests/test_fde_phase3_feishu_runtime_contract.py -q
ruff check --ignore E402 services/fde_phase3_two_stage_schema.py services/fde_phase3_feishu_runtime_contract.py
git add phase3/backend/services/fde_phase3_two_stage_schema.py phase3/backend/tests/test_fde_phase3_two_stage_schema.py phase3/backend/services/fde_phase3_feishu_runtime_contract.py docs/business/FDE_PHASE3_FEISHU_APP_RUNTIME_CONTRACT.md
git commit -m "feat(fde): define two-stage canonical schema"
```

### Task 3: Implement opaque Mentor continuation handles

**Files:**
- Create: `phase3/backend/services/fde_phase3_continuations.py`
- Create: `phase3/backend/tests/test_fde_phase3_continuations.py`
- Modify: `phase3/backend/services/fde_phase3_mentor_projection.py`
- Modify: `phase3/backend/tests/test_fde_phase3_mentor_projection.py`

**Step 1: Write failing continuation tests**

Cover issuance only after `eligible_for_interaction`, bound expert scope,
expiry, one-time consumption, idempotent duplicate delivery, cross-expert
rejection and serialization without a Bitable record identifier.

**Step 2: Implement pure handle and repository contracts**

Use a cryptographically random opaque handle or signed opaque session token.
Define a `ContinuationStore` protocol with acquire/consume semantics; its
production implementation must be durable and distinct from Bitable business
state. Store only opaque technical references, expiry, state and hashes; do not
store raw conversation data or user identity in the continuation payload.

**Step 3: Extend Mentor projection**

Mentor receives a task card action and opaque continuation reference, never a
task ID, Bitable row ID or manually typed code. The card renders only the next
human action and a safe expiry/reissue path.

**Step 4: Verify and commit**

```powershell
python -m pytest tests/test_fde_phase3_continuations.py tests/test_fde_phase3_mentor_projection.py -q
git add phase3/backend/services/fde_phase3_continuations.py phase3/backend/tests/test_fde_phase3_continuations.py phase3/backend/services/fde_phase3_mentor_projection.py phase3/backend/tests/test_fde_phase3_mentor_projection.py
git commit -m "feat(fde): add Mentor interaction continuations"
```

### Task 4: Split automated P0 into question and interaction gates

**Files:**
- Create: `phase3/backend/services/fde_phase3_question_precheck.py`
- Create: `phase3/backend/tests/test_fde_phase3_question_precheck.py`
- Modify: `phase3/backend/services/fde_phase3_event_orchestrator.py`
- Modify: `phase3/backend/tests/test_fde_phase3_event_orchestrator.py`

**Step 1: Write failing gate tests**

Test that a question can become only `eligible_for_interaction`,
`question_repair_required`, or `blocked`; it cannot become buyer-accepted.
Test that interaction evidence is rejected before eligible question read-back,
and that the six-turn/image/link/log checks occur only at the interaction gate.

**Step 2: Implement pure question precheck**

Evaluate question contract, domain tags, attachments, safety, duplicate/conflict
signals and answerability. Return versioned reason codes and a disposition. Do
not inspect raw buyer feedback or make payment/export decisions.

**Step 3: Extend the orchestrator routes**

Add approved metadata-only routes for `question_created`, `question_precheck_
completed`, and `interaction_submitted`. Every mutation requires pre-read,
narrow authorized write, post-read version advancement and durable idempotency.

**Step 4: Verify and commit**

```powershell
python -m pytest tests/test_fde_phase3_question_precheck.py tests/test_fde_phase3_event_orchestrator.py tests/test_fde_phase3_feishu_runtime_contract.py -q
ruff check --ignore E402 services/fde_phase3_question_precheck.py services/fde_phase3_event_orchestrator.py
git add phase3/backend/services/fde_phase3_question_precheck.py phase3/backend/tests/test_fde_phase3_question_precheck.py phase3/backend/services/fde_phase3_event_orchestrator.py phase3/backend/tests/test_fde_phase3_event_orchestrator.py
git commit -m "feat(fde): gate interaction on question precheck"
```

### Task 5: Add authenticated Mentor continuation endpoints

**Files:**
- Modify: `phase3/backend/api/fde_phase3_runtime.py`
- Modify: `phase3/backend/tests/test_api_fde_phase3_runtime.py`
- Modify: `phase3/backend/main.py`
- Modify: `docs/business/FDE_PHASE3_FEISHU_BINDING_RUNBOOK.md`

**Step 1: Write failing API tests**

Test that only an authenticated Mentor session can open a continuation or submit
interaction evidence; the payload cannot supply a Bitable record ID, expert ID
or arbitrary relation. Test expired, consumed and cross-scope handles, duplicate
submission and fail-closed dependency configuration.

**Step 2: Implement two narrow endpoints**

Create a Mentor-scoped continuation endpoint that returns the interaction page
configuration, plus a submission endpoint that accepts only public interaction
fields. Resolve all Bitable identities server-side from the continuation store.
Return generic client errors; do not echo internal state or raw event payloads.

**Step 3: Verify and commit**

```powershell
python -m pytest tests/test_api_fde_phase3_runtime.py tests/test_fde_phase3_continuations.py -q
python -m py_compile api/fde_phase3_runtime.py main.py
git add phase3/backend/api/fde_phase3_runtime.py phase3/backend/tests/test_api_fde_phase3_runtime.py phase3/backend/main.py docs/business/FDE_PHASE3_FEISHU_BINDING_RUNBOOK.md
git commit -m "feat(fde): add Mentor interaction submission api"
```

### Task 6: Update Skills and team guidance to the two-stage route

**Files:**
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-internal\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\fde-task-pipeline\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\ecc-shared\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-external\SKILL.md`
- Create: `phase3/backend/scripts/verify_phase3_skill_contract.py`
- Create: `phase3/backend/tests/test_verify_phase3_skill_contract.py`
- Create: `docs/business/FDE_PHASE3_SKILL_REGISTRY.md`
- Modify: `docs/business/phase3_expert_operations/02_EXPERT_ONBOARDING.md`
- Modify: `docs/business/phase3_expert_operations/03_OPERATOR_SOP.md`
- Modify: `phase3/backend/tests/test_fde_phase3_expert_operations_kit.py`

**Step 1: Write failing content-contract assertions**

Assert that user-facing material explains the two visible actions, does not
ask for a task code or table choice, and does not claim P0 is buyer acceptance.
Assert that internal Skills name the two stage tables and opaque Mentor
continuation rather than the retired unified Form.

**Step 2: Add a portable Skill-contract verifier**

The global Skill directory is an installed deployment asset rather than a Git
repository. Create a verifier that accepts a `--skills-root`, checks the four
canonical Skill files for their role and two-stage routing clauses, and never
prints their full content. Unit-test it against a temporary fixture root.

**Step 3: Update the four canonical Skills and team documents**

Keep the existing role split: `fde-task-pipeline` remains sole orchestrator,
`ecc-shared` remains the only Feishu boundary, `ecc-fde-internal` manages
state, and `ecc-fde-external` explains only the expert-facing route. Do not
create a fifth Skill or revive checklist scoring as a delivery gate.

Record names, roles and expected semantic version in the repository registry;
do not copy full Skills into a second source tree. Patch the installed Skill
files with `apply_patch`, run the verifier against the installed root, and
record only the resulting non-sensitive version/hash metadata.

**Step 4: Verify and commit**

```powershell
python -m pytest tests/test_verify_phase3_skill_contract.py tests/test_fde_phase3_expert_operations_kit.py -q
python scripts/verify_phase3_skill_contract.py --skills-root C:\Users\chunx\.agents\skills
git add phase3/backend/scripts/verify_phase3_skill_contract.py phase3/backend/tests/test_verify_phase3_skill_contract.py docs/business/FDE_PHASE3_SKILL_REGISTRY.md docs/business/phase3_expert_operations phase3/backend/tests/test_fde_phase3_expert_operations_kit.py
git commit -m "docs(fde): align Skills with two-stage flow"
```

### Task 7: Apply the approved Base migration and Form configuration

**Files:**
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`
- Modify: `LOOP_STATE_SSOT.md`
- Create: `docs/business/FDE_PHASE3_TWO_STAGE_MIGRATION_ACCEPTANCE.md`

**Step 1: Run metadata-only inventory**

Use the existing application credentials through the approved local source.
Read only table names, field metadata, Form-view metadata and automation
bindings. Do not read records, attachments or submitted Forms.

**Step 2: Delete only the authorized default table**

Run the new guarded command with both explicit flags. Re-read the table list.
Stop on any unexpected table, shared Form or active/unverified automation.

**Step 3: Provision or reuse two-stage tables and Form views**

Make `第三期题目预审` the only generally shared task Form. Do not broadly
publish `第三期交互成果`; it is reached through an authenticated Mentor
continuation only. Make every schema and Form change in a private maintenance
window and read back metadata before reopening the question Form.

**Step 4: Verify app/configuration gates**

Verify the published Nautilus and Mentor versions, callback signature,
session binding, required Bitable scopes, card action route, automation trigger
and sanitized error-log route. Do not enable automatic P0 until all gates are
independently evidenced.

**Step 5: Record and commit non-sensitive evidence**

Document names/counts/statuses only. Do not include secrets, URLs, table IDs,
records, expert data or buyer material.

```powershell
git add docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md LOOP_STATE_SSOT.md docs/business/FDE_PHASE3_TWO_STAGE_MIGRATION_ACCEPTANCE.md
git commit -m "docs(fde): record two-stage Base migration"
```

### Task 8: Run one authorized end-to-end rehearsal

**Files:**
- Modify: `docs/business/FDE_PHASE3_TWO_STAGE_MIGRATION_ACCEPTANCE.md`
- Modify: `LOOP_STATE_SSOT.md`

**Step 1: Obtain an authorized non-sensitive test participant**

Do not fabricate buyer feedback or use a developer chat as evidence. Record
only a sanitized role and test scope in Git.

**Step 2: Exercise the available route**

Verify registration/session binding -> question Form -> question P0 read-back
-> Mentor task card -> authenticated interaction submission -> automatic
relation read-back -> interaction P0. Confirm that duplicate card delivery is
idempotent and a cross-scope card is refused.

**Step 3: Extend only when eligible**

Buyer mapping, V5 export and Compass import remain disabled unless their
separate eligibility and signature gates are ready. Report them as blocked,
not simulated.

**Step 4: Verify and commit**

```powershell
python -m pytest tests/test_fde_phase3_two_stage_schema.py tests/test_fde_phase3_continuations.py tests/test_fde_phase3_question_precheck.py tests/test_api_fde_phase3_runtime.py -q
git add docs/business/FDE_PHASE3_TWO_STAGE_MIGRATION_ACCEPTANCE.md LOOP_STATE_SSOT.md
git commit -m "docs(fde): record two-stage rehearsal"
```

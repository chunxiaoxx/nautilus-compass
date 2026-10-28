# G1-A Automatic Constitutional Gate Implementation Plan

> **Execution status:** PLAN ONLY. This document is not implementation
> authorization. Stop after reviewing and committing the plan. Tasks 1-6 may
> begin only after a new, explicit user authorization that names G1-A gate
> implementation; approval of this plan does not authorize Compass edits or
> any runtime work.

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a pure Platform gate that source-binds the fixed V5 plan-only waiver, current Compass read-only capsule, and historical O1 provenance, then derives only `ready_for_r1a_plan` or exact blockers without granting runtime authority.

**Architecture:** Keep `m1-r1a-plan-admission-v1` immutable. Add a v2 pure evaluator with an injected read-only Git authority, exact JSON allowlists, fixed planning-only authorization, and one versioned evidence document. V5 and Compass retain their own artifacts; Platform reads exact commits and blob bytes and creates no database or runtime state.

**Tech Stack:** Python 3.11+, frozen dataclasses, canonical JSON, SHA-256, local read-only Git subprocesses, pytest, Ruff.

---

## Execution boundary

This plan implements only the G1-A gate. It does not implement an R1a runtime,
the parked three-operation dogfood plan, DMAS runtime, Compose, Docker,
database, model, tool, network, deployment, push, merge, or FDE work.

Work only in the existing isolated worktree and commit only the files named by
each task. Any pre-existing uncommitted v2 draft remains non-authoritative until
its tests are observed RED, the implementation is rebuilt or verified GREEN,
and independent review passes.

**Current stop gate:** do not execute Task 1 or any later task in the present
planning turn. The Platform coordinator must first report the reviewed plan and
obtain a separate implementation authorization. Compass owner work in Task 4
also requires that authorization and an explicit bounded owner handoff.

## Task 1: Freeze the current source facts

**Read-only sources:**

- Platform: `phase3/backend/platform_protocol/m1_r1a_admission.py`
- Platform: `phase3/backend/tests/platform_protocol/test_m1_r1a_plan_admission.py`
- Platform: `phase3/backend/docs/evidence/m1-r1a-plan-admission-v1.json`
- V5 Git blob:
  `cdd55315f03c145e7d83d5a0eddbfeeb5d951c94:docs/contracts/v5-r1a-plan-only-authorization-v1.json`
- Compass expected path:
  `docs/contracts/m1-r1a-grounding-capsule-v1.json`

**Step 1: Prove the fixed V5 bytes**

From the injected V5 authority clone, resolve both full commits, verify
authority-to-proposal ancestry, read the exact blob, and recompute SHA-256.
Expected digest:
`9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6`.

**Step 2: Prove the current Compass gap**

Resolve the current Compass authority commit and require the expected capsule
path to be absent. Record only `compass_owner_input_missing`; do not create the
owner file.

**Step 3: Preserve v1**

Record `git diff --exit-code` for the v1 evaluator, v1 tests, and v1 evidence
before v2 work. Repeat the same command before commit.

## Task 2: Write the v2 contract tests first

**Files:**

- Create:
  `phase3/backend/tests/platform_protocol/test_m1_r1a_plan_admission_v2.py`

**Step 1: Write the positive planning-only test**

Define the wished-for API:

```python
decision = evaluate_plan_only_admission_v2(
    document,
    source_readback=source_readback,
)
assert decision.status == "ready_for_r1a_plan"
assert decision.reason_codes == ()
```

The test uses historical O1 revisions different from current owner proposals
and proves both sets of bindings were independently read.

**Step 2: Write focused negative tests**

Cover wrong commit/path/hash/ancestry, extra fields, runtime or database
authorization, changed allowed action, V5 waiver semantic widening, Compass
capability widening, invalid attempt-binding semantics, missing owner claims,
historical O1 relabelling, incomplete decisions, and source-readback rejection.

**Step 3: Observe RED**

Run from `phase3/backend`:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_m1_r1a_plan_admission_v2.py -q --confcutdir=tests/platform_protocol
```

Expected: fail because the v2 evaluator does not yet exist. A syntax or fixture
failure is not an acceptable RED.

## Task 3: Implement the minimum pure v2 evaluator

**Files:**

- Create:
  `phase3/backend/platform_protocol/m1_r1a_plan_admission_v2.py`
- Create:
  `phase3/backend/docs/evidence/m1-r1a-plan-admission-v2.json`
- Modify only if a public export is required:
  `phase3/backend/platform_protocol/__init__.py`

**Step 1: Add exact parsers**

Use frozen output data, full-SHA and SHA-256 validation, exact field sets,
fixed authorization values, canonical blocker ordering, and no free-form
evidence fields.

**Step 2: Add source read-back**

Read exact Git objects before deriving a ready result. Parse the V5 waiver and
Compass capsule bytes, not merely caller-supplied hashes. Treat the historical
O1 artifact as capability provenance only and validate its internal historical
Task 6/V5/Compass bindings.

**Step 3: Derive rather than accept the decision**

Only missing or pending current owner inputs become blockers. Invalid evidence
raises `AdmissionViolation`. Compare the document's claimed status and reasons
to the derived result before returning.

**Step 4: Run GREEN and refactor**

Run the focused v2 test until all cases pass. Refactor only after GREEN and
rerun the same command.

## Task 4: Obtain the Compass owner capsule

**Owner repository:** Compass only.

The Platform coordinator sends the design's exact consumer constraints. The
Compass owner creates the expected contract and focused test in a clean isolated
worktree, commits only owner files, and returns:

- authority and proposal full SHAs;
- exact path and Git-blob SHA-256;
- focused pytest/Ruff/format/compile results;
- clean status; and
- explicit confirmation that all runtime capabilities are false.

Platform does not edit Compass, accept a conversation summary as evidence, or
reuse the historical `d719db1e…` capsule as current authority.

If the owner input remains absent, keep v2 evidence blocked and stop before any
R1a plan/runtime task.

## Task 5: Perform real source read-back and update the decision

**Files:**

- Modify:
  `phase3/backend/docs/evidence/m1-r1a-plan-admission-v2.json`
- Modify tests only for new owner evidence:
  `phase3/backend/tests/platform_protocol/test_m1_r1a_plan_admission_v2.py`

**Step 1: Run in a fresh process**

Instantiate the read-back with the configured Platform, V5, and Compass GitHub
authority clones. Read the committed evidence document and evaluate it without
network or checkout writes.

**Step 2: Update only immutable Compass pins**

Replace the missing Compass values with the owner-returned full commits, exact
path, hash, test status, and all-false capability map. Set the document decision
to `ready_for_r1a_plan` only if the evaluator independently derives no blockers.

**Step 3: Re-run negative mutations**

Against the frozen evidence, mutate each commit, path, hash, authority field,
capability, nested map, decision, and extra field. Every case must fail closed.

## Task 6: Verify, review, and commit

From `phase3/backend`, run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_m1_r1a_plan_admission.py tests/platform_protocol/test_m1_r1a_plan_admission_v2.py -q --confcutdir=tests/platform_protocol
python -m pytest tests/platform_protocol -q --confcutdir=tests/platform_protocol
python -m ruff check platform_protocol tests/platform_protocol
python -m ruff format --check platform_protocol tests/platform_protocol
python -m compileall -q platform_protocol tests/platform_protocol
git diff --check
```

Also require:

- v1 files byte-for-byte unchanged;
- a fresh local-Git read-back of V5 and Compass exact blobs;
- no imports of SQLAlchemy, Alembic, legacy databases, dotenv, provider SDKs,
  network clients, FDE modules, or runtime modules;
- no credentials, local authority paths, raw prompts, or business data in new
  evidence;
- independent read-only review High=0 and Medium=0; and
- `git show --check`, exact file inventory, and clean worktree after a bounded
  follow-up commit.

Do not amend the documentation commit. Do not push, merge, deploy, or start the
parked dogfood tasks.

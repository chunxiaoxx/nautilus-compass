# Internal R&D Dogfood Coordination Implementation Plan

> **Execution status:** PARKED. G1-A constitutional gate is the sole current
> target. All tasks below, Tasks 1-9, are not authorized.

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prove one source-bound, three-operation, no-business-data L2 internal R&D dogfood chain using existing Platform Protocol V2, a minimal V5 executor, a read-only Compass capsule, and an independent verifier.

**Architecture:** Platform is the sole coordinator and evidence plane. V5 owns bounded execution artifacts, Compass owns one read-only synthetic rule, and a distinct verifier signs the existing Protocol V2 receipt. All cross-owner inputs are pinned to exact Git commits, paths, and hashes. The campaign result is a pure read-only projection over three existing operation chains, not a database table or second state machine.

**Tech Stack:** Python 3.11+, dataclasses, canonical JSON and SHA-256, Ed25519 through the existing `cryptography` dependency, SQLAlchemy/Alembic, disposable local PostgreSQL, pytest, Ruff, Git source read-back.

---

## Global execution rules

- Work only in clean isolated worktrees with `codex/` branches.
- Run tests before implementation for every behavior change and capture RED.
- Commit only named task files; never amend, push, merge, or deploy.
- Do not use network/model/provider calls, production services, Docker, FDE,
  business data, credentials, legacy database helpers, or old V5 autonomous
  runtimes.
- Stop after any gate reports an open High or Medium finding.
- Do not start Task 3 or later until Task 1 derives `ready_for_r1a_plan` and
  the user separately authorizes runtime implementation.
- Do not create a campaign table, workflow table, or copied owner ledger.

### Working repositories

- Platform authority clone: `C:\Users\chunx\Projects\nautilus-core`
- V5 authority clone: `C:\Users\chunx\nautilus-v5`
- Compass authority clone: `C:\Users\chunx\Projects\nautilus-compass`
- Historical M0 candidate worktree:
  `C:\Users\chunx\Projects\nautilus-core\.worktrees\m0-v1-synthetic-dogfood-platform`
- Historical M0 candidate commit:
  `2346217edc9ed7b60f2fb7556ee9a177849acee6`

## Task 1: Close the Compass owner gap and resolve the circular G1 gate

**Owner boundary:** Compass authors only its capsule; V5 confirms only its
existing waiver; Platform derives the decision. No runtime code is authorized.

**Platform files:**

- Modify: `phase3/backend/docs/evidence/m1-r1a-plan-admission-v1.json`
- Modify: `phase3/backend/tests/platform_protocol/test_m1_r1a_plan_admission.py`
- Modify only if a demonstrated parser defect requires it:
  `phase3/backend/platform_protocol/m1_r1a_admission.py`
- Create only after a separate versioned contract decision:
  `phase3/backend/platform_protocol/m1_r1a_plan_admission_v2.py`
- Create only with that decision:
  `phase3/backend/tests/platform_protocol/test_m1_r1a_plan_admission_v2.py`

**Compass owner file:**

- Create in the Compass owner worktree:
  `docs/contracts/m1-r1a-grounding-capsule-v1.json`
- Create the owner-selected focused contract test in the Compass repository.

**Step 1: Obtain the missing owner evidence**

The Compass owner must return a clean full commit, the exact capsule path,
SHA-256 of Git blob bytes, schema `m1-r1a-owner-input-v1`, passing focused
tests, and the exact all-false capability map for `drift_write`, `ingest`,
`model`, `network`, `recall`, `source_write`, and `tool`.

If this handoff is absent, stop with `compass_owner_input_missing`. Platform
must not create the Compass artifact.

**Step 2: Write failing Platform source-readback tests**

Add tests that require a fresh O1 candidate to bind the current V5 proposal and
Compass proposal exactly. Include RED cases for:

```python
def test_current_owner_pins_are_required_for_ready_decision(): ...
def test_compass_capsule_blob_tamper_is_rejected(): ...
def test_v5_waiver_blob_tamper_is_rejected(): ...
def test_owner_summary_without_source_blob_is_rejected(): ...
def test_ready_status_cannot_be_self_declared(): ...
```

Run from `phase3/backend`:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_m1_r1a_plan_admission.py -q --confcutdir=tests/platform_protocol
```

Expected: the new ready-path test fails because the current evidence remains
historical or does not yet bind the new Compass source.

**Step 3: Re-evaluate the current v1 gate without changing its meaning**

Update the Compass owner input and let the existing parser derive the result.
Do not set `verification_status=reverified_candidate` or either revision status
to `current_owner_pinned` unless a separately authorized, fresh O1 acceptance
run has actually produced `docs/evidence/m1/o1_acceptance.json` with those exact
owner revisions and all required runtime evidence. Never copy or hand-edit a
prior acceptance result to clear the gate.

Without such a run, the honest expected result remains `blocked` after the
Compass gap closes, with the historical O1 blockers still present.

**Step 4: Present the versioned gate decision**

Stop and obtain one explicit user decision:

1. approve a new planning-only `m1-r1a-plan-admission-v2` that source-binds the
   historical O1 artifact as capability provenance and the current V5/Compass
   blobs as plan inputs, but cannot authorize runtime; or
2. separately authorize a fresh offline O1 acceptance run against current
   owner commits.

The recommended choice is option 1 because a runtime run should not be a
precondition for writing a reviewable runtime plan. If approved, start with RED
tests proving that v2 cannot claim runtime authority, cannot relabel historical
O1 as current execution evidence, and cannot accept unbound owner blobs. Keep
v1 immutable as historical evidence.

**Step 5: Run focused and static gates**

```powershell
python -m pytest tests/platform_protocol/test_contracts.py tests/platform_protocol/test_contract_hardening.py tests/platform_protocol/test_m1_r1a_plan_admission.py -q --confcutdir=tests/platform_protocol
python -m ruff check platform_protocol tests/platform_protocol/test_m1_r1a_plan_admission.py
python -m ruff format --check platform_protocol tests/platform_protocol/test_m1_r1a_plan_admission.py
python -m compileall -q platform_protocol tests/platform_protocol/test_m1_r1a_plan_admission.py
git diff --check
```

Run the CLI/source read-back in a fresh process against the three GitHub
authority clones. Expected derived result is either the honest remaining v1
blocker list or, only after a separately approved and tested v2 contract, a
planning-only ready result. Obtain an independent High=0 / Medium=0 review
before committing.

**Step 6: Commit only the approved G1 files**

```powershell
git add phase3/backend/docs/evidence/m1-r1a-plan-admission-v1.json phase3/backend/tests/platform_protocol/test_m1_r1a_plan_admission.py
git commit -m "docs(platform): bind current M1 R1a owner inputs"
```

If `m1_r1a_admission.py` needed a tested defect fix, include it in the same
bounded commit and state why. If the user approved v2, also stage only the two
named v2 files and their versioned evidence. Otherwise do not create or stage
them.

## Task 2: Source-admit the historical M0 harness as a reuse candidate

**Files:**

- Create: `phase3/backend/platform_protocol/internal_rd_dogfood_admission.py`
- Create: `phase3/backend/tests/platform_protocol/test_internal_rd_dogfood_admission.py`
- Create:
  `phase3/backend/docs/evidence/internal-rd-dogfood-m0-reuse-admission-v1.json`
- Modify: `phase3/backend/platform_protocol/__init__.py`

**Step 1: Write failing exact-source tests**

The decision schema must pin only the reviewed candidate blobs:

- `tests/platform_protocol/m0_v1_dogfood_authorization.py`
- `tests/platform_protocol/m0_v1_dogfood_cli.py`
- `tests/platform_protocol/m0_v1_dogfood_harness.py`
- `tests/platform_protocol/test_m0_v1_dogfood_authorization.py`
- `tests/platform_protocol/test_m0_v1_dogfood_cli.py`
- `tests/platform_protocol/test_m0_v1_dogfood_fail_closed.py`
- `tests/platform_protocol/test_m0_v1_dogfood.py`

Add RED tests for wrong commit, wrong path, changed bytes, an extra path,
missing file, descendant-only evidence, self-declared approval, and attempts to
admit production modules or migration files.

```python
def test_exact_reviewed_blobs_can_be_source_admitted(): ...
def test_descendant_commit_without_exact_blob_pins_is_rejected(): ...
def test_unreviewed_runtime_path_is_rejected(): ...
def test_admission_document_rejects_extra_fields(): ...
```

Run:

```powershell
python -m pytest tests/platform_protocol/test_internal_rd_dogfood_admission.py -q --confcutdir=tests/platform_protocol
```

Expected: collection or behavior failure before implementation.

**Step 2: Implement the minimum pure admission evaluator**

Use `LocalGitSourceReadback` rather than checkout, copying, or ancestry alone.
The evaluator must:

```python
@dataclass(frozen=True, slots=True)
class M0ReuseDecision:
    status: str
    reason_codes: tuple[str, ...]

def evaluate_m0_reuse_admission(
    document: Mapping[str, object],
    *,
    source_readback: SourceReadback,
) -> M0ReuseDecision:
    """Derive approved or blocked from exact commit/path/hash evidence."""
```

Accept no extra fields and no source paths outside the seven-file allowlist.
The output authorizes reuse review only; it does not authorize execution.

**Step 3: Publish the exact decision and verify**

Populate the evidence file with the recomputed SHA-256 for every allowlisted
blob and a derived status. Run the focused test, the Task 1 focused tests,
Ruff, format, compileall, `git diff --check`, and an independent High=0 /
Medium=0 review.

**Step 4: Commit**

```powershell
git add phase3/backend/platform_protocol/internal_rd_dogfood_admission.py phase3/backend/platform_protocol/__init__.py phase3/backend/tests/platform_protocol/test_internal_rd_dogfood_admission.py phase3/backend/docs/evidence/internal-rd-dogfood-m0-reuse-admission-v1.json
git commit -m "feat(platform): source-admit M0 dogfood harness"
```

## Task 3: Define the pure three-operation evidence projection

**Files:**

- Create: `phase3/backend/platform_protocol/internal_rd_dogfood_evidence.py`
- Create: `phase3/backend/tests/platform_protocol/test_internal_rd_dogfood_evidence.py`
- Create:
  `phase3/backend/platform_protocol/internal_rd_dogfood_vectors_v1.json`
- Create:
  `phase3/backend/platform_protocol/internal_rd_dogfood_vectors_v1.sha256`
- Modify: `phase3/backend/platform_protocol/.gitattributes`
- Modify: `phase3/backend/platform_protocol/__init__.py`

**Step 1: Write failing contract tests**

Define one immutable projection that references exactly three distinct
operation chains and labels the evidence `L2`. Add RED cases for duplicated
operation/attempt IDs, noncanonical ordering, extra fields, invalid hashes,
unknown outcome labels, evidence-level uplift, raw text, paths, signatures,
tokens, or business/FDE fields.

```python
EXPECTED_TASKS = (
    ("synthetic_repair", "completed"),
    ("synthetic_policy_refusal", "refused"),
    ("synthetic_grounding_review", "review_required"),
)
```

The projection records existing Protocol IDs and hashes only. It exposes no
mutation method and adds no SQLAlchemy model or migration.

**Step 2: Implement the minimum immutable contract**

Use frozen dataclasses, exact field sets, canonical JSON, and deterministic
SHA-256. Reuse the identifier, UTC, and hash rules from Protocol V2 rather than
creating looser validators.

**Step 3: Publish conformance vectors**

Add one accepted vector and fail-closed vectors for every forbidden class.
Force LF for both vector files in the narrow `.gitattributes`, recompute the
digest from canonical bytes, and test a fresh checkout representation.

**Step 4: Verify and commit**

Run the new tests, all Platform contract tests, Ruff, format, compileall,
vector-hash read-back, dependency/sensitive-field scan, and independent review.
Commit only the named files:

```powershell
git commit -m "feat(platform): define internal dogfood evidence projection"
```

## Task 4: Produce the minimal V5 synthetic executor owner package

**Repository:** V5 owner worktree only.

**Expected owner-owned files:**

- Create: `docs/contracts/internal-rd-dogfood-executor-v1.json`
- Create: `nautilus_v5/internal_rd_dogfood/contracts.py`
- Create: `nautilus_v5/internal_rd_dogfood/executor.py`
- Create: `tests/internal_rd_dogfood/test_contracts.py`
- Create: `tests/internal_rd_dogfood/test_executor.py`

The V5 owner may choose an equivalent narrow package path, but must report the
final exact paths before Platform writes an admission record.

**Step 1: Resolve executor identity before code**

Write a failing owner test that rejects conflicting executor principal/release
claims. Select one synthetic registered identity and release and bind them in
the owner contract. Do not inherit historical numeric identity constants.

**Step 2: Write failing executor tests**

Cover the fixed repair, correct policy refusal, grounding-required review,
input-HMAC mismatch, wrong attempt, wrong policy hash, path escape, unexpected
capability, raw response, and nondeterministic output.

**Step 3: Implement only the fixed executor seam**

The executor accepts a validated attempt binding and a synthetic fixture. It
returns a bounded candidate-patch artifact plus manifest input. It has no
network, model, environment-key, database, shell, terminal, general
ToolGateway, or file-write capability. The independent verifier may apply that
patch only to a disposable synthetic fixture under the test harness; no owner
source worktree is mutated or merged.

**Step 4: Verify, review, and owner-commit**

Run focused tests, Ruff, format, compileall, dependency/network/secret scan,
and independent High=0 / Medium=0 review. The V5 owner commits and returns the
clean full SHA, paths, blob hashes, identity/release/key binding, tests, and
limitations to Platform. Platform does not edit this repository.

## Task 5: Bind the read-only Compass rule

**Repository:** Compass owner worktree only.

Task 1's capsule is the only permitted grounding input. Add no Compass runtime.
The owner tests must prove canonical bytes, exact all-false capabilities,
synthetic content only, and absence of recall/model/network/tool/ingest/write
authority.

Platform source-reads the exact submitted commit and capsule blob. A changed,
historical, or unpinned capsule blocks admission before an operation starts. A
post-admission tamper case produces no verifier receipt. No experience is
promoted or written.

The Compass owner returns one clean commit and stops. Platform records only the
commit/path/hash and approved opaque rule identifier.

## Task 6: Source-admit current V5 and Compass runtime inputs for L2

**Platform files:**

- Create:
  `phase3/backend/platform_protocol/internal_rd_dogfood_owner_admission.py`
- Create:
  `phase3/backend/tests/platform_protocol/test_internal_rd_dogfood_owner_admission.py`
- Create:
  `phase3/backend/docs/evidence/internal-rd-dogfood-owner-admission-v1.json`
- Modify: `phase3/backend/platform_protocol/__init__.py`

This is a new decision. Task 1's V5 waiver authorizes planning only, and Task 2
admits only historical harness blobs. Neither can admit the new V5 executor.

**Step 1: Write failing source-admission tests**

Require exact current V5 executor contract/module/test blob hashes and the exact
current Compass capsule commit/path/hash. Bind the V5 registered executor
identity, release, key id, fixed capability, tool-policy hash, and the three
synthetic task fixture hashes.

Add RED tests for wrong/descendant commit, changed or missing blob, extra path,
identity/release/key drift, runtime capability widening, a changed Compass
capsule, reused plan-only waiver, self-declared admission, and any task outside
the three-item allowlist.

```python
def test_exact_current_owner_blobs_are_admitted_for_l2_only(): ...
def test_v5_plan_waiver_cannot_admit_executor_runtime(): ...
def test_unbound_executor_blob_is_rejected_before_operation(): ...
def test_compass_capsule_drift_is_rejected_before_operation(): ...
```

**Step 2: Implement a pure derived decision**

Use Git object read-back for every path and SHA-256. The only positive status
is `admitted_for_local_l2_harness`; it authorizes the three named synthetic
operations against a disposable database and nothing else. It explicitly
prohibits production, model, network, source mutation, push, merge, deployment,
Compass write, and FDE.

**Step 3: Make it an operation precondition**

The test harness receives the immutable derived decision through injection and
checks it before constructing caller credentials or invoking
`accept_operation`. A blocked or malformed decision must yield zero protocol
writes. Do not persist the decision in a new table.

**Step 4: Verify and commit**

Run focused admission tests, Tasks 1-3 contracts, source read-back from fresh
processes, Ruff, format, compileall, diff check, and independent High=0 /
Medium=0 review. Commit only the four named Platform files.

## Task 7: Build the test-only integration harness

**Files:**

- Create:
  `phase3/backend/tests/platform_protocol/internal_rd_dogfood_harness.py`
- Create:
  `phase3/backend/tests/platform_protocol/internal_rd_dogfood_cli.py`
- Create:
  `phase3/backend/tests/platform_protocol/test_internal_rd_dogfood_chain.py`
- Create:
  `phase3/backend/tests/platform_protocol/test_internal_rd_dogfood_fail_closed.py`
- Modify: `phase3/backend/tests/platform_protocol/conftest.py`

**Step 1: Write a failing end-to-end test**

Require the same pinned source inputs to flow through:

```text
source admission -> request -> caller credential verification
-> unique eligible executor selection -> Platform envelope -> accept_operation
-> record_attempt claim
-> V5 artifact -> record_manifest
-> independently verified receipt -> record_receipt -> outbox claim/ack
-> separate database read-back
```

The first RED test must fail before any harness is imported from the historical
candidate.

**Step 2: Port only source-admitted behavior**

Reimplement or mechanically port only the Task 2 allowlisted behavior. Do not
import from another worktree at runtime and do not copy unreviewed commits.
Use existing `ProtocolService`, DB-backed registry, Ed25519 verification,
attempt-scoped HMAC, protected artifact reference, and retry-safe outbox.
Implement DMAS semantics only as a pure test-harness selection over the fixed
registered candidates: exactly one capability/policy/release match is selected;
zero or multiple matches fail before the Platform envelope is issued or
`accept_operation` is called. Do not add a production
router, queue, service, schema, or second routing-decision ledger.

**Step 3: Add the three operations**

Run three distinct operations with the expected semantic outcomes:

| Task | Artifact outcome | Receipt decision | Reason |
| --- | --- | --- | --- |
| repair | `completed` | `accepted` | `policy_satisfied` |
| prohibited change | `refused` | `accepted` | `policy_satisfied` |
| ambiguous change | `review_required` | `accepted` | `policy_satisfied` |

The receipt approves evidence of correct bounded execution. It never grants
merge or deployment authority.

**Step 4: Add fail-closed integration tests with fixed receipt semantics**

Cover every scenario in the design matrix, including executor/verifier key
reuse, wrong HMAC, source-pin tamper, prohibited path, capsule removal, exact
replay, changed replay, zero/multiple eligible executors, injected transaction
failure, and forged L3/L4/L5 evidence.

Assert the exact mapping from the design:

- admission/caller/routing failures: no operation and zero writes;
- idempotency conflicts: original operation unchanged and no new events;
- attempt or pre-manifest failures: no receipt and no partial writes;
- post-manifest tamper: no receipt, state remains `manifest_received`;
- intact malicious synthetic output: independently signed
  `rejected/policy_denied` receipt;
- correct refusal/review: `accepted/policy_satisfied`; and
- exact replay: original records with zero growth.

Do not exercise or emit `blocked/input_unavailable` or
`blocked/verifier_unavailable` without a separate design for a truthful,
independent signed attestation.

## Task 8: Add deterministic CLI evidence and independent read-back

**Files:**

- Create:
  `phase3/backend/tests/platform_protocol/test_internal_rd_dogfood_cli.py`
- Create after an authorized run:
  `phase3/backend/docs/evidence/internal-rd-dogfood-l2-readback-v1.json`

**Step 1: Write failing CLI tests**

Require exact CLI arguments, exact database-name regex, no URL query/options,
an empty explicit `public` schema, exact evidence field allowlists, fixed
values, no secrets or paths, and a separate read-back process.

**Step 2: Implement minimum test-only CLI**

The CLI must refuse any target other than a unique disposable local PostgreSQL
database. It may not create, select, or delete arbitrary databases and may not
fall back to legacy configuration.

**Step 3: Run only after explicit database authorization**

Use a unique database name validated before creation. Put the already-approved
PostgreSQL password only in one process environment, never in output, a file,
or Git. Run the three-operation chain twice in fresh databases, require
byte-identical redacted evidence, precisely drop each named database, and read
back absence.

Expected invariant for the second replay inside each run: zero growth in
operation, attempt, manifest, receipt, audit, and outbox counts; delivered
outbox events remain delivered.

## Task 9: Full verification and independent adjudication

From `phase3/backend`, run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol -q --confcutdir=tests/platform_protocol
python -m ruff check platform_protocol platform_migrations tests/platform_protocol
python -m ruff format --check platform_protocol platform_migrations tests/platform_protocol
python -m compileall -q platform_protocol platform_migrations tests/platform_protocol
git diff --check
git show --check --stat HEAD
git status --short
```

Also verify:

- one Alembic head and unchanged canonical Protocol V2 vector hash;
- no new migration or model/table;
- owner Git source read-back from fresh processes;
- no dependency, network, credential, private-key, raw-evidence, local-path,
  account, business, or FDE persistence;
- exact three-operation row/audit/outbox counts and replay invariants;
- exact database cleanup read-back; and
- evidence level exactly `L2`.

Give frozen full SHAs and evidence to a new read-only reviewer. Fix every High
or Medium through RED-to-GREEN follow-up commits without amend. Completion
requires High=0 / Medium=0 and clean Platform, V5, and Compass worktrees.

Stop after committing the L2 evidence package. Do not start L3 internal-source
dogfood, production runtime, deployment, push, or merge.

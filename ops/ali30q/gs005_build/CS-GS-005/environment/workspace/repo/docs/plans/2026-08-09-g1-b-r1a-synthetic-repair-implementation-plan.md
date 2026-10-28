# G1-B R1a Synthetic Repair Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build one separately authorized, fixed, no-business-data R1a synthetic code-repair chain that uses Platform Protocol V2, one uniquely selected V5 executor, the pinned read-only Compass rule, and a distinct verifier, then produces deterministic Platform read-back evidence.

**Architecture:** Platform source-admits every owner blob and performs a pure unique-candidate DMAS selection before issuing an operation. The existing `ProtocolService` owns operation, attempt, manifest, receipt, audit, and outbox persistence; V5 produces only a deterministic candidate patch; Compass supplies only the already pinned all-false rule; a distinct verifier applies the patch to a disposable fixture and signs the receipt.

**Tech Stack:** Python 3.13, frozen dataclasses, canonical JSON, SHA-256 and HMAC-SHA-256, Ed25519 from the existing `cryptography` dependency, SQLAlchemy, disposable local PostgreSQL, pytest, Ruff, Git object read-back.

---

## Execution gate

No runtime task is authorized by this commit. Do not execute Task 1 or any
later task until the user separately approves R1a runtime against the final
G1-B full SHA after both V5 and Compass return High=0 and Medium=0.

This plan does not authorize a model, general tool, network, production
database, Docker, source self-modification, deployment, push, merge, business
workflow, FDE action, or Compass memory write. The future database steps below
refer only to a uniquely named disposable local Protocol V2 database and still
require the separate runtime authorization.

The Platform implementation session must begin from the approved G1-B commit
in a new clean worktree. V5 owner work occurs only in a V5 owner worktree.
Compass is read-only unless it reports a versioned conflict with its current
capsule. No task may edit another owner's repository.

### Task 1: Add runtime admission and executor-evidence contracts

**Files:**

- Create: `phase3/backend/platform_protocol/m1_r1a_runtime_admission.py`
- Create: `phase3/backend/platform_protocol/m1_r1a_execution_evidence.py`
- Create: `phase3/backend/platform_protocol/m1_r1a_execution_evidence_vectors_v1.json`
- Create: `phase3/backend/platform_protocol/m1_r1a_execution_evidence_vectors_v1.sha256`
- Modify: `phase3/backend/platform_protocol/.gitattributes`
- Create: `phase3/backend/tests/platform_protocol/test_m1_r1a_runtime_admission.py`
- Create: `phase3/backend/tests/platform_protocol/test_m1_r1a_execution_evidence.py`
- Create: `phase3/backend/docs/evidence/m1-r1a-runtime-admission-v1.json`

**Step 1: Write the failing exact-source tests**

Define the wished-for interface:

```python
decision = evaluate_r1a_runtime_admission_bytes(
    evidence_bytes,
    source_readback=source_readback,
)
assert decision.status == "blocked"
assert decision.reason_codes == ("v5_executor_owner_input_missing",)
```

The evidence must pin:

- the approved G1-B full commit and both plan-document blob hashes;
- Platform G1-A evidence at `21a36fd2...`;
- V5 authority `f560be28...` and a future executor proposal;
- Compass authority `37efc4fc...`, proposal `e87234bb...`, path, and hash;
- Protocol V2 contract/vector versions; and
- all current runtime permissions as false until owner admission completes.

Add RED cases for duplicate JSON keys, wrong/short commits, wrong paths,
changed bytes, ancestry-only evidence, extra fields, self-declared admission,
current V5 waiver reused as executor admission, changed Compass capability,
and any model/network/database/production/FDE widening.

Also define the wished-for pure `ExecutorExecutionEvidenceV1`. Require exact
fields for operation, attempt, `input_ref_hash`, executor identity/release/key,
capsule/fixture/tool-policy/artifact hashes, fixed result state, canonical UTC
time, algorithm, and `executor_signature`. Its `canonical_signing_bytes` must
exclude only the signature. Add RED cases for every changed binding, unknown
field, duplicate field, wrong algorithm/key/signature, non-UTC time, and raw
patch/evidence/path/prompt/token/private-key fields. Publish byte-exact LF
conformance vectors and their SHA-256; no consumer may create competing
canonical vectors.

Run from `phase3/backend`:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_m1_r1a_runtime_admission.py tests/platform_protocol/test_m1_r1a_execution_evidence.py -q --confcutdir=tests/platform_protocol
```

Expected: FAIL because `m1_r1a_runtime_admission` does not exist. A collection
error caused by a typo is not an acceptable RED.

**Step 2: Implement the minimum blocked decision and pure evidence contract**

Use an injected extension of `LocalGitSourceReadback`, exact field allowlists,
duplicate-key rejection, frozen output data, and canonical reason ordering:

```python
@dataclass(frozen=True, slots=True)
class R1aRuntimeAdmissionDecision:
    status: str
    reason_codes: tuple[str, ...]
```

The initial committed evidence must remain blocked while the V5 executor owner
input is absent. Invalid evidence raises `AdmissionViolation`; it does not
become a caller-selected blocker.

Implement the evidence as a frozen, slots-based value whose signing bytes are
canonical JSON. Reuse the existing Ed25519 validation and DB registry types at
the future service boundary; do not add signing keys, persistence, I/O, or a
runtime call in this task. The Platform contract and vectors are canonical;
V5 will only consume them.

**Step 3: Verify GREEN and preserve G1-A**

Run the focused test, then:

```powershell
python -m pytest tests/platform_protocol/test_m1_r1a_plan_admission_v2.py tests/platform_protocol/test_m1_r1a_runtime_admission.py tests/platform_protocol/test_m1_r1a_execution_evidence.py -q --confcutdir=tests/platform_protocol
git diff --exit-code 21a36fd2cfc8a2223454d1f7c5bc542045910291 -- phase3/backend/platform_protocol/m1_r1a_plan_admission_v2.py phase3/backend/docs/evidence/m1-r1a-plan-admission-v2.json
```

Expected: tests pass and the G1-A evaluator/evidence remain unchanged.

**Step 4: Commit only Task 1 files**

```powershell
git add phase3/backend/platform_protocol/m1_r1a_runtime_admission.py phase3/backend/platform_protocol/m1_r1a_execution_evidence.py phase3/backend/platform_protocol/m1_r1a_execution_evidence_vectors_v1.json phase3/backend/platform_protocol/m1_r1a_execution_evidence_vectors_v1.sha256 phase3/backend/platform_protocol/.gitattributes phase3/backend/tests/platform_protocol/test_m1_r1a_runtime_admission.py phase3/backend/tests/platform_protocol/test_m1_r1a_execution_evidence.py phase3/backend/docs/evidence/m1-r1a-runtime-admission-v1.json
git commit -m "feat(platform): gate R1a synthetic runtime inputs"
```

### Task 2: Produce the V5 fixed executor owner package

**Repository:** V5 owner worktree only.

**Files:**

- Create: `docs/contracts/m1-r1a-synthetic-repair-executor-v1.json`
- Create: `nautilus_v5/m1_r1a_synthetic_repair/__init__.py`
- Create: `nautilus_v5/m1_r1a_synthetic_repair/contracts.py`
- Create: `nautilus_v5/m1_r1a_synthetic_repair/executor.py`
- Create: `tests/m1_r1a_synthetic_repair/test_contracts.py`
- Create: `tests/m1_r1a_synthetic_repair/test_executor.py`

**Step 1: Write the contract RED tests**

The owner contract must bind one registered executor identity, release, Ed25519
key, capability `synthetic_code_repair_v1`, fixture hash, expected patch hash,
oracle hash, tool-policy hash, Platform evidence-contract version/vector hash,
and exact non-authorities.

```python
def test_executor_contract_is_fixed_and_has_no_general_capability() -> None:
    contract = load_executor_contract()
    assert contract["capabilities"] == ["synthetic_code_repair_v1"]
    assert contract["model_authorized"] is False
    assert contract["network_authorized"] is False
    assert contract["source_write_authorized"] is False
    assert contract["self_modify_authorized"] is False
```

Add failures for extra fields, a second task, path escape, changed fixture,
wrong release/key, model or ToolGateway access, environment-key access,
nondeterministic output, and raw prompt/response fields.

Run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/m1_r1a_synthetic_repair/test_contracts.py tests/m1_r1a_synthetic_repair/test_executor.py -q
```

Expected: FAIL because the owner package does not exist.

**Step 2: Implement the minimum deterministic executor**

The callable accepts only validated immutable inputs:

```python
def execute_synthetic_repair(
    *,
    attempt_id: str,
    attempt_secret: bytes,
    input_ref_hash: str,
    binding: Mapping[str, object],
    fixture_hash: str,
    tool_policy_hash: str,
    executor_signer: ExternalSigner,
) -> SignedSyntheticRepairResult:
    ...
```

It must independently derive the attempt HMAC using canonical fields
`attempt_id`, `bound_capsule_hash`,
`derivation_version=m1-attempt-input-hmac-v1`, and the opaque input identifier,
then use `hmac.compare_digest`. Only after the HMAC, fixture, and policy match
may it return the fixed patch artifact, fixed scope-evidence identifiers, and
an `ExecutorExecutionEvidenceV1` serialized exactly against Platform's
canonical vectors. The injected signer signs the evidence
`canonical_signing_bytes`; its private key is ephemeral and is never read from
environment variables, persisted, logged, or returned.

The adapter returns bytes; it does not open, modify, or inspect a repository
file. It imports no provider, HTTP client, shell, terminal, database, general
tool gateway, production Agent daemon, or self-modification module.

**Step 3: Prove the negative matrix**

Require fixed errors for wrong secret/HMAC, attempt, capsule, opaque input,
fixture, policy, identity/release/key, unexpected field, and repeated changed
execution. Add forged evidence, substituted artifact, re-signed changed
binding, wrong registered key, and evidence replay tests. The positive artifact
and evidence signing bytes must be byte-identical across two fresh process
runs; a valid signature must fail after any bound field changes.

**Step 4: Verify, review, and owner-commit**

Run focused tests, Ruff, format, compileall, dependency/network/secret scans,
`git diff --check`, and a V5 owner review. Commit only the six named files and
return the clean full SHA, exact paths, blob hashes, test commands, and
High=0/Medium=0 to Platform. Do not push or merge.

### Task 3: Reconfirm the Compass read-only learning boundary

**Repository:** Compass owner worktree, read-only by default.

**Existing source:**

- `docs/contracts/m1-r1a-grounding-capsule-v1.json`
- `tests/test_m1_r1a_grounding_capsule.py`
- proposal commit `e87234bbdc072bd10e9b88079c21f7c574361506`

**Step 1: Read the exact approved Platform and V5 pins**

The Compass owner receives the approved G1-B full SHA and the submitted V5
executor full SHA. It must inspect both by exact Git object read-back, without
editing Platform or V5.

**Step 2: Run the owner boundary checks**

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/test_m1_r1a_grounding_capsule.py -q
python -m ruff check tests/test_m1_r1a_grounding_capsule.py
python -m ruff format --check tests/test_m1_r1a_grounding_capsule.py
```

The review must confirm:

- the capsule bytes and SHA-256 are unchanged;
- all seven access capabilities remain false;
- Platform, not Compass, derives the attempt HMAC;
- `input_ref_hash` is not the capsule hash;
- the synthetic rule can yield `review_required` without claiming repair
  success; and
- no recall, ingest, promotion, model, network, tool, or write path is added.

**Step 3: Return only ACK or CONFLICT**

If compatible, return `ACK`, the existing full proposal SHA, commands/results,
and High=0/Medium=0. If incompatible, return `CONFLICT` with an exact commit,
path, failing command, and failure output. Do not create a follow-up commit
unless Platform first accepts the conflict and the user authorizes an owner
change.

### Task 4: Admit, claim, and persist authenticated execution evidence

**Files:**

- Modify: `phase3/backend/docs/evidence/m1-r1a-runtime-admission-v1.json`
- Modify: `phase3/backend/tests/platform_protocol/test_m1_r1a_runtime_admission.py`
- Create: `phase3/backend/platform_protocol/m1_r1a_routing.py`
- Create: `phase3/backend/tests/platform_protocol/test_m1_r1a_routing.py`
- Modify: `phase3/backend/platform_protocol/models.py`
- Modify: `phase3/backend/platform_protocol/repository.py`
- Modify: `phase3/backend/platform_protocol/service.py`
- Modify: `phase3/backend/platform_protocol/__init__.py`
- Create: `phase3/backend/platform_migrations/versions/20260809_01_protocol_v2_executor_evidence.py`
- Modify: `phase3/backend/tests/platform_protocol/test_migrations.py`
- Modify: `phase3/backend/tests/platform_protocol/test_service.py`
- Create: `phase3/backend/tests/platform_protocol/test_m1_r1a_execution_evidence_service.py`

**Step 1: Source-read the V5 owner package**

Add the returned V5 full proposal commit, exact path allowlist, blob hashes,
identity, release, key, fixture, policy, and capability bindings. Recompute
every hash from Git object bytes. Re-run all Task 1 tamper tests.

Expected runtime-admission result after exact source read-back:

```python
assert decision.status == "admitted_for_local_r1a_synthetic_repair"
assert decision.reason_codes == ()
```

This status permits only the one local synthetic harness after the separate
runtime authorization. It is not production authorization.

**Step 2: Write routing RED tests**

Define one pure function:

```python
selected = select_unique_executor(
    candidates,
    capability="synthetic_code_repair_v1",
    executor_release=approved_release,
    tool_policy_hash=approved_policy_hash,
    owner_admission=decision,
)
```

Require one exact result. Zero candidates, multiple candidates, inactive
identity, wrong role, release, key, capability, policy, or blocked admission
must fail before operation issuance. The function has no I/O and writes no
routing record.

**Step 3: Prove the attempt claim under real concurrency**

First write a RED integration test that opens two independent PostgreSQL
sessions, synchronizes both after they observe the same operation as
`accepted`, and submits different `attempt_id` values for that operation.
Require exactly one commit, one persisted attempt, one `dispatched` audit and
outbox event, and zero losing rows/events. The loser must receive the fixed
`ProtocolViolation("attempt_claim_conflict")`.

Preserve the existing `ProtocolRepository.transition` compare-and-transition
as the first candidate implementation: attempt insert, operation
`accepted -> dispatched` transition, and event writes stay in one transaction,
so a failed transition rolls everything back. Map the losing transition to the
fixed protocol error. Do not add an operation-wide unique constraint merely to
make the test pass, because that would silently redefine general retry
semantics. If the synchronized RED proves the current CAS insufficient, add
the smallest forward-only, single-head claim mechanism and document why.

**Step 4: Persist executor evidence and manifest atomically**

Add the forward migration and SQLAlchemy model for the exact allowlisted
`protocol_executor_evidence` table. Do not rewrite an existing migration or
change frozen `ManifestV2`/Protocol V2 vectors. The new table binds one
evidence record to the exact operation/attempt/executor/release and stores only
approved protocol IDs, hashes, fixed state/version, canonical UTC time,
algorithm, public key identifier, evidence hash, and `executor_signature`.

Write `record_execution_evidence_and_manifest` RED tests before the service
change. The command must use the DB-backed registry to verify the exact active
executor role/release/key and Ed25519 signature, match `input_ref_hash`,
capsule/fixture/tool-policy/artifact hashes, require a single manifest artifact
with the same hash, and then persist evidence, manifest, state transition,
audit, and outbox in one transaction. Forged evidence, substituted artifact,
wrong key/release, changed binding, expired attempt, and injected failures must
leave no evidence or manifest row. Exact replay returns the original records
without growth.

The independent verifier must later load and re-verify this persisted evidence;
it may not trust a manifest's executor identifier as proof of execution.

**Step 5: Implement the minimum frozen selection result and verify**

The result contains only executor identity, release, key, capability, and
tool-policy hash. It cannot carry prompts, paths, payloads, human identifiers,
fallback order, or free-form reasons.

Run Task 1 and Task 4 focused tests, the synchronized two-session PostgreSQL
test, migration upgrade/downgrade/upgrade with one head, Ruff, format,
compileall, and diff checks. Commit only the named files. The disposable
database remains separately authorized, name-restricted, and exactly cleaned.

### Task 5: Build the test-only Protocol V2 vertical chain

**Files:**

- Create: `phase3/backend/tests/platform_protocol/m1_r1a_synthetic_repair_harness.py`
- Create: `phase3/backend/tests/platform_protocol/m1_r1a_synthetic_repair_verifier.py`
- Create: `phase3/backend/tests/platform_protocol/test_m1_r1a_synthetic_repair.py`
- Create: `phase3/backend/tests/platform_protocol/test_m1_r1a_synthetic_repair_fail_closed.py`
- Modify: `phase3/backend/tests/platform_protocol/conftest.py` only if the disposable database fixture requires it

**Step 1: Write the positive-chain RED test**

Require this exact flow:

```text
OperationRequestV2
-> caller credential
-> pure DMAS selection
-> OperationEnvelopeV2
-> accept_operation
-> ExecutionAttemptV2
-> record_attempt
-> V5 deterministic artifact + executor-signed execution evidence
-> ManifestV2
-> record_execution_evidence_and_manifest
-> ManifestReadGrantV1
-> distinct verifier re-verifies executor evidence and runs oracle
-> IndependentReceiptV2
-> record_receipt
-> outbox claim/ack
-> separate database read-back
```

Assert one operation, attempt, manifest, and receipt; one claim; exact required
audit/outbox events; `accepted/policy_satisfied`; and no network delivery.

Expected: FAIL before the harness exists.

**Step 2: Reuse only source-admitted semantics**

Use current `ProtocolService`, DB-backed identity/key registry, Ed25519
verification, the new source-admitted `ExecutorExecutionEvidenceV1`,
attempt-scoped HMAC rules, protected artifact storage, manifest read grant, and
retry-safe outbox. Do not import code from another worktree or copy a
historical harness without exact source admission.

The executor and verifier must have different principals, releases, private
keys, and public key material. The executor signs execution evidence; the
verifier independently validates it and signs only the receipt. Private keys
and the attempt secret are ephemeral and never persisted or printed.

**Step 3: Keep source mutation outside the chain**

The verifier creates a temporary synthetic fixture, verifies its initial hash,
applies the candidate bytes there, runs the fixed oracle, computes artifact and
manifest hashes, and removes the fixture. No Platform or V5 worktree file is
opened for writing.

**Step 4: Implement honest grounding behavior**

The positive artifact includes the required integrity and scope evidence. A
negative variant without scope evidence must return a bound
`review_required` artifact and an `accepted/policy_satisfied` receipt for that
honest bounded outcome; it must not claim the repair completed.

### Task 6: Prove fail-closed, replay, rollback, and read-back

**Files:**

- Modify: `phase3/backend/tests/platform_protocol/test_m1_r1a_synthetic_repair_fail_closed.py`
- Create: `phase3/backend/tests/platform_protocol/test_m1_r1a_synthetic_repair_cli.py`
- Create after an authorized run: `phase3/backend/docs/evidence/m1-r1a-synthetic-repair-readback-v1.json`

**Step 1: Add the full failure matrix**

Test wrong owner commit/path/hash, runtime admission, caller credential,
zero/multiple DMAS matches, executor identity/release/key, tool policy, lease,
attempt HMAC, capsule, fixture, artifact, executor evidence, manifest, grant
nonce/expiry, verifier identity/release/key/signature, and oracle result. Fixed
cases include `executor_evidence_forged`, artifact substitution, wrong executor
key/release, evidence binding tamper, and evidence replay mismatch.

Assert the exact persistence stage from the design. In particular:

- pre-operation failures write zero rows;
- claim failures add no attempt;
- a two independent PostgreSQL sessions claim race has exactly one winner and
  one `attempt_claim_conflict` loser;
- pre-manifest failures add no executor evidence, manifest, or receipt;
- manifest/grant tamper leaves the last valid state and adds no receipt;
- transaction injection rolls back the complete command; and
- no failure falls back to another executor, database, tool, or runtime.

**Step 2: Prove replay semantics**

Run the exact chain twice against the same disposable database. The second run
must return the original records with zero row, audit, or outbox growth. Change
one request, attempt, manifest, or receipt binding under the same idempotency
identity and require a conflict with the original state unchanged.

**Step 3: Add the deterministic CLI and evidence allowlist**

The CLI accepts only a URL for an explicitly named local disposable database
matching `^nautilus_platform_g1b_[0-9]{14}$`, rejects URL query/options, and
requires the explicit `public` schema to be empty before migration. It neither
creates nor drops any other database.

The evidence file may contain only fixed versions, source commits/blob hashes,
opaque protocol IDs/hashes, row/event counts, expected synthetic outcomes,
replay growth zero, cleanup read-back zero, and `evidence_level=local_r1a`.
It must exclude task source, patch bytes, prompts, dialogue, paths, database
URLs, signatures, secrets, keys, accounts, business data, and FDE data.

**Step 4: Run upgrade, chain, replay, downgrade, and exact cleanup**

Only after explicit database authorization, create one validated database,
run migration upgrade, the chain twice, independent read-back, downgrade,
upgrade determinism, then drop that exact database and read back absence. Do
not use Docker, a legacy database, or production credentials.

### Task 7: Verify frozen commits and request runtime acceptance

**Platform files:** no new implementation files unless a review finding is
first reproduced by a failing test.

**Step 1: Freeze the Platform and V5 full SHAs**

Require clean Platform, V5, and Compass worktrees. Record the exact commit,
path, and blob hashes; do not accept branch names, descendant-only claims, or
conversation summaries.

**Step 2: Run owner reviews in parallel**

Send the same frozen Platform full SHA and V5 owner SHA to:

- V5 for action-boundary review; and
- Compass for grounding/learning-boundary review.

Accept only `ACK` or an evidence-backed `CONFLICT`. Fix High or Medium findings
through a new RED-to-GREEN follow-up commit without amend, then re-run both
reviews against the new same full SHA.

**Step 3: Run fresh Platform gates**

From `phase3/backend`:

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

Also verify one migration head, unchanged Protocol V2 vector hash, unchanged
G1-A evidence, exact source read-back, and no unplanned dependency, migration,
or table. The allowlist is exactly the single forward migration and
`protocol_executor_evidence` table specified in Task 4. Verify disposable
database cleanup zero and absence of prohibited data or network calls.

**Step 4: Stop and request the next user decision**

Completion requires both owner reviews High=0/Medium=0, exact Platform
read-back, all fresh gates passing, and clean worktrees. Report the evidence
and stop. Do not deploy, push, merge, promote Compass experience, modify a real
repository source file, or begin production runtime work.

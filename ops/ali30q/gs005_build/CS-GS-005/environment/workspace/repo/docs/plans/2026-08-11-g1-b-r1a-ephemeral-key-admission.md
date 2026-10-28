# G1-B R1a Ephemeral Executor Key Admission Implementation Plan

> **For Codex:** Execute with TDD in the isolated Platform worktree. Stop before the Task 5 vertical chain.

**Goal:** Source-bind the reviewed V5 ephemeral signer owner commit, verify its Platform-challenged proof of possession, and make the existing R1a service accept only the corresponding short-lived DB-registered public key.

**Baseline:** Platform `61523fb86b406284a18654b8a03900e3523648f4`; V5 `4c18c5a70c16d1d6797f9b71ff96aa58e5a41a67`.

## Task 1: Source-bind the V5 v2 owner contract

**Files:**

- Modify `phase3/backend/platform_protocol/m1_r1a_runtime_admission.py`
- Modify `phase3/backend/docs/evidence/m1-r1a-runtime-admission-v1.json`
- Modify `phase3/backend/tests/platform_protocol/test_m1_r1a_runtime_admission.py`

1. Add RED tests for the exact V5 proposal, path, SHA-256, owner-contract schema, entrypoint, import policy, executor v2 release/key, authorization flags, bindings, and session limits.
2. Add RED cases for the old v1 contract, wrong commit/path/hash, changed entrypoint/import policy, public-key material in the owner contract, extra/duplicate fields, expanded authority, and ancestry-only substitution.
3. Implement only the exact v2 source read-back and contract allowlists. Keep the existing runtime-admission evidence schema and Protocol V2 versions unchanged.
4. Run the runtime-admission and G1-A source-binding regressions.

## Task 2: Add pure Platform challenge and announcement verification

**Files:**

- Create `phase3/backend/platform_protocol/m1_r1a_ephemeral_key_admission.py`
- Create `phase3/backend/tests/platform_protocol/test_m1_r1a_ephemeral_key_admission.py`

1. Write RED tests for canonical Platform challenge creation and exact V5 announcement parsing.
2. Require duplicate/extra rejection, canonical LF bytes, strict UTC and maximum 120-second TTL, exact nonce/hash and challenge hash, fixed executor/release/key/algorithm, valid Ed25519 public material, and PoP verification over canonical signing bytes excluding only `proof_signature`.
3. Return one frozen `R1aEphemeralExecutorAdmissionV1`; accept no private material, raw input, path, prompt, token, account, or free text.
4. Add RED cases for stale/expired/overlong challenges, changed transcript, wrong executor binding, malformed key/signature, invalid proof, replay against another challenge, and a runtime-admission decision other than the exact admitted decision.

## Task 3: Gate registration and every R1a service boundary

**Files:**

- Modify `phase3/backend/platform_protocol/m1_r1a_routing.py`
- Modify `phase3/backend/platform_protocol/service.py`
- Modify `phase3/backend/platform_protocol/__init__.py` only for the new public pure types/functions
- Modify `phase3/backend/tests/platform_protocol/test_m1_r1a_routing.py`
- Modify `phase3/backend/tests/platform_protocol/test_service.py`
- Modify `phase3/backend/tests/platform_protocol/test_m1_r1a_execution_evidence_service.py`
- Create `phase3/backend/tests/platform_protocol/test_m1_r1a_ephemeral_key_service.py`

1. RED: the old fixed public key and v1 release/key are rejected; a valid v2 announcement alone is insufficient until the fixed executor identity/key is registered in the Platform DB.
2. Add the minimum idempotent registration command. It must validate the source-derived admission before inserting the fixed executor identity/public key. Changed material or bindings conflict atomically. Do not store challenge bytes, PoP, private key, attempt secret, or free JSON.
3. Replace static public-key comparisons with exact comparisons against the frozen ephemeral admission. Keep identity/release/key/capability/policy exact.
4. Require `now < admission.expires_at`, operation expiry and attempt lease at or before admission expiry, active unrevoked DB key material equality, and the same admission at issue, claim, and evidence persistence.
5. Prove all invalid paths produce no operation, attempt, executor-evidence, manifest, audit, or outbox growth beyond any separately committed registration rows.
6. Confirm no new model, migration, table, dependency, network call, generic tool, or Protocol V2 vector change.

## Task 4: Verify, review, and commit

From `phase3/backend`, run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_m1_r1a_runtime_admission.py tests/platform_protocol/test_m1_r1a_ephemeral_key_admission.py tests/platform_protocol/test_m1_r1a_routing.py tests/platform_protocol/test_m1_r1a_ephemeral_key_service.py tests/platform_protocol/test_m1_r1a_execution_evidence_service.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
python -m pytest tests/platform_protocol -q --confcutdir=tests/platform_protocol -p no:cacheprovider
python -m ruff check platform_protocol platform_migrations tests/platform_protocol
python -m ruff format --check platform_protocol platform_migrations tests/platform_protocol
python -m compileall -q platform_protocol platform_migrations tests/platform_protocol
```

Also run exact Git-object read-back against the V5 proposal, `git diff --check`, `git show --check`, the frozen Protocol V2/vector hash checks, dependency/network/secret/private-key scans, and an independent code review. Commit only the design, plan, Task 1-3 code/tests, and updated runtime-admission evidence. Do not amend prior commits.

Stop after a clean Platform commit with High=0 and Medium=0. Return to the preserved Task 5 RED only as a separate next step.

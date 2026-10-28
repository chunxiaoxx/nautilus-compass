# G2-A0 CNY 10 V2 Contract Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task by task, with `test-driven-development` for every behavior change.

**Goal:** Add an independent, fail-closed G2-A0 V2 contract with an exact CNY 10 ceiling while leaving the complete V1 contract and behavior unchanged.

**Architecture:** Add a narrow production contract module for V2 policy/request types and a test-only V2 runner/CLI that reuses the already-tested V1 transport and synthetic verification seams. V2 requires its own types, versions, authorization marker, and evidence version. All tests inject HTTPX `MockTransport`; no test reads an environment secret or reaches a socket.

**Tech Stack:** Python 3.12+, dataclasses, HTTPX 0.28.1, pytest, Ruff.

**Fixed baseline:** `af4bf6572ae05fb7f49d3e2ff31e734205b8e976`

**Forbidden:** network, API-key reads, paid completion, database, model execution, new dependency, V1 edits, deployment, push, merge, and FDE.

---

## Task 1: Freeze the additive V2 contract

**Files:**

- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_v2_contracts.py`
- Create: `phase3/backend/platform_protocol/g2_a0_model_gate_v2.py`

### Step 1: Write the failing contract tests

Cover:

- default V2 policy has exact V2 version and `10_000_000` micros CNY;
- V2 policy otherwise equals the fixed V1 capability boundary;
- exact CNY 10 accepts and CNY 10 plus one rejects;
- `bool` is rejected as a cost integer;
- missing, extra, duplicate-key, non-canonical, V1-version, and V1-policy data fail closed;
- V2 request canonical bytes/hash are deterministic;
- V1 and V2 request replay cannot cross versions;
- V1 default canonical bytes remain at their baseline hash.

Run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_g2_a0_model_gate_v2_contracts.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
```

Expected: RED with `ModuleNotFoundError` for `platform_protocol.g2_a0_model_gate_v2`.

### Step 2: Implement the minimum V2 policy and request types

Implement:

- `MODEL_GATE_POLICY_VERSION_V2`
- `MODEL_GATE_REQUEST_VERSION_V2`
- `MAX_COST_MICROS_CNY_V2`
- `DeepSeekModelGatePolicyV2`
- `ModelGateRequestBindingV2`
- `assert_v2_idempotency_replay_matches`

Reuse V1 canonical JSON and validation behavior without changing V1. Require
exact V2 types at the V2 replay boundary.

### Step 3: Run the focused contract tests

Expected: GREEN.

### Step 4: Commit only Task 1 files

```powershell
git add -- phase3/backend/platform_protocol/g2_a0_model_gate_v2.py phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_v2_contracts.py
git diff --cached --check
git commit -m "feat(platform): add G2-A0 CNY 10 v2 contract"
```

## Task 2: Add the inert V2 runner and authorization boundary

**Files:**

- Create: `phase3/backend/tests/platform_protocol/g2_a0_model_gate_v2_cli.py`
- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_v2_cli.py`

### Step 1: Write failing runner tests

Cover:

- exact V2 authorization marker is required;
- V1 marker and near-miss markers fail before transport;
- V2 request is required and V1 request is rejected;
- one injected completion call and two bounded balance reads produce V2 evidence;
- identical replay returns the original result with zero provider-call growth;
- changed replay conflicts before balance or transport;
- exact CNY 10 provider cost and balance delta are accepted;
- either cost at CNY 10 plus one is rejected with `budget_exceeded`;
- missing or malformed balance becomes inconclusive and never retries;
- evidence uses V2 version and canonical bytes;
- a socket-deny guard observes no real network access.

Run the new test file and record the expected import/feature RED.

### Step 2: Implement the minimum V2 runner

Add:

- `G2_A0_PAID_RUN_AUTHORIZATION_V2`
- `MODEL_GATE_EVIDENCE_VERSION_V2`
- `ModelGateEvidenceV2`
- `OfflineModelGateRunnerV2`
- a V2 request builder and injected-transport `execute_probe_v2`

Reuse V1 completion parsing, strict balance parsing, synthetic fixture, verifier,
and HTTPX client. The V2 entry must type-check V2 before delegating. Override
evidence construction so all terminal results are V2. Do not read environment
variables or construct a real transport in tests.

### Step 3: Run focused tests

Expected: GREEN with exactly one mock completion for the positive run and zero
calls for all preflight/replay rejections.

### Step 4: Commit only Task 2 files

```powershell
git add -- phase3/backend/tests/platform_protocol/g2_a0_model_gate_v2_cli.py phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_v2_cli.py
git diff --cached --check
git commit -m "test(platform): add inert G2-A0 v2 runner"
```

## Task 3: Close V2 fail-closed and source-binding gaps

**Files:**

- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_v2_fail_closed.py`
- Modify only if a RED proves necessary: the two new V2 implementation files
- Modify only if actual Git-object read-back proves Windows newline drift:
  `phase3/backend/platform_protocol/.gitattributes`
- Create only under the same proven condition:
  `phase3/backend/tests/platform_protocol/.gitattributes`

### Step 1: Write failing adversarial tests

Cover:

- every V2 policy/request/evidence field rejects an extra field;
- duplicate JSON keys are rejected before last-wins parsing;
- booleans cannot impersonate counters or costs;
- V1 request/evidence/marker cannot enter V2;
- V2 request/evidence/marker cannot enter V1;
- provider model, thinking, retry, fallback, stream, endpoint, prompt, fixture,
  response schema, and call-count tampering fail closed;
- response, reasoning, fingerprint, candidate, balance, and cost tampering fail;
- transport exceptions are redacted and do not trigger a retry;
- evidence contains no API key, authorization header, raw prompt/response,
  reasoning text, source/patch text, path, balance value, or free-form error;
- V2 source read-back is bound to the required V1 and V2 source blobs;
- no environment proxy or plugin can create a network path in the focused run.

Run and capture the RED for each missing guard before implementing it.

### Step 2: Implement only guards proven missing

Keep changes within the two new V2 implementation files. Do not modify V1 to
make V2 tests pass. If actual source read-back fails only because Git blob LF is
checked out as CRLF, add the narrow permanent `text eol=lf` policies listed
above and prove that every affected V1 source blob remains unchanged.

### Step 3: Run all V2 tests

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_g2_a0_model_gate_v2_contracts.py tests/platform_protocol/test_g2_a0_model_gate_v2_cli.py tests/platform_protocol/test_g2_a0_model_gate_v2_fail_closed.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
```

Expected: GREEN.

### Step 4: Commit only Task 3 files

```powershell
git add -- phase3/backend/platform_protocol/g2_a0_model_gate_v2.py phase3/backend/tests/platform_protocol/g2_a0_model_gate_v2_cli.py phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_v2_fail_closed.py
git diff --cached --check
git commit -m "test(platform): harden G2-A0 v2 fail-closed gate"
```

## Task 4: Full verification and independent review

**Files:** No intended changes.

### Step 1: Run the existing V1 regression suite

Run the same five-file baseline command recorded before implementation. It must
remain `228 passed` or increase only if test collection intentionally includes
new files, which this explicit command does not.

### Step 2: Run static gates

From `phase3/backend`:

```powershell
python -m ruff check platform_protocol/g2_a0_model_gate_v2.py tests/platform_protocol/g2_a0_model_gate_v2_cli.py tests/platform_protocol/test_g2_a0_model_gate_v2_contracts.py tests/platform_protocol/test_g2_a0_model_gate_v2_cli.py tests/platform_protocol/test_g2_a0_model_gate_v2_fail_closed.py
python -m ruff format --check platform_protocol/g2_a0_model_gate_v2.py tests/platform_protocol/g2_a0_model_gate_v2_cli.py tests/platform_protocol/test_g2_a0_model_gate_v2_contracts.py tests/platform_protocol/test_g2_a0_model_gate_v2_cli.py tests/platform_protocol/test_g2_a0_model_gate_v2_fail_closed.py
python -m compileall -q platform_protocol tests/platform_protocol
```

Also run targeted scans for secret-shaped literals, environment key reads,
real-network construction/execution, paid invocation, forbidden imports, and
raw evidence fields.

### Step 3: Prove V1 is unchanged

Use `git diff --exit-code` from the fixed baseline across all original G2-A0 V1
source/test paths. Run `git diff --check` and `git show --check` for every new
commit. Confirm the working tree contains only the allowlisted V2/docs files.

### Step 4: Independent read-only review

Freeze the candidate commit and ask an independent reviewer to inspect exact Git
objects, version separation, CNY 10 enforcement, replay, evidence, network/key
absence, and V1 zero-diff. Do not edit while review is running.

If High or Medium findings exist, add a failing regression test, make the
minimum V2-only fix, commit a follow-up without amending, rerun all gates, and
request a fresh narrow review. Completion requires High=0 and Medium=0.

### Step 5: Stop with the branch preserved

Confirm clean status. Do not run the paid probe and do not push or merge. Report
the exact worktree, branch, HEAD, commits, files, RED/GREEN evidence, checks,
review conclusion, and the paid probe as the remaining separately authorized
action.

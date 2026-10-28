# G2-A0 DeepSeek Model Gate Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prove or reject one exact, thinking-enabled `deepseek-v4-flash-0731` call on a deterministic synthetic repair without admitting V5 runtime, fallback, general tools, or source writes.

**Architecture:** Platform defines side-effect-free gate contracts and exact evidence rules. A test-only DeepSeek client uses injected HTTP transport for all offline work and, only after separate approval, may call the two allowlisted official endpoints once; an independent local verifier applies the returned patch only to a disposable fixture and emits a redacted capability receipt.

**Tech Stack:** Python 3.13, frozen dataclasses, canonical JSON, SHA-256, `httpx` 0.28+, `decimal.Decimal`, temporary directories, pytest, Ruff, and Git object read-back.

---

## Execution gates

This plan commit does not authorize implementation or a paid call.

- Tasks 1-4 are offline implementation tasks and require a separate user
  approval against this plan's final full SHA.
- Task 5 is a live, paid network probe. It requires an additional explicit
  approval after Tasks 1-4 are committed, clean, reviewed, and source-read.
- Task 6 may commit only redacted evidence produced by the approved Task 5
  run. It cannot make another model call.

No task may modify V5, Compass, Quantum Buddha, FDE, a real source repository,
or production infrastructure. No task may install a dependency, use an API key
from a tracked file, invoke another model, retry automatically, deploy, push,
or merge.

The implementation worktree must start from design commit
`a7e028a45e14813f11c66106721904994dd73c95`. Each task commits only its listed
files and stops before the next task unless that next task is separately
authorized.

### Task 1: Add pure gate contracts and canonical policy

**Files:**

- Create: `phase3/backend/platform_protocol/g2_a0_model_gate.py`
- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_contracts.py`

**Step 1: Write the contract RED tests**

Define the wished-for immutable policy and result interface:

```python
policy = DeepSeekModelGatePolicyV1.default()

assert policy.provider_origin == "https://api.deepseek.com"
assert policy.requested_model == "deepseek-v4-flash-0731"
assert policy.thinking_type == "enabled"
assert policy.reasoning_effort == "max"
assert policy.max_input_bytes == 24_576
assert policy.max_tokens == 4_096
assert policy.max_provider_calls == 1
assert policy.max_cost_micros_cny == 5_000_000
assert policy.timeout_seconds == 120
assert policy.retry_count == 0
assert policy.fallback_models == ()
```

Add RED tests for:

- exact top-level and nested field allowlists;
- duplicate JSON keys at every depth;
- canonical UTF-8 JSON and stable SHA-256;
- bool rejected where an integer is required;
- any model other than `deepseek-v4-flash-0731`;
- absent/disabled thinking or effort other than `max`;
- a sampling parameter, tool, `tool_choice`, retry, fallback, redirect, proxy,
  streaming, or extra endpoint;
- malformed URLs, non-HTTPS origins, query strings, fragments, or user-info;
- raw API keys, headers, prompts, responses, reasoning, paths, or commands in
  serializable contracts; and
- changed canonical payload under the same idempotency key.

Run from `phase3/backend`:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_g2_a0_model_gate_contracts.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
```

Expected: collection FAIL with
`ModuleNotFoundError: No module named 'platform_protocol.g2_a0_model_gate'`.
A syntax error or broken import in the test is not an acceptable RED.

**Step 2: Implement the minimum pure contracts**

Use frozen, slots-based dataclasses and integer money units:

```python
@dataclass(frozen=True, slots=True)
class DeepSeekModelGatePolicyV1:
    contract_version: str
    provider_origin: str
    balance_path: str
    completion_path: str
    requested_model: str
    thinking_type: str
    reasoning_effort: str
    max_input_bytes: int
    max_tokens: int
    max_provider_calls: int
    max_cost_micros_cny: int
    timeout_seconds: int
    retry_count: int
    fallback_models: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelGateDecisionV1:
    status: Literal["admitted", "rejected", "inconclusive"]
    reason_codes: tuple[str, ...]
    request_hash: str
```

Provide one `canonical_json_bytes` helper that recursively rejects duplicate
keys when parsing bytes and emits sorted, compact JSON with a final LF only
when writing evidence. Keep I/O, HTTP, environment access, fixture bytes, and
provider response bytes out of this module.

Fixed reason codes include at least:

- `model_identity_unproven`;
- `thinking_evidence_missing`;
- `structured_output_invalid`;
- `usage_invalid`;
- `budget_exceeded`;
- `candidate_verification_failed`;
- `idempotency_conflict`;
- `provider_call_ambiguous`; and
- `policy_violation`.

**Step 3: Verify GREEN and generic Protocol compatibility**

```powershell
python -m pytest tests/platform_protocol/test_g2_a0_model_gate_contracts.py tests/platform_protocol/test_contracts.py tests/platform_protocol/test_contract_hardening.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
python -m ruff check --no-cache platform_protocol/g2_a0_model_gate.py tests/platform_protocol/test_g2_a0_model_gate_contracts.py
python -m ruff format --check --no-cache platform_protocol/g2_a0_model_gate.py tests/platform_protocol/test_g2_a0_model_gate_contracts.py
```

Expected: all pass. Protocol V2 conformance vectors and contracts have zero
diff from the design baseline.

**Step 4: Commit only Task 1 files**

```powershell
git add phase3/backend/platform_protocol/g2_a0_model_gate.py phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_contracts.py
git commit -m "feat(platform): define DeepSeek model gate policy"
```

### Task 2: Add the transport-isolated DeepSeek client

**Files:**

- Create: `phase3/backend/tests/platform_protocol/g2_a0_deepseek_client.py`
- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_deepseek_client.py`

**Step 1: Write fake-transport RED tests**

Use `httpx.MockTransport`; do not open a socket. The client interface is:

```python
result = client.complete_once(
    canonical_request=canonical_request,
    api_key="test-only-placeholder",
)

assert result.returned_model == "deepseek-v4-flash-0731"
assert result.reasoning_sha256 == expected_reasoning_hash
assert result.provider_call_count == 1
```

Assert the exact request body contains:

```json
{
  "model": "deepseek-v4-flash-0731",
  "thinking": {"type": "enabled"},
  "reasoning_effort": "max",
  "response_format": {"type": "json_object"},
  "stream": false
}
```

It must not contain temperature, top-p, penalties, tools, `tool_choice`, raw
paths, or user/account identity. The prompt must contain the word `json` and
the exact response example required by DeepSeek JSON Output.

Add injected-response failures for:

- status 301/302/307/308, 400, 401, 402, 422, 429, 500, or 503;
- returned model `deepseek-v4-flash` or any other mismatch;
- missing/empty `system_fingerprint` or `reasoning_content`;
- multiple choices, missing content, wrong finish reason, invalid JSON,
  duplicate keys, or extra output fields;
- bool, negative, missing, or inconsistent usage counts;
- redirects followed, proxy environment inherited, a second HTTP completion,
  or any retry after timeout; and
- exception text containing the API key, Authorization header, raw prompt,
  response, or reasoning.

Run:

```powershell
python -m pytest tests/platform_protocol/test_g2_a0_deepseek_client.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
```

Expected: FAIL because `g2_a0_deepseek_client` does not exist.

**Step 2: Implement the minimum client with injected transport**

Construct the client explicitly:

```python
with httpx.Client(
    base_url="https://api.deepseek.com",
    transport=transport,
    timeout=httpx.Timeout(policy.timeout_seconds),
    follow_redirects=False,
    trust_env=False,
) as http:
    response = http.post("/chat/completions", headers=redacted_auth, json=body)
```

The production header contains the supplied key, but no stored object,
exception, dataclass, log record, or evidence value may retain it. Hash raw
reasoning, content, and fingerprint immediately; return hashes and validated
structured content only. The client makes exactly one completion request per
method call and never catches an error in order to retry.

Price the public V4 Flash snapshot in integer micros CNY per million tokens:

- cache hit input: 20,000 micros CNY;
- cache miss input: 1,000,000 micros CNY; and
- output, including reasoning tokens reported as output: 2,000,000 micros CNY.

Reject unknown usage fields rather than guessing a price.

**Step 3: Verify the client offline**

```powershell
python -m pytest tests/platform_protocol/test_g2_a0_deepseek_client.py tests/platform_protocol/test_g2_a0_model_gate_contracts.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
python -m ruff check --no-cache tests/platform_protocol/g2_a0_deepseek_client.py tests/platform_protocol/test_g2_a0_deepseek_client.py
python -m ruff format --check --no-cache tests/platform_protocol/g2_a0_deepseek_client.py tests/platform_protocol/test_g2_a0_deepseek_client.py
```

Expected: all pass and a socket-deny monkeypatch observes zero real network
attempts.

**Step 4: Commit only Task 2 files**

```powershell
git add phase3/backend/tests/platform_protocol/g2_a0_deepseek_client.py phase3/backend/tests/platform_protocol/test_g2_a0_deepseek_client.py
git commit -m "test(platform): isolate DeepSeek gate transport"
```

### Task 3: Build the disposable synthetic repair verifier

**Files:**

- Create: `phase3/backend/tests/platform_protocol/g2_a0_synthetic_fixture.py`
- Create: `phase3/backend/tests/platform_protocol/g2_a0_synthetic_verifier.py`
- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_synthetic_verifier.py`

**Step 1: Write verifier RED tests**

Create one fixed synthetic Python module with a bounded defect and two disjoint
test surfaces:

- the public prompt describes required behavior and gives one example; and
- the hidden verifier checks all boundaries and invalid input.

The verifier interface is:

```python
verification = verify_candidate_patch(
    fixture=fixture,
    candidate=candidate,
    temp_root=temp_root,
)
assert verification.status == "passed"
assert verification.source_write_count == 0
assert verification.network_call_count == 0
assert verification.fixture_cleanup_count == 1
```

RED cases cover Markdown fences, prose, absolute/UNC/device paths, `..`, NUL,
symlinks, multiple files, rename/delete/create, binary patch, mode changes,
oversized diff, commands, URLs, environment access, subprocess use, network,
modification outside the disposable fixture, malformed hunks, and a plausible
patch that fails a hidden boundary case.

**Step 2: Implement the minimum verifier**

Use only Python standard library parsing and a bounded patch applier owned by
the fixture module. Do not invoke Git, `patch`, shell, PowerShell, or a general
test runner on model-selected input. Import the patched module in an isolated
child process with:

- a fixed interpreter;
- a minimal environment;
- a fixed wall timeout;
- no inherited API key or proxy variables;
- the temporary fixture as the only import root; and
- a hard-coded hidden oracle entrypoint.

The verifier returns hashes, counts, and fixed statuses only. It deletes the
temporary fixture in `finally` and independently confirms the path no longer
exists.

**Step 3: Run GREEN and static scans**

```powershell
python -m pytest tests/platform_protocol/test_g2_a0_synthetic_verifier.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
python -m ruff check --no-cache tests/platform_protocol/g2_a0_synthetic_fixture.py tests/platform_protocol/g2_a0_synthetic_verifier.py tests/platform_protocol/test_g2_a0_synthetic_verifier.py
python -m ruff format --check --no-cache tests/platform_protocol/g2_a0_synthetic_fixture.py tests/platform_protocol/g2_a0_synthetic_verifier.py tests/platform_protocol/test_g2_a0_synthetic_verifier.py
```

Expected: all pass; test monkeypatches prove no external network or source-tree
write.

**Step 4: Commit only Task 3 files**

```powershell
git add phase3/backend/tests/platform_protocol/g2_a0_synthetic_fixture.py phase3/backend/tests/platform_protocol/g2_a0_synthetic_verifier.py phase3/backend/tests/platform_protocol/test_g2_a0_synthetic_verifier.py
git commit -m "test(platform): verify disposable model patch"
```

### Task 4: Add the offline gate runner and evidence validator

**Files:**

- Create: `phase3/backend/tests/platform_protocol/g2_a0_model_gate_cli.py`
- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_cli.py`
- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_fail_closed.py`

**Step 1: Write runner RED tests**

The runner accepts injected balance, completion, and verifier functions. It
must execute this state machine exactly:

```text
NEW -> BALANCE_READ -> CALLING -> VALIDATED -> VERIFIED -> REPLAYED -> COMPLETE
                            \-> REJECTED
                            \-> INCONCLUSIVE
```

Tests prove:

- one canonical request causes one completion call;
- exact replay returns the first validated result with call-count growth zero;
- changed replay conflicts before any balance or completion request;
- a provider exception after entering `CALLING` becomes `inconclusive` and is
  never automatically repeated;
- a rejected response or failed verifier cannot produce admitted evidence;
- balance-before and balance-after are read exactly once each;
- raw balances never enter evidence; only integer delta micros does;
- evidence exact allowlists reject extra fields and bool-as-int; and
- evidence claims are recomputed from source-bound hashes, not accepted from
  caller-provided counts.

**Step 2: Implement the minimum runner**

Keep the replay ledger in memory and explicitly name its limitation. It is
sufficient only for same-process gate replay and must not be exported as a
durable production idempotency mechanism.

Add two CLI modes:

- `--offline-fixture`, used by tests with fake transport; and
- `--live`, which refuses to start unless the exact paid-run authorization
  marker, a non-empty process-only `DEEPSEEK_API_KEY`, and the source-bound
  implementation commit are supplied.

The CLI writes no evidence by default. It emits one redacted canonical JSON
object to stdout; no raw prompt, response, reasoning, patch, balance, path,
header, or environment value may appear.

**Step 3: Run the full offline gate twice**

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/platform_protocol/test_g2_a0_model_gate_contracts.py tests/platform_protocol/test_g2_a0_deepseek_client.py tests/platform_protocol/test_g2_a0_synthetic_verifier.py tests/platform_protocol/test_g2_a0_model_gate_cli.py tests/platform_protocol/test_g2_a0_model_gate_fail_closed.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
python -m pytest tests/platform_protocol/test_g2_a0_model_gate_contracts.py tests/platform_protocol/test_g2_a0_deepseek_client.py tests/platform_protocol/test_g2_a0_synthetic_verifier.py tests/platform_protocol/test_g2_a0_model_gate_cli.py tests/platform_protocol/test_g2_a0_model_gate_fail_closed.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
```

Expected: both runs pass with zero network calls and byte-identical redacted
offline evidence.

Then run:

```powershell
python -m ruff check --no-cache platform_protocol/g2_a0_model_gate.py tests/platform_protocol/g2_a0_*.py tests/platform_protocol/test_g2_a0_*.py
python -m ruff format --check --no-cache platform_protocol/g2_a0_model_gate.py tests/platform_protocol/g2_a0_*.py tests/platform_protocol/test_g2_a0_*.py
python -m compileall -q platform_protocol tests/platform_protocol
git diff --check
```

Scan the exact changed files for keys, Authorization values, proxy inheritance,
fallbacks, retries, shell execution, repository writes, and raw evidence.

**Step 4: Obtain independent offline review and commit**

An independent reviewer reads the staged tree and reports High=0 and Medium=0
for identity, secret, budget, network, patch, evidence, and idempotency
boundaries. Resolve findings through follow-up RED/GREEN commits; do not amend.

```powershell
git add phase3/backend/tests/platform_protocol/g2_a0_model_gate_cli.py phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_cli.py phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_fail_closed.py
git commit -m "test(platform): close offline DeepSeek model gate"
```

Stop and request Task 5 authorization. Report the full implementation SHA,
changed files, exact tests, review result, and the process-only secret
requirement. Do not call DeepSeek.

### Task 5: Run one separately approved paid probe

**Files:** none during the call

**Preconditions:**

- user approval names the exact implementation full SHA;
- worktree is clean and source-read matches that SHA;
- a fresh or independently confirmed non-exposed `DEEPSEEK_API_KEY` is placed
  only in the current process environment by the user/operator;
- the key is not sourced from V5 `.env.bak` or another tracked file;
- no other model or balance-changing workload uses the account during the
  bounded measurement window; and
- the expected maximum completion count is one and maximum cost is CNY 5.

**Step 1: Run preflight without exposing the key**

The CLI checks only that the key is present, never prints its value, reads the
official balance endpoint, and stops before completion if the model policy,
source SHA, balance currency, or budget marker differs.

**Step 2: Make one completion call**

Run the CLI in a single short-lived process with `--live`. No stdout or stderr
may contain the raw prompt, response, reasoning, patch, balance, key, or local
path. The client makes one POST to `/chat/completions` and no other completion
request.

**Step 3: Execute same-process replay and tamper rejection**

The runner replays the same canonical request and proves provider call growth
zero. It then submits a changed model or prompt hash under the same idempotency
key and proves rejection before network I/O.

**Step 4: Read balance and clean temporary state**

Read `/user/balance` once after completion. Verify CNY delta no greater than
5, remove the process key, delete the fixture, and confirm no child process or
temporary directory remains. Do not rerun after a rejection or inconclusive
result.

Expected terminal results:

- `admitted`: exact dated model echoed, thinking present, patch verified,
  budget and replay gates passed;
- `rejected`: a deterministic policy or evidence mismatch; or
- `inconclusive`: timeout, provider ambiguity, balance ambiguity, or crash.

All three are valid evidence outcomes. Only `admitted` can unlock the next
Shadow Coding design discussion.

### Task 6: Commit redacted read-back evidence and stop

**Files:**

- Create: `phase3/backend/docs/evidence/g2-a0-deepseek-model-gate-v1.json`
- Create: `phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_evidence.py`
- Modify: `phase3/backend/platform_protocol/.gitattributes`

**Step 1: Write evidence RED tests**

Bind the evidence to the exact implementation parent commit, every changed
source blob, policy version, fixture/oracle hashes, and live result. Reject:

- extra or missing fields;
- duplicate keys or non-canonical JSON;
- bool counts;
- raw prompt, response, reasoning, patch, balance, key, header, path, account,
  or environment data;
- model requested/returned mismatch hidden by hashes;
- call count other than one or replay growth other than zero; and
- cleanup, verifier, budget, or final decision values not matching the live
  redacted output.

**Step 2: Add canonical evidence and LF policy**

Write only the approved allowlist from the design. Fix this evidence file to
`text eol=lf` in the narrow Platform `.gitattributes`. If the live result is
rejected or inconclusive, record that exact result without editing it into an
admitted claim.

**Step 3: Verify from a fresh process**

```powershell
python -m pytest tests/platform_protocol/test_g2_a0_model_gate_evidence.py tests/platform_protocol/test_g2_a0_model_gate_contracts.py tests/platform_protocol/test_g2_a0_deepseek_client.py tests/platform_protocol/test_g2_a0_synthetic_verifier.py tests/platform_protocol/test_g2_a0_model_gate_cli.py tests/platform_protocol/test_g2_a0_model_gate_fail_closed.py -q --confcutdir=tests/platform_protocol -p no:cacheprovider
python -m ruff check --no-cache platform_protocol/g2_a0_model_gate.py tests/platform_protocol/g2_a0_*.py tests/platform_protocol/test_g2_a0_*.py
python -m ruff format --check --no-cache platform_protocol/g2_a0_model_gate.py tests/platform_protocol/g2_a0_*.py tests/platform_protocol/test_g2_a0_*.py
python -m compileall -q platform_protocol tests/platform_protocol
git check-attr eol -- docs/evidence/g2-a0-deepseek-model-gate-v1.json
git diff --check
git show --check --stat HEAD
```

Expected: all pass, evidence is LF-stable, and the worktree contains only the
allowlisted evidence/test/LF-policy changes.

**Step 4: Independent evidence review and commit**

Require High=0 and Medium=0 from an independent read-only reviewer. Commit the
evidence without amending prior tasks:

```powershell
git add phase3/backend/docs/evidence/g2-a0-deepseek-model-gate-v1.json phase3/backend/tests/platform_protocol/test_g2_a0_model_gate_evidence.py phase3/backend/platform_protocol/.gitattributes
git commit -m "test(platform): record DeepSeek model gate evidence"
```

Confirm clean worktree and stop. Do not begin V5 adapter design, make another
paid call, or expand to a real repository without a new user-approved goal.

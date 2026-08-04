# Compass Learning Kernel R0 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a deterministic offline comparison kernel that proves which combination of memory representation, context-conditioned utility, independent verdicts, and reversible forgetting improves a later mechanically verified action without protected-class regression.

**Architecture:** Add an evaluation-only package under `benchmarks/learning_kernel_r0` that reuses immutable `gep` records and `benchmarks.poi_gate2` hashing, action metrics, and policy gates. It creates hash-bound evaluation views over existing packets, runs fixed selector/intervention matrices, and emits candidate-only evidence; it never writes runtime memory or creates a second ledger.

**Tech Stack:** Python 3.13, frozen dataclasses, canonical JSON/SHA-256 helpers from `benchmarks.poi_gate2`, pytest, Ruff, existing `gep` and PoI-Gate-2 contracts.

---

## Preconditions and Fixed Boundaries

- Work only in `C:\Users\chunx\.config\superpowers\worktrees\nautilus-compass\s4-mainline-convergence`.
- Start from design commit `816df5c` or a reviewed descendant.
- Do not modify Platform, V5, FDE, Feishu, Bitable, deployment, or provider credentials.
- Do not call external models in Tasks 1-8.
- Do not modify `ExperiencePacket` v0 or serving/runtime recall behavior.
- Keep `runtime_recommendation=flat` and `improvement_claim=false` in every R0 artifact.
- Stop on the first failed gate; do not reinterpret missing support as success.

### Task 1: Define Immutable R0 Contracts

**Files:**
- Create: `benchmarks/learning_kernel_r0/__init__.py`
- Create: `benchmarks/learning_kernel_r0/schema.py`
- Test: `tests/learning_kernel_r0/test_schema.py`

**Step 1: Write the failing schema tests**

Cover:

```python
def test_manifest_rejects_unknown_selector(): ...
def test_memory_view_requires_source_packet_hash(): ...
def test_run_result_requires_mechanical_verdict(): ...
def test_runtime_is_always_flat(): ...
def test_unknown_keys_fail_closed(): ...
```

Define exact selector values:

```python
SELECTORS = (
    "flat",
    "semantic",
    "distilled",
    "contextual_utility",
    "current_poi",
    "governed",
)
INTERVENTIONS = (
    "no_memory",
    "raw",
    "distilled",
    "shuffled",
    "stale",
    "contradictory",
    "poisoned",
)
```

Required records:

```python
@dataclass(frozen=True)
class MemoryView:
    view_id: str
    source_packet_hash: str
    route_key: str
    query_class: str
    action_kind: str
    representation: str
    rendered_text: str
    semantic_score: float
    verification_state: str
    verdict: str | None
    lifecycle_state: str
    expires_at: str | None = None

@dataclass(frozen=True)
class LearningRunResult:
    run_id: str
    task_id: str
    query_class: str
    selector: str
    intervention: str
    selected_view_ids: tuple[str, ...]
    success: bool
    first_pass_success: bool
    verifier_code: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    result_hash: str
```

**Step 2: Run tests and verify RED**

Run:

```powershell
python -m pytest tests/learning_kernel_r0/test_schema.py -q
```

Expected: FAIL because `benchmarks.learning_kernel_r0.schema` does not exist.

**Step 3: Implement the minimal immutable contracts**

Use `dataclass(frozen=True, slots=True)`. Parse mappings through explicit
allowlists. Reject booleans where an integer is expected, non-finite scores,
unknown enum values, bare hashes, empty IDs, non-flat runtime recommendations,
and non-false improvement claims.

Use existing `benchmarks.poi_gate2.canonical` helpers; do not create another
canonical JSON implementation.

**Step 4: Run tests and Ruff**

```powershell
python -m pytest tests/learning_kernel_r0/test_schema.py -q
python -m ruff check benchmarks/learning_kernel_r0/schema.py tests/learning_kernel_r0/test_schema.py
```

Expected: PASS.

**Step 5: Commit**

```powershell
git add benchmarks/learning_kernel_r0/__init__.py benchmarks/learning_kernel_r0/schema.py tests/learning_kernel_r0/test_schema.py
git commit -m "feat(learning): define R0 evaluation contracts"
```

### Task 2: Build Hash-Bound Memory Interventions

**Files:**
- Create: `benchmarks/learning_kernel_r0/interventions.py`
- Test: `tests/learning_kernel_r0/test_interventions.py`

**Step 1: Write failing tests**

Test that every intervention:

- preserves source packet immutability;
- returns deterministically ordered views;
- produces a distinct canonical view hash;
- never exposes hidden verifier text or credentials;
- marks poisoned memory as ineligible rather than deleting it;
- maps `no_memory` to an empty tuple;
- swaps context only for `shuffled`;
- marks expiry only for `stale`;
- preserves both incompatible views for `contradictory` so the selector must
  resolve or abstain.

**Step 2: Run tests and verify RED**

```powershell
python -m pytest tests/learning_kernel_r0/test_interventions.py -q
```

**Step 3: Implement pure view construction**

Expose one public function:

```python
def build_memory_views(
    packets: tuple[ExperiencePacket, ...],
    *,
    intervention: str,
    query_class: str,
    now_iso: str,
) -> tuple[MemoryView, ...]:
    ...
```

Use `dataclasses.replace` only on evaluation views, never on source packets.
Derive view IDs and hashes from canonical content. Redact suspicious key names
using the existing packaged-secret boundary vocabulary; do not invent a new
secret store.

**Step 4: Run focused tests and Ruff**

```powershell
python -m pytest tests/learning_kernel_r0/test_interventions.py tests/gep/test_packaged_secret_boundary.py -q
python -m ruff check benchmarks/learning_kernel_r0/interventions.py tests/learning_kernel_r0/test_interventions.py
```

**Step 5: Commit**

```powershell
git add benchmarks/learning_kernel_r0/interventions.py tests/learning_kernel_r0/test_interventions.py
git commit -m "feat(learning): add causal memory interventions"
```

### Task 3: Implement Comparable Selector Policies

**Files:**
- Create: `benchmarks/learning_kernel_r0/selectors.py`
- Create: `benchmarks/learning_kernel_r0/utility.py`
- Test: `tests/learning_kernel_r0/test_selectors.py`
- Test: `tests/learning_kernel_r0/test_utility.py`

**Step 1: Write failing selector tests**

Require a common candidate set and deterministic tie-breaking by `view_id`.
Test:

- `flat` always selects nothing;
- `semantic` orders by semantic score only;
- `distilled` preserves semantic order but renders distilled lessons;
- `current_poi` delegates to `gep.poi_rerank` semantics;
- `contextual_utility` first narrows semantically, then ranks by the exact
  `(route_key, query_class, action_kind)` utility;
- `governed` excludes absent independent verdicts, poisoned/stale views, and
  protected-context mismatches;
- unknown context and missing support fall back exactly to `flat`.

**Step 2: Write failing utility-update tests**

Use an append/rebuild model:

```python
@dataclass(frozen=True, slots=True)
class UtilityObservation:
    context_key: tuple[str, str, str]
    view_id: str
    reward: float
    result_hash: str

def rebuild_utility(
    observations: tuple[UtilityObservation, ...],
) -> Mapping[tuple[str, str, str, str], float]:
    ...
```

The value is the deterministic arithmetic mean of independently verified
rewards for the exact key. Duplicate `result_hash` entries are idempotent.
Unverified rewards are rejected before this function.

**Step 3: Run tests and verify RED**

```powershell
python -m pytest tests/learning_kernel_r0/test_selectors.py tests/learning_kernel_r0/test_utility.py -q
```

**Step 4: Implement the minimal selectors and utility rebuild**

Do not add a database or online learner. The utility mapping is rebuilt from
the frozen run journal for each benchmark invocation.

**Step 5: Run tests and Ruff**

```powershell
python -m pytest tests/learning_kernel_r0/test_selectors.py tests/learning_kernel_r0/test_utility.py tests/gep/test_poi_rerank.py -q
python -m ruff check benchmarks/learning_kernel_r0/selectors.py benchmarks/learning_kernel_r0/utility.py tests/learning_kernel_r0/test_selectors.py tests/learning_kernel_r0/test_utility.py
```

**Step 6: Commit**

```powershell
git add benchmarks/learning_kernel_r0/selectors.py benchmarks/learning_kernel_r0/utility.py tests/learning_kernel_r0/test_selectors.py tests/learning_kernel_r0/test_utility.py
git commit -m "feat(learning): compare contextual memory selectors"
```

### Task 4: Add Reversible Forgetting

**Files:**
- Create: `benchmarks/learning_kernel_r0/forgetting.py`
- Test: `tests/learning_kernel_r0/test_forgetting.py`

**Step 1: Write failing tests**

Test state values `active`, `cooling`, and `archived`. Require:

- source packets remain present and hash-identical;
- verified harm can archive a view;
- low support cools rather than deletes;
- new independent support can restore an archived view;
- protected-class harm cannot be overridden by aggregate benefit;
- an oracle replay computes forgetting regret without changing selection state.

**Step 2: Run tests and verify RED**

```powershell
python -m pytest tests/learning_kernel_r0/test_forgetting.py -q
```

**Step 3: Implement a pure lifecycle reducer**

```python
def reduce_lifecycle(
    current: str,
    *,
    independent_support: int,
    verified_harm: int,
    protected_harm: bool,
    expired: bool,
) -> str:
    ...
```

Keep thresholds in the frozen benchmark manifest, not hidden module globals.

**Step 4: Run tests and Ruff**

```powershell
python -m pytest tests/learning_kernel_r0/test_forgetting.py -q
python -m ruff check benchmarks/learning_kernel_r0/forgetting.py tests/learning_kernel_r0/test_forgetting.py
```

**Step 5: Commit**

```powershell
git add benchmarks/learning_kernel_r0/forgetting.py tests/learning_kernel_r0/test_forgetting.py
git commit -m "feat(learning): add reversible experience forgetting"
```

### Task 5: Run the Frozen Mechanism Matrix

**Files:**
- Create: `benchmarks/learning_kernel_r0/runner.py`
- Create: `benchmarks/learning_kernel_r0/metrics.py`
- Test: `tests/learning_kernel_r0/test_runner.py`
- Test: `tests/learning_kernel_r0/test_metrics.py`

**Step 1: Write failing runner tests**

Use a deterministic fake action executor with a hidden mechanical verifier.
The runner must produce the Cartesian product:

```text
tasks x query classes x selectors x interventions x replicas
```

Require unique IDs, isolated output directories, canonical result hashes,
idempotent read-back, and no access to external providers.

**Step 2: Write failing metric tests**

Reuse `benchmarks.poi_gate2.action_metrics` where possible. Add only:

- raw-versus-distilled delta;
- poison/contradiction rejection rates;
- forgetting regret and recovery rate;
- p50/p95 latency, token totals, and cost;
- per-selector/per-intervention breakdown.

**Step 3: Run tests and verify RED**

```powershell
python -m pytest tests/learning_kernel_r0/test_runner.py tests/learning_kernel_r0/test_metrics.py -q
```

**Step 4: Implement the runner and aggregation**

Inject the executor and verifier as callables. Do not shell out from the runner.
Write JSONL only through the existing canonical JSON discipline and fail if an
output file already contains a conflicting run ID.

**Step 5: Run focused tests and Ruff**

```powershell
python -m pytest tests/learning_kernel_r0/test_runner.py tests/learning_kernel_r0/test_metrics.py tests/poi_gate2/test_action_metrics.py -q
python -m ruff check benchmarks/learning_kernel_r0/runner.py benchmarks/learning_kernel_r0/metrics.py tests/learning_kernel_r0/test_runner.py tests/learning_kernel_r0/test_metrics.py
```

**Step 6: Commit**

```powershell
git add benchmarks/learning_kernel_r0/runner.py benchmarks/learning_kernel_r0/metrics.py tests/learning_kernel_r0/test_runner.py tests/learning_kernel_r0/test_metrics.py
git commit -m "feat(learning): run R0 mechanism matrix"
```

### Task 6: Enforce the Candidate-Only Decision Gate

**Files:**
- Create: `benchmarks/learning_kernel_r0/policy.py`
- Test: `tests/learning_kernel_r0/test_policy.py`

**Step 1: Write failing policy tests**

Test exact outcomes:

- positive delta below permutation p95 -> `flat`;
- any protected delta below `-0.0005` -> `blocked`;
- any admitted poisoned view -> `blocked`;
- missing query-class support -> `flat`;
- reproducibility mismatch -> `blocked`;
- all gates green -> `candidate_only`;
- runtime always remains `flat` and `improvement_claim=false`.

**Step 2: Run tests and verify RED**

```powershell
python -m pytest tests/learning_kernel_r0/test_policy.py -q
```

**Step 3: Implement the pure decision function**

Return reason codes and the exact failing metric. Reuse PoI-Gate-2 protected
gate semantics; do not create a looser threshold.

**Step 4: Run tests and Ruff**

```powershell
python -m pytest tests/learning_kernel_r0/test_policy.py tests/poi_gate2/test_action_runner.py tests/poi_gate2/test_gate_policies.py -q
python -m ruff check benchmarks/learning_kernel_r0/policy.py tests/learning_kernel_r0/test_policy.py
```

**Step 5: Commit**

```powershell
git add benchmarks/learning_kernel_r0/policy.py tests/learning_kernel_r0/test_policy.py
git commit -m "feat(learning): gate R0 policy candidates"
```

### Task 7: Freeze Golden Fixtures and One-Command CLI

**Files:**
- Create: `benchmarks/learning_kernel_r0/cli.py`
- Create: `benchmarks/learning_kernel_r0/__main__.py`
- Create: `benchmarks/learning_kernel_r0/fixtures/r0/manifest.json`
- Create: `benchmarks/learning_kernel_r0/fixtures/r0/tasks.json`
- Create: `benchmarks/learning_kernel_r0/fixtures/r0/experiences.json`
- Create: `benchmarks/learning_kernel_r0/fixtures/r0/verifiers.py`
- Test: `tests/learning_kernel_r0/test_fixture.py`
- Test: `tests/learning_kernel_r0/test_cli.py`

**Step 1: Write failing fixture tests**

Require at least:

- one ordinary task helped by correct distilled experience;
- one protected task where ineligible context must collapse to flat;
- one stale experience;
- one contradictory pair;
- one high-similarity poisoned experience lacking independent verdict;
- one experience whose archive decision creates measurable forgetting regret.

Bind all fixture files and verifier source hashes in the manifest.

**Step 2: Write failing CLI tests**

Support:

```powershell
python -m benchmarks.learning_kernel_r0 dry-run --fixture-dir ...
python -m benchmarks.learning_kernel_r0 run --fixture-dir ... --out ...
python -m benchmarks.learning_kernel_r0 read-back --fixture-dir ... --runs ...
```

`dry-run` must make no writes. `run` refuses a changed manifest. `read-back`
must reproduce all hashes and return a candidate-only decision artifact.

**Step 3: Run tests and verify RED**

```powershell
python -m pytest tests/learning_kernel_r0/test_fixture.py tests/learning_kernel_r0/test_cli.py -q
```

**Step 4: Implement fixtures and CLI**

Keep all fixtures synthetic and free of FDE or personal data. Use no provider
keys. Store run outputs under ignored `outputs/learning_kernel_r0/`.

**Step 5: Run tests and Ruff**

```powershell
python -m pytest tests/learning_kernel_r0/test_fixture.py tests/learning_kernel_r0/test_cli.py -q
python -m ruff check benchmarks/learning_kernel_r0 tests/learning_kernel_r0
```

**Step 6: Commit**

```powershell
git add benchmarks/learning_kernel_r0 tests/learning_kernel_r0/test_fixture.py tests/learning_kernel_r0/test_cli.py
git commit -m "test(learning): freeze R0 mechanism benchmark"
```

### Task 8: Prove Existing Unverified Dogfood Cannot Enter R0

**Files:**
- Create: `benchmarks/learning_kernel_r0/dogfood_projection.py`
- Test: `tests/learning_kernel_r0/test_dogfood_projection.py`
- Create: `docs/evidence/learning_kernel_r0_dogfood_preflight_v1.json`

**Step 1: Write the failing projection test**

Load `docs/evidence/s4_live_agent_dogfood_candidates_v1.json` and assert:

- all three candidates remain visible for audit;
- admitted Stage-A count is exactly zero;
- reason is `blocked_missing_independent_verdict`;
- no reward, impact, capsule, selector, or utility authority is synthesized;
- development/runtime remain flat.

**Step 2: Run test and verify RED**

```powershell
python -m pytest tests/learning_kernel_r0/test_dogfood_projection.py -q
```

**Step 3: Implement the read-only projection and deterministic artifact builder**

The builder may read the committed dogfood file and write only the requested
evidence artifact. It must not modify the source or append to flywheel state.

**Step 4: Generate and verify the artifact**

```powershell
python -m benchmarks.learning_kernel_r0.dogfood_projection --write docs/evidence/learning_kernel_r0_dogfood_preflight_v1.json
python -m pytest tests/learning_kernel_r0/test_dogfood_projection.py -q
git diff --check
```

**Step 5: Commit**

```powershell
git add benchmarks/learning_kernel_r0/dogfood_projection.py tests/learning_kernel_r0/test_dogfood_projection.py docs/evidence/learning_kernel_r0_dogfood_preflight_v1.json
git commit -m "test(learning): bind R0 dogfood admission"
```

### Task 9: Execute Provider-Free R0 and Record the Gate Decision

**Files:**
- Create: `docs/evidence/learning_kernel_r0_protocol_v1.json`
- Create: `docs/evidence/learning_kernel_r0_mechanism_summary_v1.json`
- Test: `tests/learning_kernel_r0/test_committed_evidence.py`

**Step 1: Run the complete frozen matrix**

```powershell
python -m benchmarks.learning_kernel_r0 dry-run --fixture-dir benchmarks/learning_kernel_r0/fixtures/r0
python -m benchmarks.learning_kernel_r0 run --fixture-dir benchmarks/learning_kernel_r0/fixtures/r0 --out outputs/learning_kernel_r0/r0
python -m benchmarks.learning_kernel_r0 read-back --fixture-dir benchmarks/learning_kernel_r0/fixtures/r0 --runs outputs/learning_kernel_r0/r0 --write-summary docs/evidence/learning_kernel_r0_mechanism_summary_v1.json
```

**Step 2: Write committed-evidence tests**

Assert fixture/source hashes, exact matrix counts, complete selector/intervention
coverage, protected-class gates, poison rejection, deterministic rerun hashes,
cost/latency fields, and `runtime_recommendation=flat`.

**Step 3: Generate the protocol artifact**

Record code commit, fixture hashes, commands, Python version, dependency lock
hash, test results, and the candidate-only/flat/blocked decision. Synthetic
mechanism success must not become an improvement claim.

**Step 4: Run the complete local gate**

```powershell
python -m pytest tests/learning_kernel_r0 tests/poi_gate2 tests/gep -q
python -m ruff check benchmarks/learning_kernel_r0 benchmarks/poi_gate2 gep tests/learning_kernel_r0 tests/poi_gate2 tests/gep
git diff --check
```

Expected: all pass; runtime remains flat.

**Step 5: Independent review**

Review only the delta from `816df5c` to the candidate tip. Required review
questions:

- Does any path fabricate an independent verdict?
- Can poisoned, stale, or contradictory experience win silently?
- Does any code mutate runtime state or source packets?
- Are selector comparisons based on the same semantic candidate set?
- Does missing support fall back exactly to flat?

Resolve every High/Medium finding, then rerun Step 4.

**Step 6: Commit**

```powershell
git add docs/evidence/learning_kernel_r0_protocol_v1.json docs/evidence/learning_kernel_r0_mechanism_summary_v1.json tests/learning_kernel_r0/test_committed_evidence.py
git commit -m "test(learning): verify Compass Learning Kernel R0"
```

## Completion and Next Gate

R0 is complete when Tasks 1-9 are committed, the full local gate passes, an
independent review reports no High/Medium findings, and the evidence artifacts
are hash-bound and reproducible.

R0 completion does **not** authorize live providers or runtime promotion. The
next plan may select only mechanisms that survive R0 and run a fresh internal
action delta. A signed Super Agent adapter is designed only after that delta is
positive with no protected-class regression.

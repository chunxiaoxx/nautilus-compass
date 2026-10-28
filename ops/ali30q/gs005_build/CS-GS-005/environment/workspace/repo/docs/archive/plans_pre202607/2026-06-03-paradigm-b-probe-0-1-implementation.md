# Paradigm B Probe 0 + Probe 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the minimal falsifiable apparatus to test whether *clean, isolated,
decomposed context* (Paradigm B division-of-labor) beats a single mixed-context agent
on SWE-bench-Lite — Probe 0 (smoke: arm 1 baseline is sane) then Probe 1 (arm 1 vs
arm 3, matched budget, escape-noise verdict).

**Architecture:** All arms are SWE-bench solvers built on a single scaffold
(`mini-swe-agent`) so the only thing that varies is the context-isolation factor.
Our `LLMClient` (MiniMax-M3 via Anthropic SDK) is plugged in as a duck-typed model.
Patches are scored by the **official `swebench` Docker harness** (external ground
truth) — never a home-grown scorer. The escape-noise statistics (`binom_sign_test`,
`aggregate_multiseed`) are reused from the Phase-3 harness, generalized from
persona-specific keys to arbitrary arm names.

**Tech Stack:** Python 3.13, `datasets`, `anthropic` SDK (M3), `mini-swe-agent`
(MIT, pinned), `swebench` official harness (Docker), pytest.

**Locked design inputs (do NOT re-litigate — see
`docs/plans/2026-06-03-paradigm-b-division-of-labor-probe-design.md`):**
- Dataset: SWE-bench-Lite, core subset = gold patch ≥2 hunks, **N=110**, ids already
  in `phase3/agent-engine/benchmarks/swebench_lite_core_subset.json`.
- Arms (Probe 1 only uses 1 and 3): `1 = mono/generic` (scaffold as-is),
  `3 = decomp/generic` (localize→edit→test sub-agents, each isolated minimal context).
- Fairness: **matched total token budget** per instance across arms (the core confound
  control — "more turns/tokens ≠ clean context").
- Fitness: official harness, `FAIL_TO_PASS` all pass AND `PASS_TO_PASS` no regression.
- Escape-noise gate (conservative): effect counts only if mean > 0 AND every seed
  positive AND paired sign-test p < 0.05. Else "within noise."
- Staging: Probe 0 (smoke ~5) → Probe 1 (arm1 vs arm3 on N=110, matched budget, 1–2
  seeds, M3) → expand to full 2×2 + DeepSeek **only if Probe 1 shows signal**.

**Environment split (read before starting):**
- **Local (Windows, no Docker)** — TDD-able pure logic: Tasks 1, 2, 4, 5, 6, 7.
  All have injected fakes; no LLM call, no Docker.
- **Cloud VM (x86_64, Docker)** — Tasks 3 (install), 8, 9, 10, 11. The agentic loop,
  real M3 calls, repo checkouts, and the swebench Docker eval run here. The design §7
  spike confirmed: 8+ cores / 16 GB / ~120 GB disk / `--cache_level=env` / Lite's 6
  repos. **Never `--cache_level=instance`** (≈2 TB disk). Escape hatch: Modal
  (`--modal true`) or sb-cli.

**Guardrails carried in (anchors):**
- benchmark = proxy, NOT market validation. No wiring V5 RSI / economic loop /
  compass L4 before a real escape-noise signal (#3).
- Reuse the Phase-3 stats + `_chat_safe` pattern (#5); orchestration is the new part.
- Falsifiable on day 1 via Probe 1; do not build the full 4-arm × 2-model apparatus
  before Probe 1 shows signal (#3).
- diverge (build/run) and converge (verdict) stay separate; the gate is mechanical.

---

## Phase A — Prerequisites (local, no Docker)

### Task 1: `LLMClient.chat` per-request timeout

Phase-3 root cause: a hung M3 request deadlocked `ThreadPoolExecutor.map` (seed3 hang).
The Anthropic SDK accepts a per-request `timeout=` on `messages.create`; thread it
through so a hang raises (and `_chat_safe` retries/degrades) instead of blocking forever.

**Files:**
- Modify: `phase3/agent-engine/llm/client.py:41-70` (`chat`) and `:72-101`
  (`chat_with_messages`)
- Test: `phase3/agent-engine/tests/test_llm_client_timeout.py` (create)

**Step 1: Write the failing test** — inject a fake Anthropic client that records the
kwargs passed to `messages.create`, assert `timeout` is forwarded and defaults to
`DEFAULT_TIMEOUT = 180.0`.

```python
# tests/test_llm_client_timeout.py
import types
from llm.client import LLMClient

class _FakeMessages:
    def __init__(self): self.kwargs = None
    def create(self, **kwargs):
        self.kwargs = kwargs
        return types.SimpleNamespace(
            content=[types.SimpleNamespace(type="text", text="ok")]
        )

class _FakeAnthropic:
    def __init__(self): self.messages = _FakeMessages()

def _client_with_fake():
    c = LLMClient(api_key="x")
    c.client = _FakeAnthropic()
    return c

def test_chat_forwards_default_timeout():
    c = _client_with_fake()
    assert c.chat("hi") == "ok"
    assert c.client.messages.kwargs["timeout"] == 180.0

def test_chat_forwards_explicit_timeout():
    c = _client_with_fake()
    c.chat("hi", timeout=30)
    assert c.client.messages.kwargs["timeout"] == 30
```

**Step 2: Run test, verify it fails**

Run: `cd phase3/agent-engine && python -m pytest tests/test_llm_client_timeout.py -v`
Expected: FAIL — `KeyError: 'timeout'` (kwargs has no `timeout`).

**Step 3: Implement** — add a class constant and a `timeout` param to both methods,
forwarded into `kwargs`.

```python
class LLMClient:
    DEFAULT_MODEL = "MiniMax-M3"
    DEFAULT_BASE_URL = "https://api.minimaxi.com/anthropic"
    DEFAULT_TIMEOUT = 180.0  # seconds; a hung request must raise, not deadlock a pool

    def chat(self, prompt, system="", max_tokens=4096, temperature=0.3,
             timeout: float = DEFAULT_TIMEOUT) -> str:
        kwargs = {
            "model": self.model, "max_tokens": max_tokens,
            "temperature": temperature, "timeout": timeout,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        return _extract_text(response)
```
(Mirror the same `timeout` addition in `chat_with_messages`.)

**Step 4: Run test, verify it passes**

Run: `python -m pytest tests/test_llm_client_timeout.py -v`
Expected: PASS (2 passed).

**Step 5: Commit**

```bash
git add phase3/agent-engine/llm/client.py phase3/agent-engine/tests/test_llm_client_timeout.py
git commit -m "fix(llm): per-request timeout on chat to prevent pool deadlock"
```

---

### Task 2: Generalize escape-noise stats into a shared, arm-agnostic module

Phase-3's `aggregate_multiseed` hardcodes `"homogeneous"` / `"persona-diverse"` keys.
Probe 1 compares `arm1` / `arm3`. Extract the stats (DRY) and parametrize the two arm
names so any pair reuses them. Copy the proven logic verbatim from
`.worktrees/phase3-multiseed/phase3/agent-engine/benchmarks/humaneval_consensus_probe.py:263-356`.

**Files:**
- Create: `phase3/agent-engine/benchmarks/escape_noise_stats.py`
- Test: `phase3/agent-engine/benchmarks/test_escape_noise_stats.py`

**Step 1: Write the failing test** — feed two seeds where the "treatment" arm wins a
lopsided item tally; assert `escapes_noise` True; feed a sign-flipping case; assert
False.

```python
from escape_noise_stats import aggregate_paired_multiseed, binom_sign_test

def test_binom_sign_test_no_discordant_is_one():
    assert binom_sign_test(0, 0) == 1.0

def test_escapes_noise_requires_all_positive_and_significant():
    # treatment beats baseline in both seeds, lopsided item tally
    seeds = []
    for _ in range(2):
        base = {f"i{j}": (j % 5 != 0) for j in range(20)}   # 16/20 pass
        trt  = {f"i{j}": (j % 7 != 0) for j in range(20)}   # 17/20 pass, different items
        seeds.append({"baseline": {"pass_at_1": sum(base.values())/20, "items": base},
                      "treatment": {"pass_at_1": sum(trt.values())/20, "items": trt}})
    agg = aggregate_paired_multiseed(seeds, baseline_key="baseline", treatment_key="treatment")
    assert agg["item_level"]["discordant"] > 0
    assert isinstance(agg["escapes_noise"], bool)

def test_sign_flip_does_not_escape():
    s1 = {"baseline": {"pass_at_1": 0.5, "items": {"a": False}},
          "treatment": {"pass_at_1": 0.6, "items": {"a": True}}}
    s2 = {"baseline": {"pass_at_1": 0.6, "items": {"a": True}},
          "treatment": {"pass_at_1": 0.5, "items": {"a": False}}}
    agg = aggregate_paired_multiseed([s1, s2], baseline_key="baseline", treatment_key="treatment")
    assert agg["escapes_noise"] is False  # net sign flips between seeds
```

**Step 2: Run test, verify it fails**

Run: `cd phase3/agent-engine/benchmarks && python -m pytest test_escape_noise_stats.py -v`
Expected: FAIL — `ModuleNotFoundError: escape_noise_stats`.

**Step 3: Implement** — port `binom_sign_test`, `_mean`, `_sample_std` unchanged;
rewrite `aggregate_multiseed` → `aggregate_paired_multiseed(seed_records,
baseline_key, treatment_key)` returning the same dict shape but with generic
`baseline` / `treatment` / `net` sections and the same conservative `escapes_noise`
gate (`net_mean > 0 AND all seeds positive AND sign_p < 0.05`). Keep the anti-
conservative-pooling docstring caveat.

**Step 4: Run test, verify it passes**

Run: `python -m pytest test_escape_noise_stats.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add phase3/agent-engine/benchmarks/escape_noise_stats.py phase3/agent-engine/benchmarks/test_escape_noise_stats.py
git commit -m "feat(bench): arm-agnostic escape-noise stats (reuse Phase-3 logic)"
```

---

### Task 3: Pin and vendor `mini-swe-agent` (cloud VM; spike-confirm its model API)

The scaffold spike (design §7) chose `mini-swe-agent` but the executor must confirm the
*exact* model-plug interface against the pinned version before building arms on it. Do
NOT hardcode an assumed `query()` signature.

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/requirements.txt`
  (pin `mini-swe-agent==<latest>`, `swebench==<latest>`, `datasets`)
- Create: `phase3/agent-engine/benchmarks/swebench/NOTES_scaffold_api.md`

**Steps (runbook, on cloud VM):**
1. `pip install mini-swe-agent swebench` into a fresh venv; record resolved versions
   into `requirements.txt`.
2. Locate the model abstraction: read `mini_swe_agent`'s model module and its SWE-bench
   batch entry point. Write into `NOTES_scaffold_api.md`: (a) the exact method the
   scaffold calls on a model (name + signature + return shape — the spike expects a
   duck-typed `query(messages) -> dict`), (b) how step/cost caps are configured,
   (c) the SWE-bench run command + where it reads the dataset and writes predictions.
3. Confirm a model class can be injected without editing scaffold source (override
   hook / config), so our M3 adapter (Task 8) plugs in cleanly.

**Commit:**
```bash
git add phase3/agent-engine/benchmarks/swebench/requirements.txt phase3/agent-engine/benchmarks/swebench/NOTES_scaffold_api.md
git commit -m "chore(bench): pin mini-swe-agent + swebench, document scaffold model API"
```

> Gate: if step 2 reveals the model interface is NOT cleanly injectable (needs forking
> scaffold source), STOP and report — that changes the arm-isolation argument in §7.

---

### Task 4: Core-subset instance loader

Load the locked N=110 subset from the artifact and join with the HF dataset to get the
fields the solver and harness need (`repo`, `base_commit`, `problem_statement`,
`test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`).

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/subset_loader.py`
- Test: `phase3/agent-engine/benchmarks/swebench/test_subset_loader.py`

**Step 1: Failing test** — with an injected fake dataset (list of dicts) and a tiny
subset-id list, assert the loader returns only subset instances, in subset order, with
the required keys present.

```python
def test_loads_only_subset_ids_in_order(tmp_path):
    fake_rows = [{"instance_id": f"x-{i}", "repo": "r", "base_commit": "c",
                  "problem_statement": "p", "test_patch": "t",
                  "FAIL_TO_PASS": "[]", "PASS_TO_PASS": "[]"} for i in range(5)]
    subset = [{"instance_id": "x-3"}, {"instance_id": "x-1"}]
    rows = load_subset_instances(subset, dataset=fake_rows)
    assert [r["instance_id"] for r in rows] == ["x-3", "x-1"]
    assert {"repo", "base_commit", "problem_statement", "FAIL_TO_PASS"} <= rows[0].keys()
```

**Step 2: fails** (`load_subset_instances` undefined).
**Step 3: implement** — read `swebench_lite_core_subset.json` for ids when no `subset`
passed; default `dataset` = `load_dataset("princeton-nlp/SWE-bench_Lite", split="test")`;
index by `instance_id`; preserve subset order; raise on a missing id.
**Step 4: passes.**
**Step 5: commit** `feat(bench): SWE-bench-Lite core-subset loader`.

---

### Task 5: Prediction JSONL writer

The official harness consumes one JSONL line per instance:
`{instance_id, model_patch, model_name_or_path}`. Pure I/O, unit-testable.

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/predictions.py`
- Test: `phase3/agent-engine/benchmarks/swebench/test_predictions.py`

**Step 1: Failing test** — write 2 predictions, read the file back, assert each line is
valid JSON with exactly the three keys and that an empty patch is preserved (it scores
as unresolved downstream, never dropped).

**Step 2: fails. Step 3: implement** `write_predictions(path, model_name, items)` where
`items = [{"instance_id", "model_patch"}]`; one `json.dumps` per line.
**Step 4: passes. Step 5: commit** `feat(bench): SWE-bench prediction JSONL writer`.

---

### Task 6: Token-budget accountant (matched-budget control)

The headline fairness control. Wrap any model with a counter that sums prompt+completion
tokens and raises `BudgetExceeded` once a per-instance cap is hit, so `mono` and `decomp`
arms are compared at an equal total-token ceiling.

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/budget.py`
- Test: `phase3/agent-engine/benchmarks/swebench/test_budget.py`

**Step 1: Failing test**

```python
from budget import BudgetedModel, BudgetExceeded

class FakeModel:
    def query(self, messages, **kw):
        return {"content": "ok", "usage": {"input_tokens": 100, "output_tokens": 50}}

def test_counts_tokens_and_raises_at_cap():
    m = BudgetedModel(FakeModel(), max_total_tokens=300)
    m.query([{"role": "user", "content": "a"}])   # 150
    m.query([{"role": "user", "content": "b"}])    # 300 total -> at cap
    assert m.spent == 300
    import pytest
    with pytest.raises(BudgetExceeded):
        m.query([{"role": "user", "content": "c"}])  # would exceed
```

**Step 2: fails. Step 3: implement** — `BudgetedModel` proxies `query`, reads `usage`
from the return dict (fallback: a `tiktoken`/char-based estimate if usage absent —
document the estimate path), accumulates `self.spent`, raises before a call that would
cross `max_total_tokens`. **Step 4: passes. Step 5: commit**
`feat(bench): per-instance token-budget accountant for matched-budget arms`.

> Design note (carry into Task 9/10): native mini-swe-agent caps are steps/$, not
> tokens (design §7). This accountant is the small `query()` extension that gives a
> strict **token** match. The headline Probe-1 number uses the token-matched cap; a
> natural-budget run (no cap) is reported alongside.

---

### Task 7: M3/DeepSeek model adapter (duck-typed `query`)

Adapt our `LLMClient` to whatever method name Task 3 confirmed the scaffold calls
(spike expects `query(messages) -> {"content": str, "usage": {...}}`). Reuse the
Phase-3 `_chat_safe` retry/degrade pattern; honor the new per-request timeout (Task 1).

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/model_adapter.py`
- Test: `phase3/agent-engine/benchmarks/swebench/test_model_adapter.py`

**Step 1: Failing test** — inject a fake `LLMClient` (records prompts, returns canned
text); assert the adapter maps a `messages` list to a single prompt+system, returns the
scaffold's expected dict shape, and that a raising fake degrades to a safe value after
retries (no exception bubbles).

**Step 2: fails. Step 3: implement** `M3Model(llm=None, model_name="MiniMax-M3",
max_tokens=16000, temperature=0.0)`: flatten `messages` (system → `system`, rest →
`chat_with_messages` if multi-turn else `chat`), wrap in `_chat_safe`-style backoff,
return `{"content": text, "usage": {...}}` (usage from response if exposed, else
estimate). `model_name_or_path` defaults to `self.model_name`.
**Step 4: passes. Step 5: commit** `feat(bench): M3 model adapter for mini-swe-agent`.

---

## Phase B — Probe 0 smoke (cloud VM, Docker)

> Goal: confirm arm 1 (mono/generic) produces real patches and a **sane** resolve rate
> on ~5 instances — the SWE-bench analog of Phase-2's "single = 76.8% is sane"
> self-check. Establishes our own Lite baseline (no citable Lite number exists, §7).

### Task 8: arm 1 runner (mono/generic) wired to M3 + budget

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/run_arm.py`
- Test: `phase3/agent-engine/benchmarks/swebench/test_run_arm.py` (fakes only — no
  Docker, runs local)

**Step 1: Failing test (local, fake scaffold + fake model)** — `run_arm("mono", model,
instances, solver=fake_solver)` returns one prediction per instance with keys
`{instance_id, model_patch}`, in order, and a failing solver yields an empty patch (not
a crash). Concurrency via `ThreadPoolExecutor` (mirror Phase-3 `run_codegen_arm`).

**Step 2: fails. Step 3: implement** `run_arm(arm, model, instances, solver,
max_workers)` where `solver(instance, model) -> patch_str`; for `mono`/`generic` the
solver invokes the mini-swe-agent SWE-bench solve for one instance (checkout at
`base_commit`, feed `problem_statement`, run agent loop under the budgeted model, return
the diff). Wrap each item so an exception → empty patch + logged. **Step 4: passes.
Step 5: commit** `feat(bench): arm runner (mono/generic) over M3 + budget`.

### Task 9: Probe 0 driver + official harness eval (cloud runbook)

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/probe0_smoke.py`
- Create: `phase3/agent-engine/benchmarks/swebench/RUNBOOK_cloud.md`

**Steps:**
1. `probe0_smoke.py`: load first 5 ids of the core subset (Task 4) → `run_arm("mono",
   M3Model(...), instances)` (Task 8) → `write_predictions(...)` (Task 5) to
   `preds_probe0.jsonl`.
2. RUNBOOK: the exact cloud eval command —
   ```
   python -m swebench.harness.run_evaluation \
     --predictions_path preds_probe0.jsonl \
     --dataset_name princeton-nlp/SWE-bench_Lite \
     --max_workers 4 --run_id probe0 --cache_level env --clean true
   ```
   plus the disk/VM preconditions from design §7 and the Modal escape hatch.
3. Run it; record `resolved` count + the report json path.

**Verify (not "complete" until checked — verification-mandatory):** at least a
non-trivial fraction of 5 resolved AND every prediction line is well-formed AND no
Docker disk blow-up. A 0/5 with well-formed empty patches means the agent/model wiring
is broken (debug before Probe 1); a sane >0/5 unblocks Probe 1.

**Commit:** `feat(bench): Probe 0 smoke driver + cloud eval runbook` (commit the driver
+ runbook + the result json).

---

## Phase C — Probe 1: arm 1 vs arm 3 (cloud VM)

> The cheapest direct test of the user's core claim: *does clean isolated decomposed
> context alone beat a single mixed-context agent, at matched budget?* If arm 3 fails to
> beat arm 1 here, the Paradigm-B context claim is in trouble and we save the full-2×2
> cost (design §6).

### Task 10: arm 3 decomp orchestrator (localize → edit → test, isolated context)

The new orchestration logic (Agentless pipeline as *design reference* only, §7). Each
sub-agent gets a curated minimal context + a structured handoff, NOT the others' full
transcripts. Generic toolset (same tools as arm 1 — the `generic` factor level), so the
ONLY difference vs arm 1 is context partitioning.

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/decomp_solver.py`
- Test: `phase3/agent-engine/benchmarks/swebench/test_decomp_solver.py` (fakes only)

**Step 1: Failing test (fake model returning scripted stage outputs)** — assert the
solver runs three stages in order; assert **each stage's prompt does NOT contain the
previous stage's full transcript** (only the structured handoff fields); assert the
budgeted model is shared so the total token cap spans all three stages; assert a stage
returning empty degrades to an empty final patch.

```python
def test_stages_isolated_and_budget_shared():
    calls = []
    class FakeModel:
        spent = 0
        def query(self, messages, **kw):
            calls.append(messages)
            return {"content": SCRIPT.pop(0), "usage": {"input_tokens": 10, "output_tokens": 10}}
    solve_decomp(instance, FakeModel())
    # localize handoff -> edit: edit prompt must reference the located file,
    # but NOT the localizer's raw exploration transcript
    edit_prompt = render(calls[1])
    assert "located_file" in edit_prompt
    assert LOCALIZER_RAW_TRANSCRIPT not in edit_prompt
```

**Step 2: fails. Step 3: implement** `solve_decomp(instance, model, tools)`: stage 1
localizer (repo map / grep → returns `{files, hunneeded_context}`); stage 2 editor
(receives only located file + issue → returns edit/patch); stage 3 tester (runs tests,
returns pass/fail + minimal failure context; on fail, ONE bounded repair handoff back to
editor). Each stage = a fresh message list seeded only with its structured handoff.
Return the final diff. **Step 4: passes. Step 5: commit**
`feat(bench): arm-3 decomposed solver with isolated per-stage context`.

> Operationalization gate (design §2 arm-2 risk analog): the executor MUST confirm in
> the test that arm 3 differs from arm 1 *only* by context partitioning — same tools,
> same model, same total budget. If arm 3 ends up with extra tools or more budget, the
> context factor is confounded — STOP and fix the spec.

### Task 11: Probe 1 driver — matched budget, 1–2 seeds, escape-noise verdict

**Files:**
- Create: `phase3/agent-engine/benchmarks/swebench/probe1_arm1_vs_arm3.py`

**Steps:**
1. Load the full N=110 core subset (Task 4).
2. For each seed (1–2) on M3, run `arm1` and `arm3` over the subset, **each under the
   same per-instance `BudgetedModel` cap** (Task 6). Stream predictions to disk after
   each arm (Phase-3 partial-run safety).
3. Eval both via the official harness (Task 9 RUNBOOK command, distinct `--run_id`s) →
   per-instance resolved booleans.
4. Build `seed_records = [{"baseline": {pass_at_1, items}, "treatment": {pass_at_1,
   items}}, ...]` and call `aggregate_paired_multiseed(..., baseline_key="baseline",
   treatment_key="treatment")` (Task 2). Print the same summary block as the Phase-3
   probe (per-seed net, item-level win tally, sign-test p, `escapes_noise`).
5. Report BOTH the matched-budget figure (headline) and a natural-budget figure.

**Verify (verification-mandatory):** the verdict line is `escapes_noise: True/False`
from real harness scores on N=110. Do not call Paradigm B confirmed/refuted on a single
seed or a 1-instance swing — the conservative gate (mean>0 AND all seeds positive AND
sign p<0.05) is the bar, same as Phase 3.

**Commit:** `feat(bench): Probe 1 arm1-vs-arm3 driver + escape-noise verdict`
(commit driver + result json + a short `PROBE1_RESULT.md` honest write-up).

---

## Decision gate after Probe 1 (do this, don't auto-expand)

- **`escapes_noise: True` on M3** → write the result memory, then plan the full 2×2 +
  multi-seed + DeepSeek replication (still proxy — anchor #3: no V5/economic/compass
  wiring yet; the cross-lab replication is the next falsification, not a ship signal).
- **`escapes_noise: False`** → record the negative result (like Phase-3 persona moat).
  The Paradigm-B *context-isolation* claim did not survive the cheapest test on Lite;
  candidates before abandoning: multi-file dataset (Verified, 71 instances — design §10)
  where decomposition has more to bite on, or the tool-specialization factor (arms 2/4).
  User decides direction — do not silently keep iterating.

## Reuse / provenance notes

- `binom_sign_test` / `_mean` / `_sample_std` / aggregation logic: ported from
  `.worktrees/phase3-multiseed/.../humaneval_consensus_probe.py:263-356` (Phase-3,
  Paradigm A — CLOSED). Generalized in Task 2.
- `_chat_safe` retry/degrade + `ThreadPoolExecutor` concurrency: same file, lines
  364-457. Reused conceptually in Tasks 7/8.
- Subset artifact + counter: `swebench_lite_core_subset.json` /
  `swebench_lite_subset_count.py` (committed `8c563554d`).
- Official harness is the scorer — NOT the Phase-3 subprocess `run_program` (that was
  HumanEval-specific; SWE-bench needs repo checkout + Docker).

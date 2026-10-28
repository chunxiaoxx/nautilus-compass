# Probe 3 — soul-fitness evolution: does an agent improve over cycles on external benchmark?

> **For Claude:** REQUIRED SUB-SKILL: superpowers:executing-plans to implement task-by-task.
> 2026-06-04 · platform-soul · the recursive-self-improvement thesis (anchor #2), made falsifiable.
> Resolves the open questions in `2026-06-03-benchmark-as-soul-fitness-design.md` §5.

**Goal:** Test whether a soul that self-modifies the agent and is selected by an
EXTERNAL benchmark resolve-rate measurably improves the agent over N cycles — or
whether it stays flat (thesis fails). This is the keystone the whole 6/1 pivot built
toward; the ruler (Probe 0/1) is now validated, so this is testable.

**Architecture:** each cycle: proposer (LLM) reads the current agent prompt + a sample
of its failures → proposes a prompt edit → the modified agent runs the held-out probe
set via the proven container-eval harness → fitness_delta = resolve-rate(candidate) −
resolve-rate(current-best), paired + escape-noise → accept the edit iff the gate
passes; the accepted prompt becomes the new best. After N cycles, the real verdict is
the trend on a SEPARATE held-out VALIDATION set the loop never trains against.

**Tech Stack:** reuses `probe1_runner.py` (agent run) + the container swebench harness
(scoring) + `escape_noise_stats.py` (gate) + M3 via litellm route A.

---

## Resolved design decisions (from design §5 open questions)

| Question | Decision (minimal falsifiable) |
|---|---|
| What does the soul self-modify? | The **agent's system+instance prompt** (mini-swe-agent swebench.yaml agent block). Highest-leverage, no infra risk. (scaffold/tools/routing = later.) |
| The cycle | propose prompt edit → run modified agent on FIXED probe set → fitness_delta vs current-best → accept iff escape-noise positive |
| Probe vs validation (anti-Goodhart) | **FIXED probe set** (the N=15 instances) for per-cycle scoring + a **separate held-out VALIDATION set** (10–15 NEW instances) the loop never sees. Verdict = validation-set trend, not probe-set. |
| Baseline drift | candidate vs **current-best** (not frozen); accepted prompt becomes new best |
| Search operator | LLM-authored prompt edit (M3): "here is the agent prompt + K failed instances + their errors → propose a prompt change to fix more". 1 proposal/cycle (best-of-K later) |
| Falsifiable metric | resolve-rate on held-out VALIDATION set after N cycles: up (real improvement) vs flat (thesis fails) |

**The two confounds this controls (honesty):**
1. **Goodhart**: the loop WILL overfit the probe set → only the held-out validation
   trend counts as "improvement".
2. **Proposer luck**: a single accepted edit could be noise → each cycle's acceptance
   is gated by escape-noise on the probe set, and the validation trend must hold.

---

## Phase A — pure-logic loop (local, TDD, no compute)

### Task 1: cycle state + selection rule
**Files:** Create `swebench_probe/evolution.py` · Test `test_evolution.py`
- `EvolutionState(best_prompt, best_score, history)` + `consider_candidate(state, cand_prompt, cand_items, base_items) -> (accepted: bool, new_state)`.
- accept iff `aggregate_paired_multiseed([{base,cand}], "base","cand")["escapes_noise"]` is True AND cand mean > best mean. (reuse the gate.)
- TDD: accepted when candidate lopsided-better; rejected when within noise; best updates only on accept.

### Task 2: proposer prompt builder (pure)
**Files:** `swebench_probe/proposer.py` · `test_proposer.py`
- `build_proposer_prompt(current_agent_prompt, failed_instances) -> str` — frames the current prompt + K failures (instance + error) and asks for a single improved prompt, returned in a fenced block.
- `extract_proposed_prompt(llm_output) -> str` — parse the fenced block; "" on miss (rejected).
- TDD: pure framing + extraction with fakes.

### Task 3: one-cycle orchestrator (injected runner+scorer+proposer)
**Files:** `swebench_probe/evolve_cycle.py` · `test_evolve_cycle.py`
- `run_cycle(state, probe_instances, *, propose_fn, run_agent_fn, score_fn) -> new_state` — propose → run modified agent on probe set → score → consider_candidate.
- All deps injected → unit-test the orchestration with fakes (no LLM/Docker). Empty proposal → no-op cycle.

---

## Phase B — compute run (cloud-container, fresh session)

### Task 4: held-out validation set + probe set freeze
- Pick the N=15 probe instances (already run) as the FIXED probe set; pick 10–15 NEW
  subset instances (never used) as the held-out validation set. Pre-pull images.

### Task 5: real proposer + real agent-run wiring
- `propose_fn` = M3 call (route A) with the proposer prompt.
- `run_agent_fn` = `probe1_runner` arm1 with the candidate prompt injected (override the
  swebench.yaml agent block).
- `score_fn` = container swebench harness → resolve booleans.

### Task 6: N-cycle run + validation verdict
- Run N cycles (start N=3–5) on the probe set; after each accept, score the new best on
  the **held-out validation set** (cheap, only on accepts).
- **Verdict:** validation resolve-rate at cycle 0 vs cycle N. Up beyond noise =
  recursive self-improvement works. Flat = thesis fails (honest, valuable).
- Compute: each cycle ≈ 1 probe-set agent run (~75 min for 15 instances) + 1 proposer
  call. N=3–5 = several hours → fresh session, /loop or /goal.

---

## Falsifiable outcomes (do not over-claim)

- **Validation trend UP, escapes noise** → recursive self-improvement on external truth
  WORKS. The platform has a demonstrated value (self-improving agent). THEN consider
  wiring to the live soul executor (gated, draft-PR, never auto-merge — outbound #17).
- **Validation FLAT / within noise** → the recursive thesis is also weak under honest
  measurement (like Paradigm A/B). Record the negative; the ruler still has standalone
  value (external eval). Candidates: richer self-mod target (scaffold not just prompt),
  or harder/heterogeneous tasks (Probe 2 specialization).
- Either way the apparatus answers the keystone question with external ground truth.

## Guardrails
- Validation set held out — the loop NEVER scores on it during selection (anti-Goodhart).
- escape-noise gate per cycle (no single-edit over-claim).
- No wiring to live soul/V5 before a positive validation verdict (anchor #3; consistent
  with outbound #17 to V5 — external fitness first).
- Phase A is local TDD; Phase B compute is fresh-session (don't rush the keystone).

## Relations
- `2026-06-03-benchmark-as-soul-fitness-design.md` (the design this concretizes)
- `2026-06-03-probe1-result.md` (the ruler, validated) · `2026-06-04-platform-value-...-memo.md` (§4-A)
- `session_20260604_outbound17_v5_economic_darwin_godel_gates.md` (same stance to V5)

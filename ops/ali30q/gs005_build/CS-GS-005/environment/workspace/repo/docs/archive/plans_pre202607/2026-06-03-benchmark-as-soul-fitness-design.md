# Design draft — benchmark-as-soul-fitness: wiring external selection pressure into the recursive self-improvement loop

> 2026-06-03 · platform-soul dialog · DESIGN DRAFT, not a build green-light.
> **Hard gate: nothing here is built until Probe 1 proves the benchmark discriminates
> (an arm-difference that escapes noise). A ruler that can't tell arm1 from arm3
> cannot tell a good self-modification from a bad one.**

## 0. The trap this exists to break

The recursive self-improvement loop has failed 5–6 times
(`design_20260601_external_selection_pressure_benchmark_loop`). Root cause, confirmed
three ways:
- `design_20260601`: fitness was all self-referential (composite_score ≡ 0, NAU
  self-minted, sandbox 0 runs).
- `observation_20260602`: the platform is a self-referential economy — tool calls,
  bounties, NAU all thrive internally while **external value = 0**.
- This session: the executor **check-stage is hollow** (approve → `checks:[]` → 0 PRs).

**More autonomy (/loop, cron, event bus, consumer loops) on a self-referential
fitness just spins the loop faster — it is not improvement.** Today's V5 and compass
inbounds both asked to build more internal-loop plumbing; both were declined on this
exact ground (anchor #3). The fix is not a better goal/loop mechanism — the mechanism
(systemd timers, /loop, cron) already exists and is not the bottleneck. **The
bottleneck is the fitness signal.**

## 1. The core wiring (one sentence)

Replace the soul self-modification cycle's fitness — currently the hollow internal
check-stage / composite_score / NAU — with **"did this self-modification raise the
agent's resolve rate on an external held-out benchmark?"**

```
soul cycle proposes a self-modification (see §5: what exactly?)
  -> apply it to a candidate agent version
  -> run the candidate on a held-out benchmark probe set (official swebench harness)
  -> fitness_delta = resolve_rate(candidate) - resolve_rate(baseline)   [external GT]
  -> the cycle survives / propagates / mints reward IFF fitness_delta escapes noise
```

This is the SAME apparatus proven today (Probe 0/1: agent → patch → official harness →
externally-verified resolve verdict). The recursive loop becomes real the moment a
cycle's survival depends on **moving an external number it cannot fake**.

## 2. What it changes structurally

- **check-stage** (today: empty) → run the benchmark on the proposed change. Real
  external scoring replaces the hollow self-check that produces 0 PRs.
- **NAU / reward** minted ONLY on positive external `fitness_delta`, never on
  self-evaluation. This directly kills the self-minting documented in
  `observation_20260602`.
- **survival / selection** (the automaton's pressure) is tied to an external,
  falsifiable measure — the definition of external selection pressure the 6/1 pivot
  locked.

## 3. The hard gating (so we do not repeat the trap)

1. **Pre-req — the ruler must discriminate.** Probe 1 (arm1 vs arm3) must show an
   arm-difference that escapes noise. If the benchmark is too saturated or too noisy
   to separate two real designs, it cannot separate a good self-mod from a bad one.
   *Fix the ruler before wiring it to anything.* (This is why Probe 1 comes first.)
2. **Pre-req — the fitness must be cheap per cycle.** A full 110-instance × 2-arm run
   is hours; a self-improvement loop needs fast feedback. → a small rotating
   **fitness probe set** (~10–20 held-out instances) per cycle, with periodic
   full-set validation to catch overfit.
3. **Pre-req — anti-Goodhart / held-out.** The soul WILL overfit to whatever
   instances it is scored on. Need a rotating held-out probe set + a final unseen
   validation set the loop never trains against, else it memorizes the probe instead
   of improving. Cross-model (M3 + DeepSeek) to avoid overfitting one model's quirks.

## 4. Minimal first wiring (don't build the full automaton)

- `fitness_from_benchmark(candidate) -> delta`: apply the candidate change → run the
  N-instance probe set in the proven container-eval harness → return resolve-rate
  delta vs baseline (reuse `probe1_runner.py` + the official harness path).
- Wire it as the executor's check-stage replacement (the 'check' that is currently
  hollow), gated by the Phase-3 escape-noise apparatus
  (`aggregate_paired_multiseed`).
- Mint reward / mark the cycle "shipped" ONLY on a positive escape-noise delta.

## 5. Open questions (decide before building — brainstorming, not settled)

- **What does the soul actually self-modify?** The agent scaffold? the prompts? the
  model routing? the decomp structure (arm3)? This determines what the benchmark
  measures and how big the search space is. (Strong candidate: the agent's
  prompt/scaffold, since that's what the benchmark already varies.)
- **Probe-set size vs cost vs overfit.** 10–20 instances per cycle? rotation policy?
- **Baseline drift.** As the agent improves, the baseline must move with it (compare
  candidate vs current-best, not vs a frozen old baseline).
- **Search operator.** How does a cycle propose a self-mod — LLM-authored diff?
  mutation of prompts? This is the "variation" half of variation+selection.

## 6. Sequencing (strict — each step gated on the prior)

- **Step 0 (NOW, in progress):** Probe 1 — prove the ruler discriminates. *No wiring
  before this.* If Probe 1 shows no signal, the ruler needs work (harder dataset,
  multi-file Verified, etc.) before it can be a fitness at all.
- **Step 1:** if Probe 1 signal → build `fitness_from_benchmark` on a small probe set.
- **Step 2:** replace the soul check-stage with it; mint only on positive external
  delta; keep NAU/internal metrics as observability, NOT as selection.
- **Step 3:** let the existing timer/loop run the cycle continuously. *Now* the
  continuous run is a genuine recursive self-improvement engine — each cycle survives
  only by moving an external number.

## 7. The honest one-liner

You already chose the right thing (6/1 pivot: build the external ruler = benchmark
loop). The answer to "how to truly guide soul+agent into the recursive loop" is NOT a
better /goal or /loop — it is: **make the loop's fitness external and falsifiable,
then let the timers run.** Order is non-negotiable: ruler first (Probe 1), wiring
second, autonomy last.

## Relations
- `design_20260601_external_selection_pressure_benchmark_loop` (direction source)
- `observation_20260602_platform_self_referential_economy_3layer` (the trap, hard data)
- `session_20260603_phase4_subset_locked_plan_timeout_done` §6–8 (Probe 0 done, Probe 1
  apparatus proven — the ruler being built)
- `session_20260603_outbound16_v5_...` / `..._compass_outcome_fuel_...` (same stance
  applied to V5/compass: declined internal-loop plumbing pending external signal)

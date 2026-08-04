# Compass C2 Live-Agent Causal A/B Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task by task. Use `test-driven-development` for every behavior change.

**Goal:** Produce a replayable, provider-stratified causal A/B result for Compass memory/path intervention while preserving `flat`, `candidate_only`, and `improvement_claim=false` unless every promotion gate passes.

**Architecture:** Keep the existing Learning Kernel R0 and append-only flywheel journal as the authority. Add a thin `benchmarks.live_agent_c2` adapter-and-evidence layer around them: frozen deidentified tasks, isolated provider invocations, deterministic verification, paired randomization, strict episode evidence, and a fail-closed policy gate. Never use provider self-judgment, runtime release slots, or raw response logs as verdict authority.

**Tech Stack:** Python 3.9+, pytest, PyNaCl, subprocess-based isolated CLIs, optional OpenAI-compatible HTTP adapter, Ruff, existing `gep` and `benchmarks.learning_kernel_r0` modules.

---

## Task 1: Repair the two canonical contract mismatches

**Files:**
- Modify: `release_manifest.py`
- Modify: `benchmarks/learning_kernel_r0/utility.py`
- Modify: `tests/release/test_release_manifest.py`
- Modify: `tests/learning_kernel_r0/test_utility.py`

1. Add a failing release-manifest test requiring `compass.verdict_packet.v0`.
2. Add failing utility tests that provide distinct `episode_event_hash` and `result_hash`, require both to be validated, and reject either mismatch.
3. Run the focused tests and record the expected failures.
4. Change the release schema constant to the canonical verdict schema.
5. Add an explicit `episode_event_hash` field to `UtilityObservation`; bind the verdict to it while retaining `result_hash` as the unique result/evidence key.
6. Run focused tests, existing Learning Kernel tests, and Ruff on touched files.
7. Commit only these files as `fix(c2): align verdict and utility hash contracts` and push the checkpoint.

## Task 2: Freeze the C2 task and evidence schemas

**Files:**
- Create: `benchmarks/live_agent_c2/__init__.py`
- Create: `benchmarks/live_agent_c2/schema.py`
- Create: `benchmarks/live_agent_c2/task_pack.py`
- Create: `benchmarks/live_agent_c2/fixtures/c2/task_pack.json`
- Create: `tests/live_agent_c2/test_schema.py`
- Create: `tests/live_agent_c2/test_task_pack.py`
- Modify: `pyproject.toml`

1. Write failing tests for exact-key parsing, canonical JSON/hashes, duplicate IDs, unknown query classes, unsafe/raw identity fields, missing protected class, and deterministic pack order.
2. Define immutable `LiveTask`, `ProviderIdentity`, `AttemptEvidence`, `PairedEpisode`, and `C2TaskPack` records with strict validation.
3. Freeze the query classes: `episodic_lookup`, `procedural_route`, `conflict_resolution`, and `protected_noop`.
4. Build a deidentified task pack with hidden deterministic verifier inputs and no provider-specific wording.
5. Package only the task fixture; never package raw provider output.
6. Run focused tests and Ruff.
7. Commit as `feat(c2): freeze live A/B task and evidence schemas` and push.

## Task 3: Add deterministic verification and isolated provider boundaries

**Files:**
- Create: `benchmarks/live_agent_c2/verifier.py`
- Create: `benchmarks/live_agent_c2/providers.py`
- Create: `tests/live_agent_c2/test_verifier.py`
- Create: `tests/live_agent_c2/test_providers.py`

1. Write failing tests for exact-answer/set/ordered-step verifiers, malformed output, prompt injection text, timeout, non-zero exit, oversized output, unknown model identity, and credential redaction.
2. Implement deterministic verifier strategies whose policy and evidence are hash-bound.
3. Define a strict provider protocol and a subprocess CLI adapter with fresh session, isolated temporary cwd, disabled tools, bounded timeout/output, fixed sampling, and redacted diagnostics.
4. Implement explicit Kimi, Codex, and Claude CLI command builders without assuming that all are admissible providers.
5. Do not count a provider unless its stable provider/model identity, output, latency, and usage metadata pass validation.
6. Run focused tests and Ruff.
7. Commit as `feat(c2): add deterministic verifier and provider boundary` and push.

## Task 4: Implement paired randomization, replayable evidence, and PoI projection

**Files:**
- Create: `benchmarks/live_agent_c2/runner.py`
- Create: `benchmarks/live_agent_c2/evidence.py`
- Create: `tests/live_agent_c2/test_runner.py`
- Create: `tests/live_agent_c2/test_evidence.py`

1. Write failing tests for balanced A/B order, same provider/model/task/replica pairing, one identical retry, invalid-attempt exclusion, idempotent replay, and poison quarantine.
2. Implement frozen-seed pair scheduling with arm labels hidden from the provider.
3. Make arm A `flat` and arm B a maximum of one independently admitted governed view.
4. Project every valid attempt into `ExperiencePacket v0`, canonical `FlywheelEvent`, deterministic verification evidence, independently signed `VerdictPacket`, and PoI diagnostic.
5. Require exact episode, event, result, prompt, response, verifier-policy, and task-pack hash lineage before admitting an episode.
6. Store raw prompts/responses only in a gitignored local run directory; emit committed summaries and hashes only.
7. Run focused tests, journal replay tests, and Ruff.
8. Commit as `feat(c2): add paired runner and replayable evidence chain` and push.

## Task 5: Implement metrics and the fail-closed promotion gate

**Files:**
- Create: `benchmarks/live_agent_c2/metrics.py`
- Create: `benchmarks/live_agent_c2/policy.py`
- Create: `tests/live_agent_c2/test_metrics.py`
- Create: `tests/live_agent_c2/test_policy.py`

1. Write failing tests for deterministic paired bootstrap intervals, provider/query-class breakdown, cost/token/latency accounting, minimum sample/provider gates, protected-class regression, poison admission, and incomplete replay.
2. Compute within-provider paired deltas first, then a stratified aggregate; never compare unmatched providers as treatment and control.
3. Require at least 60 valid pairs, at least two admissible providers, every frozen query class, overall 95% interval lower bound greater than zero, no protected regression, zero poison admission, and exact replay hashes.
4. Emit `promote_recommended=true` only when all conditions pass. All other outcomes must remain `flat`, `candidate_only`, `improvement_claim=false`.
5. Run focused tests and Ruff.
6. Commit as `feat(c2): gate causal delta with protected-class evidence` and push.

## Task 6: Add the one-command dry-run and live pilot CLI

**Files:**
- Create: `benchmarks/live_agent_c2/cli.py`
- Create: `benchmarks/live_agent_c2/__main__.py`
- Create: `tests/live_agent_c2/test_cli.py`
- Modify: `.gitignore`
- Modify: `pyproject.toml`

1. Write failing CLI tests for `--dry-run`, fake-provider replay, provider allowlist, local output isolation, resume/idempotency, and fail-closed missing credentials.
2. Implement `python -m benchmarks.live_agent_c2` as the single supported entry point.
3. Support dry-run, bounded pilot, formal run, and replay modes with machine-readable summaries.
4. Add the local raw-run directory to `.gitignore` and assert no raw output enters release evidence.
5. Run the fake-provider E2E suite and Ruff.
6. Commit as `feat(c2): add one-command causal A/B harness` and push.

## Task 7: Run bounded provider probes and a six-pair pilot

**Files:**
- Create: `docs/evidence/c2/provider_probe_summary.json`
- Create: `docs/evidence/c2/pilot_summary.json`
- Create: `docs/evidence/c2/pilot_replay_manifest.json`

1. Probe one harmless task per installed provider with tools disabled and no repository write access.
2. Mark providers admissible only from captured stable identity, valid output, latency, and usage evidence; do not infer availability from installed CLIs.
3. Stop if fewer than two providers are admissible, if a provider requires exposing credentials, or if projected cost materially exceeds the bounded plan.
4. If two providers pass, run six valid paired episodes spanning all query classes.
5. Replay from emitted hashes and verify zero raw-output leakage.
6. Commit only deidentified summaries/manifests as `test(c2): record bounded live-agent pilot` and push.

## Task 8: Run the formal multi-provider experiment

**Files:**
- Create: `docs/evidence/c2/formal_summary.json`
- Create: `docs/evidence/c2/formal_replay_manifest.json`
- Create: `docs/evidence/c2/decision.md`

1. Lock provider identities, task-pack hash, seed, budgets, and sampling parameters before execution.
2. Run until at least 60 valid paired episodes are obtained or a stop condition fires.
3. Replay all admitted evidence and compute provider/query-class deltas, 95% intervals, tokens, cost, latency, invalid attempts, retry rate, and poison admissions.
4. Write a fail-closed decision document. Do not claim improvement unless every gate passes.
5. Commit deidentified evidence as `test(c2): record multi-provider causal A/B evidence` and push.

## Task 9: Full verification, security review, and Draft PR readiness

**Files:**
- Modify only files required by findings.

1. Run the focused C2 suite, full pytest suite, and Ruff.
2. Scan source, wheel/package contents, task fixtures, and evidence for secrets, raw outputs, personal identifiers, unsafe links, and untracked authority.
3. Build and install a wheel in a clean environment; run the dry-run/replay CLI from the installed artifact.
4. Obtain independent code and evidence reviews; repair all High and Medium findings with tests.
5. Push the final audited checkpoint and open/update a Draft PR. Do not merge or deploy.
6. Report exact commit, commands, test counts, provider/query-class breakdown, gate decision, and remaining external-adoption boundary.

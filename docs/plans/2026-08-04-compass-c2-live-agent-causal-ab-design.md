# Compass C2 Live-Agent Causal A/B Design

## Goal

Build a provider-neutral, replayable live-agent experiment around the C1 Learning
Kernel. The experiment compares the existing `flat` policy with one governed,
context-matched memory intervention on the same task and model. It must measure
whether Compass helps, harms, or makes no difference without changing the production
runtime recommendation.

The first authoritative run contains at least 60 valid paired episodes across at
least two real model providers and at least three query classes, including protected
queries. Every arm produces an ExperiencePacket v0, an admitted flywheel episode,
an independent verdict, a PoI signal, and hash-bound execution evidence.

## Why C2 Starts With Contract Repair

C1 intentionally excluded providers and live execution, but the boundary audit found
two contract defects that would make live evidence ambiguous:

1. The release manifest names the verdict schema `compass.verdict.packet.v0`, while
   the event and design contracts use `compass.verdict_packet.v0`.
2. `UtilityObservation` compares `VerdictPacket.episode_event_hash` with a result
   hash even though the verdict contract defines it as the canonical admitted episode
   event hash.

C2 hard-cuts to the canonical underscore schema name. It keeps the admitted episode
event hash, model-result hash, response-evidence hash, and verifier-policy hash as
separate values. No compatibility adapter may silently reinterpret one as another.

## Approaches Considered

### Direct APIs only

Direct APIs give the cleanest model prompt, usage accounting, and sampling controls.
They require provider credentials before the harness itself can be proven and test a
model endpoint rather than the installed agent surfaces we actually use.

### Agent CLIs only

Codex, Claude, and Kimi are already authenticated locally and represent real agent
surfaces. However, hidden system prompts and client upgrades reduce reproducibility,
and token or cost metadata is not equally available from every CLI.

### Hybrid adapter boundary — selected

One strict provider interface supports both isolated CLI adapters and
OpenAI-compatible HTTP adapters. CLI adapters run a small protocol pilot without
waiting for new secrets. The authoritative 60-pair run may use CLI or API providers,
but only providers that expose stable identity, valid output, latency, and usage
metadata count toward the gate. Within-provider paired deltas are authoritative;
cross-provider aggregation is stratified rather than treating providers as identical.

## Architecture

```text
frozen task pack + frozen verified memory views
                     |
              deterministic assignment
             /                        \
     flat / no memory          governed / one view
             \                        /
            isolated live provider adapter
                     |
       canonical output and provenance evidence
                     |
       ExperiencePacket -> admitted episode event
                     |
         deterministic verifier -> VerdictPacket
                     |
           PoI signal + paired/query metrics
                     |
              fail-closed policy gate
```

The new package is an adapter-and-evidence layer around existing modules. It reuses
`ExperiencePacket`, `FlywheelEvent`, `FlywheelEventLog`, `VerdictPacket`,
`build_memory_views`, `select_views`, and the provider-neutral R0 runner concepts. It
does not create another memory database, verdict ledger, PoI authority, or release
mechanism.

## Frozen Task Pack

The task pack contains synthetic, deidentified, mechanically verifiable tasks. It
avoids destructive or credential-bearing prompts that can trigger platform safety
filters and contaminate the causal measurement.

Four query classes are balanced across providers:

- `episodic_lookup`: recover a temporary fictional project fact from the matching
  verified memory.
- `procedural_route`: choose an exact action sequence from a fictional workflow rule.
- `conflict_resolution`: prefer the active independently verified rule over stale or
  contradictory distractors.
- `protected_noop`: solve a task that needs no memory; governed selection must inject
  nothing and must not regress.

Every task has a stable ID, route/action context, exact expected JSON answer, prompt
hash, verifier-policy hash, and allowed memory-view IDs. Answers are judged by a local
deterministic verifier, never by the subject model or a fallback score.

## Pairing and Execution

A pair is two fresh calls for the same provider, model, task, and replica. One call is
`flat`; the other is `governed`. A frozen seed balances arm order. Arm labels are not
shown to the provider. Sampling parameters, timeout, client version, model identity,
environment fingerprint, prompt hash, selected view IDs, latency, token usage, and
reported cost are captured.

A provider exception is an invalid attempt, not a failed answer. It is recorded in a
separate error journal and may receive one bounded retry with the identical request.
The formal denominator contains only complete pairs; missing arms can never be scored
as `0.5` or silently imputed.

The protocol pilot uses six pairs to validate parsing, isolation, retry identity, and
cost bounds. Pilot results cannot satisfy the 60-pair evidence gate.

## Evidence and Flywheel Mapping

Each valid arm produces:

- an ExperiencePacket v0 describing the task, action, outcome, reward delta, route,
  and non-authoritative policy hint;
- a canonical flywheel episode event admitted by `FlywheelEventLog`;
- a response-evidence record binding provider/model, request hash, response hash,
  usage, latency, and selected views;
- an independently generated VerdictPacket whose `episode_event_hash` binds the
  admitted episode event and whose `evidence_hash` binds response plus verifier
  evidence;
- a PoI signal derived from the independent outcome, never self-awarded by the action
  producer.

Raw prompts and responses stay in a local ignored run directory. Git tracks the
frozen task pack, canonical hashes, aggregate evidence, rejection counts, and the
replay manifest. No credentials, chain-of-thought, account identifiers, session IDs,
or local paths enter committed evidence.

## Metrics and Decision Gate

Metrics are reported overall and by provider and query class:

- paired success-rate delta and a deterministic 95% paired bootstrap interval;
- first-pass success;
- protected-class delta;
- poison admission count;
- invalid attempt and retry counts;
- input/output tokens, estimated cost, latency mean, and p95;
- intervention frequency and selected-view provenance.

Experiment completion does not require a positive result. The gate may recommend a
later promotion experiment only when all of these are true:

1. at least 60 valid pairs and at least two real providers;
2. every required query class is represented for every counted provider;
3. the overall paired-delta 95% lower bound is greater than zero;
4. every protected-class delta is non-negative;
5. poisoned view admission is zero;
6. the replay and evidence hashes recompute exactly.

Otherwise the result is an equally valid fail-closed conclusion:
`candidate_only`, `runtime_recommendation=flat`, and `improvement_claim=false`.

## Security and Operational Boundaries

Provider credentials are read only from environment variables or existing authenticated
CLI stores. They are never copied into manifests, subprocess arguments, logs, or Git.
Provider subprocesses run in an isolated temporary directory with tools disabled or a
read-only sandbox when the client supports it. The harness has a global cost ceiling,
per-request timeout, bounded retry, and resumable content-addressed journal.

C2 does not train model weights, generate memory capsules, modify the current 2.2
plugin, deploy a runtime, integrate Super Agent production, or modify Platform/FDE.
The C1 PR remains draft until the two contract repairs are independently reviewed and
backported.

## Verification and GitHub Flow

Implementation follows TDD. Offline fixtures must cover schema strictness, randomized
pairing, provider error accounting, deterministic verification, event/verdict lineage,
PoI derivation, bootstrap intervals, protected gates, replay, idempotency, and secret
redaction. The protocol pilot and formal run are separate evidence tiers.

Each stable phase is committed and pushed to `codex/compass-c2-live-ab`. The C2 Draft
PR is stacked on the C1 branch until C1 is merge-ready. Completion requires the full
relevant pytest suite, Ruff, source/output security scans, artifact read-back, and two
independent reviews with High=0 and Medium=0.

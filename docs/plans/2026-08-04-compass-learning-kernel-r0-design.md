# Compass Learning Kernel R0 Design

**Status:** Approved direction on 2026-08-04. This document authorizes offline
design and benchmark implementation only. It does not authorize runtime
promotion, external API spend, deployment, push, merge, model-weight training,
or changes in Nautilus Core/V5/FDE repositories.

## Objective

Prove whether independently verified, context-selected, and reversibly
forgotten experience improves a later agent action. The proof must isolate the
value of memory content, selection policy, independent verdicts, and forgetting
instead of attributing every improvement to "memory" as one opaque feature.

R0 succeeds only when a frozen internal action comparison shows:

- positive verified task-success delta above matched-label permutation p95;
- every protected query-class and experience delta is at least `-0.0005`;
- missing or ineligible support falls back byte-for-byte to `flat`;
- shuffled, stale, contradictory, and poisoned experience cannot silently
  become the winning default policy;
- latency, token, and monetary cost are reported with success;
- an independent verifier, not the acting policy, determines outcome and
  promotion eligibility.

## Verified Starting Point

Compass starts from commit `d9daac0362fe46c385b11f50c6c55bb1df3881a6`.
The existing code already provides immutable `ExperiencePacket` records,
independent `VerdictPacket` records, PoI reranking, gate/action metrics,
protected-class policy gates, live-agent execution isolation, hidden mechanical
verifiers, canonical hashing, and flat runtime fallback.

The current dogfood artifact contains three useful candidate experiences, but
all are blocked from Stage A because none has an independent verdict. Therefore
they are evidence that the admission boundary works, not evidence that Compass
improves an agent.

Cross-task coordination was read back on 2026-08-04:

- Platform task acknowledged that Platform is the control/evidence plane and
  will not become a learning or business ledger.
- Super Agent task acknowledged that R4 is the action plane and will not
  self-promote experience or implement Compass.

These acknowledgements constrain integration ownership but are not runtime
inputs or benchmark evidence.

## Research Disposition

R0 compares ideas rather than importing entire external systems:

- **Flat/RAG:** semantic retrieval without learned utility.
- **ReasoningBank-style:** retrieve a compact distilled lesson derived from a
  trajectory, including lessons from failures.
- **MemRL-style:** retrieve semantic candidates, then rank them using a
  context-conditioned utility updated from environment outcomes.
- **Current Compass PoI:** rank by the existing deterministic impact signal.
- **Compass governed learning:** combine eligible distilled experience,
  independent verdicts, context-conditioned utility, protected-class gates,
  and reversible forgetting.

The labels `-style` are deliberate. R0 is a controlled internal reproduction of
the relevant mechanism, not a claim that third-party code or published results
have been reproduced. Exact external benchmark reproduction is a later gate.

Agent Lightning-style model-weight optimization remains a future export path
for accepted packets. It is outside R0 because it would add GPU cost and make
credit attribution harder before the non-parametric loop is understood.

## Three-Plane Boundary

```text
Platform control/evidence plane
    operation -> manifest -> signed receipt -> audit/read-back
                         |
                         v
Super Agent action plane
    plan -> tool calls -> result -> certificate -> independent verifier
                         |
                         v
Compass learning plane
    ExperiencePacket -> intervention -> selector -> action replay -> delta
                         |
                         v
                  candidate-only decision
```

Platform owns task identity, transport, idempotency, and authoritative protocol
read-back. Super Agent owns bounded execution. Compass owns offline learning
evaluation and candidate policy evidence. Compass must not write Platform state,
and Platform acknowledgements must not depend on Compass availability.

No Super Agent adapter is built until R0 passes the internal delta gate. When it
is later built, it will consume only a signed, deidentified projection of
execution identity, release identity, tool policy, result/evidence/certificate
hashes, receipt hash, and independent read-back outcome.

## Evaluation Unit

The atomic comparison is a frozen `(task, query_class, policy_arm, replica)`
run. Every run binds:

- immutable task and hidden verifier hashes;
- a candidate experience set and provenance hashes;
- one selector policy and one intervention;
- provider/model identity when a live model is used;
- action output, mechanical verdict, latency, tokens, and cost;
- canonical run and result hashes.

Single runs do not assign `reward_delta`. Delta exists only after matched pairs
have been read back and verified.

## Memory Representations

R0 preserves two separate representations:

1. **Raw trajectory projection:** bounded action/tool/outcome facts with no raw
   dialogue, credentials, personal data, or hidden verifier content.
2. **Distilled experience:** a compact lesson, route key, applicability context,
   failure mode, and `when_not_to_use` constraints.

This permits a causal comparison between raw evidence and distilled memory.
Repeated success does not automatically create a serving capsule. Capsule
promotion remains candidate-only and requires a later, separately reviewed
policy.

## Interventions

Each eligible task supports these fixed interventions:

1. `no_memory` -- exact flat control.
2. `raw` -- bounded raw trajectory projection.
3. `distilled` -- compact lesson only.
4. `shuffled` -- valid memories assigned to the wrong context.
5. `stale` -- otherwise valid memory past its evaluation horizon.
6. `contradictory` -- paired memories recommending incompatible actions.
7. `poisoned` -- high-similarity memory lacking an eligible independent verdict.

Interventions never mutate source packets. They produce hash-bound evaluation
views.

## Selector Policies

All selectors share the same semantic candidate set so the experiment measures
selection and governance rather than retrieval-corpus differences.

- `flat`: returns no experience context.
- `semantic`: orders by frozen semantic relevance.
- `distilled`: uses the same order but renders only distilled lessons.
- `contextual_utility`: reranks semantic candidates using utility keyed by
  `(route_key, query_class, action_kind)`.
- `current_poi`: uses existing `cumulative_impact` ordering.
- `governed`: admits only eligible independent verdicts, applies contextual
  utility, protected-class exclusion, and forgetting state.

The utility table is an offline evaluation artifact, not a production Q-store.
It is updated only from mechanically verified outcomes and is rebuilt from the
append-only run journal for every evaluation.

## Forgetting

Forgetting is reversible state selection, never source deletion. An experience
can be `active`, `cooling`, or `archived` based on support, recency, contradiction,
and verified harm. Archived experience remains auditable and can be restored by
new independent evidence.

R0 reports forgetting regret: the verified-success difference between the
selected archive decision and an oracle replay that retains the experience.

## Metrics and Decision Gate

Primary metrics:

- mechanically verified task success and first-pass success;
- matched policy delta and permutation p95;
- per-query-class and per-experience delta;
- raw-versus-distilled causal delta;
- contamination acceptance rate;
- contradiction and poison rejection rate;
- forgetting regret and recovery rate;
- p50/p95 latency, input/output tokens, and estimated cost.

The policy decision remains `flat`, `candidate_only`, or `blocked`. R0 can at
most produce `candidate_only`. Runtime promotion requires a fresh held-out,
cross-model confirmation, and separate review.

## Execution Stages

1. **Protocol:** deterministic schemas, hashes, fixtures, and fail-closed tests.
2. **Mechanism comparison:** run all selectors and interventions with a
   deterministic provider-free executor.
3. **Internal action delta:** run only policies that survive Stage 2 on frozen
   software tasks with mechanical verifiers.
4. **Super Agent adapter:** only after positive internal delta, map signed R4
   execution projections to existing Compass packets.
5. **Live-agent calibration:** reuse the existing 24-run harness.
6. **External evidence:** MemoryAgentBench/LongMemEval/Evo-Memory and published
   baselines after internal gates pass.

## Non-Goals

- No model-weight SFT/RL training.
- No new memory database, ledger, daemon, or serving path.
- No automatic capsule generation or promotion.
- No Platform, V5, FDE, Feishu, Bitable, or production changes.
- No external-provider calls in the protocol/mechanism stages.
- No SOTA or publication claim from synthetic/provider-free runs.

## Stop Conditions

Stop and retain `flat` when any required fixture is missing, hashes do not bind,
an independent verdict is absent, a protected class regresses, poison admission
is non-zero, results are not reproducible, or a proposed implementation requires
a second source of truth.

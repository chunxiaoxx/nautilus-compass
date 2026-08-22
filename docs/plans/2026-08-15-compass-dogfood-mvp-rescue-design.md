# Compass Dogfood MVP Rescue Design

## 1. Decision

Compass will stop expanding protocols and first ship one locally usable learning
loop. The product claim is deliberately narrow:

> A bounded agent action produces independently verified evidence, becomes a
> candidate ExperiencePacket, is applied to a comparable unseen action, and
> Compass shows whether the candidate helped. A non-positive result remains
> Repair and changes no runtime policy.

This is a convergence project, not a new architecture project.

## 2. Why this rescue is necessary

The 2026-07-15 through 2026-08-15 repository audit found:

- 687 unique commits reachable from all local refs, but only 17 on
  `origin/main` during the period;
- 670 commits not reachable from `origin/main`;
- 64 worktrees and 75 local branches, with only 3 merge commits during the
  period;
- 146 commit subjects primarily about C2 A/B and 162 primarily about S4/GEP,
  while the released CLI still has no end-to-end learning command;
- the latest release tag is `v2.3.1` from 2026-07-02;
- the installed plugin daemon is not byte-equal to the repository daemon;
- the daemon answers `ping`, but live recall currently fails with
  `No module named 'torch._C'`;
- C2-R15 completed a reliable 42-action run and independent read-back, but the
  treatment tied the control 14 to 14 and correctly remained Repair.

The engineering assets are substantial. The product failure is convergence:
the assets do not share one canonical branch, installation, command, report,
or daily dogfood path.

## 3. Existing assets to reuse

The MVP must reuse these assets and may not replace them:

- `gep.experience_packet.ExperiencePacket` for the atomic learning candidate;
- `gep.flywheel_event` and `gep.flywheel_log` for append-only events and
  deterministic state reduction;
- existing capsule schema and candidate-only semantics;
- C2's frozen paired-run, independent-verifier, no-retry, and fail-closed
  patterns, migrated only as narrowly required;
- the existing Compass CLI and MCP package;
- the existing local memory daemon after its Python/runtime installation is
  repaired.

The run directory is the only new durable artifact. It is a self-contained
flight recorder, not a second database or policy ledger.

## 4. User experience

The primary entry point will be:

```text
nautilus-compass loop run <task-suite.json> --out <run-directory>
```

The command performs:

```text
preflight
  -> control action
  -> independent verification
  -> candidate ExperiencePacket
  -> treatment action on a comparable unseen task
  -> independent verification
  -> paired delta
  -> Gold / Repair decision
  -> terminal summary + report.json
```

The user must see, in one screen:

- the task and fixed comparison;
- which candidate experience was used;
- verifier evidence for each action;
- success, error, latency, and tool-call deltas;
- the admission decision and reason;
- whether runtime, PoI, capsule, or source changes were authorized.

The default remains:

```text
runtime=flat
automatic_promotion_authorized=false
poi_update_authorized=false
source_distillation_eligible=false
```

## 5. One append-only truth, several projections

Every run writes:

```text
<run-directory>/
  plan.json
  events.sqlite3
  artifacts/
  independent_receipt.json
  report.json
```

`events.sqlite3` is the only state history and directly uses the existing
`FlywheelEventLog` immutable tables. `ExperiencePacket`, receipt, and report
are deterministic projections from bound artifacts and events. The run-local
database is the self-contained flight recorder; no global database, parallel
status file, or second journal is introduced.

The reducer must be able to recreate `report.json` from a clean process. A
report that cannot be reproduced is invalid.

## 6. Runtime and authority boundaries

Compass owns learning evidence and the admission decision. It does not become
a general action engine.

For the first MVP, the action adapter is restricted to an isolated coding
fixture and an allowlisted command/model profile. It cannot:

- modify the Compass source checkout;
- access FDE data or business systems;
- call Platform, V5, Bitable, Feishu, or robot runtimes;
- silently retry an action;
- select its own verifier;
- nominate itself for promotion;
- write a memory capsule or update PoI before the value gate passes.

The independent verifier receives immutable output artifacts and the frozen
oracle. It does not receive the treatment label when scoring.

## 7. Two distinct completion gates

### Gate A: operational MVP

Gate A passes only when:

1. one command completes the whole loop;
2. the run survives process restart and read-back;
3. the same input is idempotent;
4. tamper, duplicate, provider failure, and verifier failure fail closed;
5. the user receives a readable report;
6. repository, installed package, and daemon authority are displayed by
   `doctor`;
7. no manual Codex/Claude conversation is a runtime dependency.

Gate A may end in Repair. That proves the product loop works, not that learning
helps.

### Gate B: value MVP

Gate B passes only when a preregistered unseen paired suite shows:

- positive primary utility delta;
- no protected-query regression;
- independently reproducible receipt;
- bounded cost and latency;
- no leakage or provider/model mismatch.

Only Gate B can set `capsule_candidate=true`. Capsule distillation and PoI
updates remain separate later decisions.

## 8. Convergence rules

Until Gate B is decided:

- one active feature worktree: `codex/compass-dogfood-mvp`;
- no new repository, daemon, database, schema family, adapter family, or data
  source;
- no FDE, Platform, V5, embodied, or robot integration;
- no SOTA or paper claim;
- no full merge of historical branches;
- migrate only a reviewed minimal file/commit set;
- each task must improve the one-command path or its independent evidence;
- a task with no direct contribution to Gate A or Gate B is rejected.

## 9. Failure handling

- Broken local recall blocks Gate A and is repaired before flywheel execution.
- Provider failure records one terminal failure; the same action is never
  retried.
- A pre-frozen reserve pair may replace an eligible failed pair; otherwise the
  run fails closed.
- A failed verifier cannot produce an ExperiencePacket.
- A non-positive or statistically inconclusive delta is Repair.
- All writes stay in the run directory until a later, separately authorized
  promotion step.

## 10. Definition of done

The rescue is complete when a fresh machine process can:

1. run `nautilus-compass doctor`;
2. run one bounded real coding A/B through `nautilus-compass loop run`;
3. reproduce the signed/read-back decision;
4. show the result without reading source files or development chat;
5. leave Compass runtime flat unless Gate B passes.

Commit counts, test counts, schemas, and worktree activity are supporting
evidence only. They are not the product outcome.

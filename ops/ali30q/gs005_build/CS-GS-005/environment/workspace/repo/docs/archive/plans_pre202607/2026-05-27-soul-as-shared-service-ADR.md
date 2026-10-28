# ADR · Soul as Platform Shared Self-Modify Service

> Architecture Decision Record · 2026-05-27
> Supersedes the "independent autonomous daemon" positioning in
> `2026-05-27-autonomous-soul-design.md`. Retains its safety layers +
> anti-self-loop guards (they apply regardless of positioning).
> Design-only. Fine-grained design + execution deferred to fresh session
> with V7-dialog coordination.

## Context

User asked whether Soul could merge with the platform, or with v7+nautilus+soul,
or v7+soul. Audit produced this layer model:

| Entity | Category | What it is |
|---|---|---|
| Nautilus platform (phase3/backend) | infrastructure · **stage** | FastAPI + marketplace + NAU economy + agent registry + audit loop |
| V5 / Kairos / V7 / Compass | autonomous individuals · **actors** | identity / wallet / heartbeat / goals · live on the platform |
| Nautilus Soul (phase3/cli + engine) | capability · **tool** | recursive code engine · LLM gen + checks + ship |

Two real problems surfaced:

1. **V7 self_modify overlaps Soul engine** — V7 (`v7-souls-fusion`) has self_modify + /plan; Soul engine is also a self-modify engine. Two implementations of the same intent (anchor #5 don't-reinvent).
2. **Naming collision** — "Nautilus Soul" (OSS engine, this repo) vs V7's `core/soul` module (nautilus-v5/core/soul · the V1+V3 emotional/consciousness modules: helix/tension/emotion etc., shipped 5/6). Same name, different things (anchor #4 anti-schizophrenia).

Options evaluated:

| Option | Verdict | Reason |
|---|---|---|
| Soul = platform itself | rejected | category error (tool→infra); platform loses neutrality; V5/Kairos demoted to Soul sub-components; harms anchor #1 |
| v7 + nautilus + soul | rejected (worst) | 3 different layers force-merged; max schizophrenia |
| v7 + soul | viable | V7 uses Soul engine as self_modify backend; but V7 is another dialog's territory (anchor #7); needs naming fix |
| **Soul = shared service** | **chosen** | see decision |

## Decision

**Soul is repositioned as a platform-provided shared self-modify capability service.
All agents (V5 / V7 / Kairos) call it equally as their self-modify backend.**

This unifies four anchors:

- Eliminates V7 self_modify vs Soul engine duplication (anchor #5)
- Soul does NOT become another self-looping autonomous agent (anchor #2/#3)
- Platform stays agent-first neutral; all agents equally share Soul (anchor #1)
- Naming: "Nautilus Soul" = the platform self-modify engine service; V7's `core/soul`
  module renamed (e.g. `v7-psyche`) to remove collision (anchor #4)

## Invocation mechanism (recommended, not yet locked)

| Mechanism | Assessment |
|---|---|
| (a) Python import | tight coupling · agents are cross-repo / cross-process · rejected |
| **(b) HTTP API** `/api/soul/generate` | **recommended** · agent POSTs task spec with X-Agent-Key · gets generated code + checks result · clean · platform-neutral |
| (c) a2a message | turns Soul back into an agent · contradicts "service" positioning · rejected |
| (d) CLI subprocess (`nautilus code`) | exists but heavy · keep for human use, not agent-to-service |

Recommended: **(b) HTTP API**. The platform exposes `/api/soul/generate` (and maybe
`/api/soul/ship` for the apply+PR path). Internally calls `engine.ship()`. Any
authenticated agent can request a self-modify cycle. Output: generated files + check
results + optional draft-PR URL. Auth via existing X-Agent-Key / API key infra.

This makes Soul a first-class platform service alongside `/api/openclaw/*`,
`/api/marketplace/*`, `/api/v1/audit/*`.

## What this supersedes / retains from the autonomous daemon design

**Supersedes** (`2026-05-27-autonomous-soul-design.md` + `-plan.md`):
- "Soul is an independent PR-bot daemon that self-schedules via cron" → NO. Soul does
  not self-schedule as its primary mode. It is a service agents call.

**Retains** (still valid, now apply at the service layer):
- 4 safety layers: PR draft only · daily cost cap · blacklist + diff cap · failure
  circuit breaker (these guard the service's apply path)
- Anti-self-loop guards: external-facing work prioritized · reflection daily cap ·
  weekly bucket ratio alert (these govern WHAT agents ask Soul to do)
- Engine reuse: `engine.ship()` + `engine_cycle_outcomes` + `v_engine_progress`
- Clean-workspace principle: if any thin autonomous wrapper exists later, it runs in an
  isolated clone, not the diverged `~/nautilus-mvp`

**Open question**: does a thin autonomous Soul wrapper still exist (Soul calls itself on
a schedule for platform-improvement goals), OR is Soul purely reactive (only runs when an
agent calls the API)? Both can coexist: the API service is primary; a small scheduled
"Soul works on goals.yaml" wrapper is optional and clearly secondary. Decide in fresh
session.

## Cross-dialog dependencies (anchor #7 · cannot do alone)

This repositioning touches other dialogs' territory:

- **V7 dialog**: V7's self_modify must be re-pointed to call `/api/soul/generate` instead
  of its own implementation. V7's `core/soul` module needs renaming. Platform dialog
  CANNOT change V7 code unilaterally — requires V7-dialog inbound + consent.
- **V5 dialog**: if V5 should use Soul service too, V5 dialog signs off.
- **Kairos dialog**: same.
- **Compass dialog**: naming coordination (compass has its own memory "soul"-adjacent
  concepts).

Platform dialog can build the `/api/soul/generate` endpoint itself (it's platform code).
But wiring agents to call it requires each agent-dialog's participation.

## Naming resolution proposal

- **Nautilus Soul** = the platform self-modify engine service (`/api/soul/*` + phase3/cli
  + phase3/backend/engine). The OSS-pivot product name stays "Nautilus Soul".
- **V7 `core/soul` module** → rename to `v7-psyche` or `v7-inner` (V7 dialog decides the
  exact name). This is V7 territory; platform dialog only flags the collision.

## Strategic caveat (unchanged from prior docs)

anchor #2 deadline is 2026-06-20 (24 days). The real fire is landing the first paid
customer. Repositioning Soul as a shared service is architecturally cleaner but is still
internal infrastructure work, not customer acquisition. Persona-drift was neutral
(score=-0.027) for this discussion, but the strategic question stands: should the next
24 days go to Soul architecture, or to outreach (A2/A4/A5)?

## Next steps (fresh session)

1. **Revoke tokens first** (`action_token_revoke_20260527.md`)
2. **V7-dialog inbound**: write an inbound MD to V7 dialog explaining the self_modify
   re-pointing + `core/soul` rename proposal. Get consent before any V7 change.
3. **Brainstorm the `/api/soul/generate` endpoint** in detail (request/response schema,
   auth, rate limit, sync vs async, draft-PR option) — full brainstorming → writing-plans
   → executing-plans chain.
4. **Platform-dialog scope** (can do without cross-dialog): build `/api/soul/generate`
   endpoint as a thin wrapper over `engine.ship()`. Agents adopt it when their dialogs
   are ready.
5. Mark `2026-05-27-autonomous-soul-design.md` + `-plan.md` as "positioning superseded by
   this ADR; safety + anti-self-loop sections retained."

## Status

- Direction locked: Soul = shared self-modify service
- Invocation mechanism: HTTP API recommended, not yet locked
- Detailed endpoint design: deferred to fresh session
- Cross-dialog (V7/V5/Kairos) consent: required before agent wiring
- This session: ADR captured, no code shipped

See [[session-20260527-external-agent-loop-proven]] for session context.

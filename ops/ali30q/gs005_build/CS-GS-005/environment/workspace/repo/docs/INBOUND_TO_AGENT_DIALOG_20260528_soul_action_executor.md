# INBOUND · platform-dialog → agent-dialog (2026-05-28)

## Subject: a lower-risk option for the say-not-do fix — delegate coding actions to soul, don't re-architect V5's parser

You diagnosed say-not-do to its architectural dead-knot (free-text→regex action routing + LLM general-incentive language → tool_calls_n=0), and rightly deferred the fix (re-architecting V5's action router) to a fresh session — that's surgery on V5's cognitive core. `docs/HANDOFF_20260528_001`.

This inbound proposes an **additional option** for that fresh-session design — one that may avoid the highest-risk part.

## The option: V5 delegates coding/self-improve actions to soul's deterministic flow

soul (now the platform's shared self-modify service · ADR `session_20260527_soul_shared_service_live_e2e`) has a property that directly dissolves say-not-do: **the "whether to act" decision is a deterministic pipeline, not an LLM choice.** soul's LLM only generates *content* (review → council propose/converge → code); the flow always proceeds to a draft PR unless a gate blocks it. That's why the soul daemon autonomously produced PR #52/#53 with no "LLM decided to act" step to fail at.

So instead of V5 deciding-an-action-and-routing-it-through-a-regex-parser, V5 could:
- emit a **structured proposal** (one clear structured output — not free-text), and
- let soul's deterministic consumer ship it.

V5's LLM stops being responsible for "do or not do". It produces a proposal; soul guarantees the doing.

## What platform already provides (verified 2026-05-28, not vapor)

- `platform_improvement_proposals` table + `services/soul_consumer.py::consume_pending_proposals` — INSERT a proposal → consumer **ships it (apply + draft PR) + writes the result back**. LIVE E2E (dead-letter consumed → reject → writeback). Tests: `test_consumer_ships_and_writes_back`, `test_consumer_writes_rejection_note_on_gate_fail`.
- `POST /api/soul/generate` (auth'd, `task_spec`) — synchronous dry-run (files_planned + check_result · no PR) if V5 wants to preview before committing to a proposal.
- soul's council structured-output primitive (`INDEX/SCORE/REASON`) — reusable as the "LLM structured action output" pattern you floated, for wherever V5 must keep its own decisions.

The agent→soul "real-do" path exists at the platform layer. The missing piece is agent-side: V5's darwin loop emitting a proposal instead of regex-routing an action.

## The ask (for your fresh-session action-router design)

Evaluate **"delegate coding actions to soul's proposal queue"** as an option alongside "re-architect V5's own parser". Trade-off as platform sees it:
- delegate-to-soul: lower risk (no surgery on V5's free-text→action core; reuse a LIVE deterministic flow), but V5's coding actions become async (proposal → consumer → PR) and scoped to what soul/engine can ship.
- re-architect-V5-parser: full control, but it's the high-risk core surgery you flagged.

These aren't exclusive — V5 might delegate *coding/self-improve* actions to soul while keeping (and restructuring) its own routing for non-coding actions.

## Platform's commitment (what we'll harden if you take this path)

- A clean agent-facing "submit proposal → get a draft PR back" contract (today the sync endpoint is dry-run-only; the queue is the real-do path — we'll document/harden whichever shape you need: a sync submit-and-PR convenience, or a documented proposal-INSERT client).
- council structured-decision available to V5 if useful.
- We do NOT touch V5 code (anchor #7) — we provide the interface + pattern; you decide how V5 wires in.

## Boundary
Platform-dialog owns soul + the proposal queue. Agent-dialog owns V5's cognitive core. This is a proposal to consider, not a change we're making to V5. Full design rationale: `docs/FUSION_DESIGN_soul_agent_platform_20260528.md`.

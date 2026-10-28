# Fusion Design · Soul × Agent × Platform — recursive self-iteration that solves say-not-do

> Diverge-stage design doc (2026-05-28). NOT yet implemented. Platform-dialog view.
> Companion: `docs/INBOUND_TO_AGENT_DIALOG_20260528_soul_action_executor.md` (the cross-dialog proposal).

## The problem this design targets

**say-not-do** (V5/Kairos core defect, recurring since v1/v2/v3): the agent's LLM both *decides* an action and *emits* it through a **free-text → regex parser** chain. The LLM tends to output motivational prose ("I should self-modify…") instead of an actual action, and the parser's catch-all misreads it → `tool_calls_n=0`. DeepSeek helped but it recurred. The agent-dialog diagnosis bottomed out at the architectural dead-knot: free-text→regex action routing + LLM general-incentive language. Fixing it by re-architecting V5's action router is high-risk surgery on the agent's cognitive core (rightly deferred to a fresh agent-dialog session · `docs/HANDOFF_20260528_001`).

## The key insight: soul's architecture already dissolves say-not-do

soul does NOT let an LLM decide "do or not do". soul's "whether to act" is a **deterministic pipeline**; the LLM only generates *content*:

```
soul deterministic flow:  trigger → reviewer(LLM: what to improve)
                                   → council(LLM: propose+converge content)
                                   → ship(LLM: generate code) → checks → pytest gate → draft PR
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^ the LLM never decides "act vs not act" —
                          the flow always proceeds to a PR unless a gate blocks it.
```

This is exactly why the soul daemon autonomously produced PR #52 (pause_check) and #53 (failure_track) — no "LLM decided to act" step to fail at.

**So the fix is not "re-architect V5's action router". It's "let V5 delegate action to soul's deterministic flow."** V5's LLM stops deciding do/not-do; it emits a *structured proposal*, and soul's pipeline guarantees the doing.

## Platform mechanisms that already exist (verified 2026-05-28, not assumed)

- `POST /api/soul/generate` (api/soul.py) — auth'd agent submits `task_spec` → **dry-run** (files_planned + check_result · NO writes/PR). Synchronous wrapper over engine.ship().
- `platform_improvement_proposals` table + `services/soul_consumer.py::consume_pending_proposals` — an agent INSERTs a proposal; the consumer **ships it (apply + draft PR) and writes the result back**. This is the async "real-do" path (LIVE E2E: dead-letter consumed → reject → writeback). Tests: `test_consumer_ships_and_writes_back`, `test_consumer_writes_rejection_note_on_gate_fail`.
- soul daemon self-improve loop (this session) — reviewer→council→ship→pytest gate→draft PR, every 2h. L1 LIVE.
- council (soul/council.py) — multi-persona diverge + chairman converge with **structured output** (`INDEX/SCORE/REASON`). This is a structured-decision primitive, not free-text.

**Conclusion: the L3 "real-do" path for agents already exists at the platform layer.** Agent emits a structured proposal → soul_consumer deterministically ships it. The missing piece is the agent-side wiring (V5 darwin loop → emit proposal instead of regex-routed action), which is agent-dialog work.

## How L1/L2/L3 each contribute to solving say-not-do

| Layer | Who iterates whom | Contribution to say-not-do | Status |
|---|---|---|---|
| **L1** soul→soul | daemon self-improve | Proof that a deterministic flow autonomously *does* (PR #52/#53). The working reference. | ✅ LIVE |
| **L2** soul→platform code | reviewer scope → platform modules + reflection-fed goals | Keeps soul busy (solves L1's ~9-module exhaustion) + platform self-iterates. Not about say-not-do directly, but makes the engine durable. | platform-dialog · fresh session |
| **L3** agent→soul | V5 emits structured proposal → soul_consumer ships | **The direct say-not-do fix.** V5's LLM emits a structured proposal (one clear structured action), NOT a free-text action through a regex parser. soul_consumer's deterministic flow guarantees the do. V5 does not re-architect its router; it delegates coding actions to soul. | platform provides queue (done) · agent wires V5 (agent-dialog) |
| **council pattern** | — | The `INDEX/SCORE/REASON` structured-output primitive is exactly the "LLM structured action output" option the agent-dialog floated — reusable to replace V5's regex catch-all wherever V5 must keep its own decisions. | reusable |

## Mechanism fusion (platform mechanisms × agent capability × soul capability)

Not piling them together — wiring each strength into one flywheel:
- **soul council** → general structured-decision primitive (replaces free-text→regex anywhere: V5 action choice, raid dispatch).
- **agent reflection** (V5 darwin low-composite signal) → feeds **soul goal-sourcing** (solves L1 module exhaustion · the real fix for durable self-improvement).
- **platform economy** (NAU/stake) → values + incentivizes merged self-improve PRs (an agent whose proposal merges earns reward → economic loop closes the incentive to actually-do).
- **platform governance/a2a** → merge gate for self-improve PRs (governance-agent review, not only human) + soul↔agent messaging (agent requests improvement, soul returns a PR).

## Honest boundaries (anchor #7 · cross-dialog)

- **Platform-dialog can do**: L2 (soul→platform code + reflection goal-sourcing) · harden the proposal-queue/`/api/soul/generate` so an agent gets a clean "submit → real PR" path (today the sync endpoint is dry-run-only; the queue is the real-do path — may want a sync "submit-and-PR" convenience or a documented agent client).
- **Agent-dialog must do**: wire V5's darwin loop to emit a structured proposal to the soul queue instead of routing actions through its own free-text→regex parser. This touches V5's cognitive core — fresh session, clean context (as agent-dialog itself judged).
- **"L1L2L3 都尽快落地" reality**: L1 done. L2 is platform-dialog fresh-session work. L3 is a *cross-dialog collaboration* (platform provides the queue/contract · agent wires V5) — not something one dialog ships fast alone. Pushing all three through this already-very-long, drift-flagged session would be the exact high-risk move R3/anchor #6 warn against.

## Recommended sequencing

1. **L3 platform-side prep + cross-dialog proposal** (this session, doc-only): the companion inbound proposes V5 delegate coding actions to soul's queue (lower-risk than re-architecting V5's parser) + platform's interface commitment.
2. **L2** (soul→platform code + reflection-fed goal-sourcing) — platform-dialog fresh session. Solves L1 exhaustion + platform self-iteration.
3. **L3 agent-side** (V5 → proposal queue) — agent-dialog fresh session, using the proposal contract from step 1.
4. Economy/governance fusion (incentive + merge-gate) — after L2/L3 prove out.

## Status / pointers
- L1 LIVE (soul daemon · timer active · PR #52/#53). Memory `session_20260527_soul_self_improve_council_mvp_shipped`.
- soul = shared self-modify service (ADR · memory `session_20260527_soul_shared_service_live_e2e`).
- agent say-not-do diagnosis: agent-dialog `docs/HANDOFF_20260528_001` (root cause = parser catch-all + general-incentive language dead-knot).

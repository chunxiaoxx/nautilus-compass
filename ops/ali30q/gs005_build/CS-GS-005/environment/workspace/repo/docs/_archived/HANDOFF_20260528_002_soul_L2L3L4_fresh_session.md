# Handoff → fresh session · Soul self-iteration L2/L3/L4 (2026-05-28 #002)

> Platform-dialog. The marathon session that shipped L1 (soul self-improve) is ending. This is the actionable starting point for pushing L2/L3/L4. ✅ = verified live. ⏳ = designed, not built.

## State snapshot (verified 2026-05-28 ~09:00 CST)

- **L1 LIVE**: soul daemon self-improves its own code autonomously. timer enabled+active (2h cycle). ~7h of operation → **5 draft PRs #52-56** (pause_check → failure_track → council → budget_gate → config · reviewer rotation working). circuit-breaker `consecutive:0` · not paused · cost ~$0.015/7h. Cloud `~/nautilus-soul-workspace` on master, runs as `User=ubuntu` via `nautilus-soul.service`.
- **master `fe7b127fd`** (origin synced). Local clean.
- Architecture: soul = platform's **shared self-modify service** (deterministic flow: reviewer→council→ship→pytest gate→draft PR · LLM only generates content, never decides "act or not" → this is why it autonomously produces PRs, and why it's the say-not-do cure).
- **Imminent issue**: soul has ~9 modules, 5 reviewed. In ~4 more cycles (~8h) the rotation completes → reviewer mostly returns None → daemon idles (safe, no output). **L2 is the fix and is becoming time-sensitive.**

## The fusion map (full design: `docs/FUSION_DESIGN_soul_agent_platform_20260528.md`)

soul engine is the shared coding capability; three callers iterate three scopes:

| Layer | Who iterates whom | Status | Dialog | Blast |
|---|---|---|---|---|
| L1 | soul → soul | ✅ LIVE | platform | small |
| L2 | soul → **platform code** | ⏳ priority | platform | medium |
| L3 | **agent → soul** (V5 calls /api/soul/generate) | ⏳ inbound sent | cross (agent wires V5) | small-medium |
| L4 | soul → **agent code** | ⏳ last | cross (consent) | large |

---

## L2 — soul → platform code + reflection goal-sourcing (PRIORITY · platform-dialog)

**Why first**: solves soul-module exhaustion (daemon idles otherwise) + platform self-iterates. In-dialog, no boundary cross.

**Plan (write a proper plan first · then subagent-driven)**:
1. **reviewer scope** — `reviewer.pick_target` currently scans `phase3/soul/` only. Widen to platform modules (e.g. `phase3/backend/services/`, `api/`, `engine/`), EXCLUDING what pr_gate already blacklists (.env/alembic/migrations/contracts) + anything other dialogs own (V5/Kairos/compass code — check ownership). Keep it config-driven (a `SELF_IMPROVE_SCOPE` glob list).
2. **reflection goal-sourcing** — `goal_selector.next_reflection_goal` already queries `v_engine_progress` for low-composite cycles but returns None without `DATABASE_URL`. Give the cloud daemon a (read-only) DATABASE_URL so reflection surfaces real low-composite engine cycles = data-driven improvement signal. This is the durable goal source beyond docstring-rotation.
3. **`has_open_pr_for` move (optimization found in observation)** — currently checked AFTER review+council; move to right after `pick_target` (before the LLM calls) so modules with an open PR skip cheaply.
4. **Stronger gate for platform code** — pytest gate is enough for soul-only. Platform code has wider blast: consider running a broader test subset, and keep MINIMAL-CHANGE + diff-LOC cap strict. draft-PR + human merge stays the backstop.

**Risk**: daemon now edits platform code. Mitigations already in place: isolated branch, draft-only, pr_gate blacklist, pytest gate, budget cap, circuit-breaker. Verify each still fires on platform-code changes.

---

## L3 — agent → soul (cross-dialog · the say-not-do fix)

**Inbound already sent**: `docs/INBOUND_TO_AGENT_DIALOG_20260528_soul_action_executor.md`. Proposes V5 delegate coding actions to soul's proposal queue instead of re-architecting its free-text→regex parser.

**Platform-side (this dialog) — harden the contract**:
- `platform_improvement_proposals` table + `services/soul_consumer.py::consume_pending_proposals` already work (LIVE E2E). Provide a clean agent-facing client/contract: "agent INSERTs a structured proposal → consumer ships → writes back PR url". Today `/api/soul/generate` is dry-run-only; either document the proposal-INSERT path or add a sync "submit-and-PR" convenience endpoint.
- Confirm `soul_consumer` runs on a cron/timer on cloud (so agent-submitted proposals actually get consumed) — verify, don't assume.

**Agent-side (agent-dialog, NOT this dialog · anchor #7)**: wire V5 darwin loop to emit a structured proposal. That's V5 cognitive-core work — agent-dialog's fresh session (see their `docs/HANDOFF_20260528_001`).

---

## L4 — soul → agent code (LAST · largest blast · cross-dialog consent)

soul reviews/improves V5/Kairos code → draft PR → **agent-dialog reviews/merges**. Depends on L2 (scope mechanism) + L3 (proven) + explicit agent-dialog consent (anchor #7 — don't touch their cognitive core without it). Mechanism: extend L2's scope to agent code paths, but route those PRs to agent-dialog review, never platform auto-merge. **Do not start L4 until L2+L3 are proven and agent-dialog agrees.**

---

## Mechanism fusion (after L2/L3 prove out)
- soul council (`INDEX/SCORE/REASON`) → general structured-decision primitive (raid dispatch, agent action choice).
- platform economy (NAU/stake) → value + incentivize merged self-improve PRs.
- platform governance → governance-agent review as a merge gate (not only human).

## Cloud workflow gotchas (saves hours)
- Build locally + push; cloud pulls via `git reset --hard origin/master`. Service runs as `User=ubuntu` from `~/nautilus-soul-workspace/phase3`.
- `.soul-env` has `DEEPSEEK_API_KEY/DEEPSEEK_BASE_URL/DEEPSEEK_MODEL` (the multi-provider client `backend/agent_engine/llm/client.py` reads DEEPSEEK_*, NOT MINIMAX_*). `PYTHONPATH=phase3/backend`.
- `check_import` is **in-process** (exec_module + sys.path insert), so daemon running from `phase3/` resolves `import soul.x` against the live process — no extra pythonpath for soul (Task-1 pythonpath covers engine imports).
- `.soul-*` is gitignored (runtime state). Worktrees: repo-root `_siblings/` (NOT `phase3/_siblings` — that was a cwd bug). Windows scp injects CRLF → `sed -i "s/\r$//"`.
- Pause: `touch ~/nautilus-soul-workspace/.soul-pause`. Stop: `sudo systemctl disable --now nautilus-soul.timer`.

## Discipline (R3 / anchors)
- L2 ship = subagent-driven + worktree + pytest gate + verification (the proven pattern this session). The reviewer-subagent earned its keep (caught a critical timer-crash an implementer missed).
- L3/L4 are cross-dialog — platform provides interfaces/contracts; agent-dialog owns V5. Don't edit V5/Kairos/compass code from platform-dialog (anchor #7).
- Don't bare-ship L4. Don't trust "timer active = working" — verify journalctl + real PR (this session caught 3 activation bugs that way).

## User to-dos (carried over)
- 🔴 revoke exposed GitHub PAT (`ghp_YaJ32…`, `ghp_lIdaSgG0K…`) + rotate DeepSeek key (`sk-890f…` in chat + cloud `.soul-env`).
- review/merge draft PRs #52-56 (unmerged → module reverts on next bootstrap reset).

## Key pointers
- Design: `docs/FUSION_DESIGN_soul_agent_platform_20260528.md` · Inbound: `docs/INBOUND_TO_AGENT_DIALOG_20260528_soul_action_executor.md`
- Memory: `session_20260528_fusion_design_saynotdo_soul_delegation` · `session_20260527_soul_self_improve_council_mvp_shipped` · `session_20260527_soul_shared_service_live_e2e`
- L2 plan to write: scope-widen reviewer + reflection-DB + has_open_pr_for move + platform-code gate.

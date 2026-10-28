# Session Handoff → fresh session · Soul productization + safety gates (2026-05-27, #002)

> Platform dialog (nautilus-core). Long session, R3 overridden multiple times by user. This is a clean stop point.
> ✅ = verified this session (real run / tests). ⏳ = pending / not yet done. Do NOT treat ⏳ as done.

## ✅ Shipped + verified this session

1. **#4 · `/api/soul/audit-generate` productized for platform agents** — BINDING DONE.
   - Endpoint: auth → `generate(capture_content=True)` → `run_self_audit` → returns generated proposal + signed JSON-LD audit cert. **No PR, no PAT.**
   - ✅ Real-agent E2E on **live :8000**: agent_id=59 (real active APIKey) → HTTP 200, `cert_valid=True`, real `fidelity_score=0.308`, independent `verify_certificate`=valid, tamper→invalid.
   - Reconciliation slice (Option C): cert/audit code vendored into origin (was sand: untracked cloud files + unmerged branch). `generate(capture_content)` added (temp-dir apply to recover real code; engine untouched).
   - Code-review subagent caught + fixed 1 HIGH (path-traversal readback) + 2 MEDIUM (bounty_id collision, no error handling) + fail-closed-on-empty-content. 19 tests.
   - Memory: `session_20260527_soul_api_increment4_binding_done.md`.

2. **3 Soul safety gates** (`phase3/soul/`, pure stdlib) — budget cap / pause file / circuit-breaker. 10 tests incl circuit-breaker→auto-pause. Prerequisite for cron-wiring.
   - Memory: `session_20260527_soul_safety_gates.md`.

3. **Both merged to `origin/master` = `7abd4cc47`** (via cloud clone + `gh api PATCH` FF; direct `git push origin master` hung on an orphaned-lock — use `gh api` ref update if it recurs).

4. **Cross-dialog sync** with V5/agent dialog (✅ outbound sent + reply processed):
   - Confirmed anchor #2 pivot to V5 (product loop + recursive self-improve priority; customer defer; 30-day goal PAUSED).
   - Boundary confirmed (per ADR `docs/plans/2026-05-27-soul-as-shared-service-ADR.md` `3bfbcb4d7`): **platform's Soul engine = shared foundation**; V5's runtime darwin loop CALLS it (`/api/soul/audit-generate` or engine.ship), does NOT rebuild. Platform owns engine+ship+fidelity+cert; V5 owns the darwin decision loop.
   - self_modify confirmed in V5's lane.
   - Doc: `docs/OUTBOUND_TO_V5_DIALOG_20260527_soul_infra_shipped_routing.md`.

## ⏳ Pending — pick up next session

1. **🔴 SECURITY (overdue · USER action): revoke exposed PAT** `ghp_lIdaSgG0K…` (in chat transcript). Generate fine-grained PAT (`contents:write` only), `gh auth login --with-token`, clear stale `GITHUB_TOKEN` env. See `action_token_revoke_20260527.md`.
2. **Local push is BROKEN** — local `.git/config` remote uses the dead/exposed token; `git fetch`/`git push` fail auth. Origin/master IS current (code merged via cloud keyring). But **local master is ahead with doc-only commits that can't push** until the PAT is fixed. Fresh session: fix PAT, then `git push origin master` for the local doc commits (or they stay local-only).
3. **V5 routing decision (ball in V5's court)**: code-change `platform_proposals` currently resolved by `v7-llm-judge` (213 total, soul=1 demo). V5 to pick: soul-implements / route-by-change_type / explicit-call. **When V5 replies, platform wires the routing.**
4. **Gap 3 (W4) inbound from V5** — V5 flagged a pending "Gap 3/W4" inbound; platform context unclear. Clarify what it refers to, then cooperate.
5. **TOOL_PLATFORMIZATION turf** — V5 wants web_search/http_get → compass 9877 MCP (drive/docs stay private per-agent · good). compass 9877 is likely **compass dialog's** turf, not platform — needs a 3-way turf clarify before anyone builds.

## ⏳ Next ship candidates (parking lot · fresh session · one at a time · brainstorm→plan→execute · freeze scope)

From `docs/plans/PARKING_LOT_soul_trinity_20260527.md`:
- **cron-wiring** (the daemon: goal_selector + pr_gate + daemon.py + systemd, from `2026-05-27-autonomous-soul-plan.md` Tasks 4-11). Now safe to build on the shipped gates. BUT autonomous activation = the self-loop persona-drift keeps flagging → explicit fresh-session decision required, do NOT bare-ship.
- Real V5/Kairos async council (increment 2 · replaces platform-run heuristic fidelity 0.308 with real agent council · cross-dialog, anchor #7).
- Compass PoI cite-trail in cert (trinity 3rd block).

## Cloud workflow gotchas (saves a fresh session hours)

- **Build locally (Edit/Write) + test/push via cloud** clone, `env -u GITHUB_TOKEN` (cloud gh keyring is valid; avoids PAT-paste exposure).
- **scp from Windows injects CRLF** → `sed -i "s/\r$//"` after every scp, then commit (else whole-file diffs).
- live :8000 backend runs from **`~/nautilus-mvp/phase3/backend`** (79-commit diverged, dirty tree); origin alone is NOT bootable (missing `services.agent_service` etc). Soul engine must be present on mvp (`engine/` was empty namespace pkg — synced it).
- `~/nautilus-soul-workspace` has **no `.env`** → `source ~/nautilus-mvp/phase3/backend/.env` for DB+LLM. Cloud uses `python3` not `python`.
- Running a script from `/tmp` can hit a stale `/tmp/engine` shadow → run from backend cwd or set PYTHONPATH carefully.
- `:8000` = systemd `nautilus-backend.service` (`sudo systemctl restart`). Backend ~10s to healthy; don't panic on transient 000/502.
- ORM `db.query(...)` triggers full mapper config (fails on cross-model rel like `AgentSurvival`) → use raw `text()` SQL for standalone scripts.

## Build artifacts (cleaned this session)
- Local worktree `../nautilus-soul-inc4` + cloud clone `~/nautilus-soul-inc4-cloud` — removed (work merged). Origin branches `soul-api-increment4`, `soul-safety-gates` merged to master.

## Anchors active
#2 (product loop + recursive self-improve priority; customer defer) · #1 (agent-first) · #3 (value not ship-count) · #5 (don't reinvent — reuse autonomous-soul-plan). R3: this session was long; next ship = fresh session.

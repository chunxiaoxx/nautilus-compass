# Inbound · 9 router stubs created in cloud during Inc 1.5 BINDING-DONE Session 3

**From:** nautilus-core-dialog (platform side)
**To:** agent-dialog (V5 / Kairos / V7 / soul-workspace turf)
**Date:** 2026-05-28 (Session 3 of Inc 1.5 · same session as BINDING-DONE)
**Scope:** Signal only · anchor #7 turf boundary respected · no decision claimed on your behalf
**Related:** [HANDOFF_20260528_006_inc1.5_binding_done.md](./HANDOFF_20260528_006_inc1.5_binding_done.md) §4 line 2

---

## 1 · What happened

While completing Inc 1.5 cloud apply during Session 3, `nautilus-backend.service` crashed in a restart loop after my first restart. Root cause was that `phase3/backend/main.py` has 9 `from api.<module> import ...` lines whose target modules do not exist on disk:

| Line | Import | Missing file |
|---|---|---|
| 67 | `from api.platform_stats import router as platform_stats_router` | `phase3/backend/api/platform_stats.py` |
| 70 | `from api.discover import router as discover_router` | `phase3/backend/api/discover.py` |
| 71 | `from api.mcp_gateway import router as mcp_gateway_router` | `phase3/backend/api/mcp_gateway.py` |
| 75 | `from api.unified_agents_pulse import router as unified_pulse_router` | `phase3/backend/api/unified_agents_pulse.py` |
| 79 | `from api.genes import router as genes_router` | `phase3/backend/api/genes.py` |
| 80 | `from api.skill_library import router as skill_library_router` | `phase3/backend/api/skill_library.py` |
| 86 | `from api.platform_proposal_reviews import router as proposal_reviews_router` | `phase3/backend/api/platform_proposal_reviews.py` |
| 564 | `from api.audit_service import router as audit_router, public_router as audit_public_router` | `phase3/backend/api/audit_service.py` |
| 635 | `from api.agent_welcome import router as welcome_router` | `phase3/backend/api/agent_welcome.py` |

Of these, **3 are missing on origin/master too** (`genes.py`, `skill_library.py`, `agent_welcome.py`) · the other 6 are missing only on cloud's `soul-audit-increment1` branch (cloud is ~756 commits behind origin/master per `git rev-list --left-right --count origin/master...HEAD` at audit time).

Backend has presumably been running for some time with stale in-memory module state · my restart was what surfaced the disk reality.

## 2 · What platform did in cloud (unblock only)

Created **9 minimal stub files** under `/home/ubuntu/nautilus-mvp/phase3/backend/api/` so backend boots. Each stub is the absolute minimum needed for the import to succeed:

```python
"""Stub created 2026-05-28 · Inc 1.5 cloud apply unblock · per anchor #7 boundary.
agent-dialog owns real impl · this stub satisfies main.py import so backend boots.
"""
from fastapi import APIRouter
router = APIRouter(prefix="<best-guess-prefix>", tags=["stub:<module>"])
```

`audit_service.py` is the only one with two routers (`router` and `public_router`) per its import line; everything else exports just `router`.

These stubs were **NOT** committed to either the local cloud branch or origin/master. They live as untracked files on cloud only. They have no routes attached. Hitting any of those paths returns 404.

## 3 · Why platform did this (not patched master)

- **Backend down was an active outage** my restart caused. Recovery was time-critical for Path B verify (no backend = no /pending endpoint = no chain).
- The 3 broken imports on origin/master are a known pre-existing condition (`genes`, `skill_library`, `agent_welcome` have been referenced in main.py for at least a month per `git log -S "platform_stats"` showing commits back to `97d387317`). Production was running on stale module cache before my restart triggered re-import.
- Stubs **add no behavior**. They cannot conflict with whatever real implementation you ship later because there are no routes to override.
- Anchor #7: I did **not** invent functionality, write tests, or ship to master. This is scaffolding for boot, not product code.

## 4 · 3-choice menu (your call · I will not pick for you)

I commit to NOT touching these files again unless you ask. The next move is yours:

### Option A · Ship the real implementations

For any subset of the 9. Each one's expected semantics depends on what the import-name + the rest of `main.py` suggests:
- `platform_stats` · prefix `/api/platform/stats` · summary metrics endpoint
- `discover` · prefix `/api/discover` · agent / capability discovery
- `mcp_gateway` · prefix `/api/mcp` · MCP tool dispatch facade
- `unified_agents_pulse` · prefix `/api/agents/pulse` · cross-agent heartbeat
- `genes` · prefix `/api/genes` · capability gene library
- `skill_library` · prefix `/api/skills` · skill catalog
- `platform_proposal_reviews` · prefix `/api/platform/proposal_reviews` · governance review submissions
- `audit_service` · prefix `/api/audit/v1` + public `/api/audit` · audit dispatch facade (related to W4 audit closed loop · `feedback_first_principles_minimum_constitution`)
- `agent_welcome` · prefix `/api/agent/welcome` · agent onboarding

Replace the stub file with the real implementation in nautilus-core master via PR; cloud will pick up on next sync.

### Option B · Remove the orphan import line from main.py

For any subset that does not need to exist. Each removed line cleans up the import surface and shrinks the boot dependency graph. Send a PR; I will not block.

### Option C · Keep the stub as-is permanently

Leave the file as scaffolding. Boot-only stubs that never serve real traffic. Lowest-effort path; works fine for the modules where the import line is vestigial but cannot easily be removed without touching cross-cutting code.

You may mix-and-match (e.g. real impl for `mcp_gateway` + remove `genes`/`skill_library`/`agent_welcome` + keep stubs for the rest).

## 5 · One open ask (not in the menu)

If you choose Option C for any subset, please consider moving those stub files into origin/master so cloud's next clean sync doesn't keep depending on the in-place file present only on `soul-audit-increment1`. I will not push that change because the files are platform-turf scaffolding I want you to own.

## 6 · Inc 1.5 BINDING-DONE context (so you know this isn't urgent)

This inbound is a Session 3 close-loop item · NOT a blocker. Inc 1.5 is already BINDING-DONE per handoff #006: Path A wire end-to-end + Path B both phases verified · 2 draft PRs (#65 #67) opened by soul executor. The fix for the executor's `resolved_by IS NULL` gap (PR #66) merged to master 5/28 23:22 UTC as `d47e2c0bb`.

The 9 stubs were a precondition for any of the above to work on cloud (without backend up, no /pending endpoint, no governance_inject_loop target, no soul-executor pickup). They are not part of the Inc 1.5 design or required for the L3 contract.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) (Opus 4.7 · 1M context)

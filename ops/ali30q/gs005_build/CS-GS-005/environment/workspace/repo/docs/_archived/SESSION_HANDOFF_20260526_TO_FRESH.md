# Platform Dialog · Fresh Session Handoff · 2026-05-26 → next

> **Read this first** in next session before any action.

## TL;DR (5/26 session · ~3.5h)

- Shipped Option C quick wins (3 commits): emit-skip dry-run · CLI --cycle-id wire · README + Nautilus Soul mention. Tests 179 green.
- Brainstorming for Gap 1 (semantic guard) approved · design doc committed.
- Strategic path locked: **Path C** (Gap 1 + Gap 2 institutional first · 5h total · then re-decide A vs B).
- Master ahead origin **7** commits. Token rotate pending → user push manually after rotating.

## Master state · git

```
HEAD: <pending>      docs: brainstorming · Gap 1 semantic guard design (handoff 守门) + 5/26 handoff
      4df87f791      docs: introduce Nautilus Soul product name + root README subsection
      aeb1f5f5b      feat(cli): wire --cycle-id flag to engine ship (plan decision #5)
      e4660a37e      fix(engine): Stage 1 · skip emit for dry-run cycles (closes handoff Gap 2)
      d75e79b33      docs: implementation plan · 4 phases · TDD per item (writing-plans output)
      2fdb0c89f      docs: brainstorming approved · 3 quick wins design
      e160f0d51      docs: fresh-session handoff · platform dialog 2026-05-25 stop
```

## Active anchors (must hold)

| # | Anchor | Status |
|---|---|---|
| #1 | Agent first / protocol activation | Gap 5 (Stage 2 driver) is the long-term land — design path sketched in 5/26 strategic Q response |
| #2 | 30-day real customer land (deadline 2026-06-20 · 25 days remaining) | **STILL 0** — Option A OSS pivot deferred · Path C first (~5h) then re-decide A vs B |
| #5 | Schema audit cheatsheet | Held — Stage 1 schema still raw SQL bootstrap (alembic migration awaits Gap 3 cross-dialog) |
| #6 | Institutional guardrails | Path C aligns directly — Gap 1+2 close Stage 1 institutional holes before any ship-driver agent |
| #7 | Don't touch other dialogs' maintenance | Held — Gap 3 inbound to V5/Kairos/V7/compass still pending (not started this session) |

## Next session boot sequence

1. **Token rotate** (5/25 handoff hard prereq · still pending · revoke 2 exposed tokens + generate fine-grained PAT for chunxiaoxx/nautilus-core)
2. `git push origin master` (pushes 7+ commits ready locally)
3. `/clear` this session, start fresh
4. New session start prompt (cold pickup ready):
   > 走 writing-plans skill → executing-plans skill chain · 执行 `docs/plans/2026-05-26-gap1-semantic-guard-design.md` · 5 phases · TDD per check · master direct commits · 不 push · 不动 alembic.

The design doc has implementation sequence in the last section — writing-plans skill expands each phase to bite-sized RED → GREEN steps.

## Gap 1 design summary (locked decisions)

- **Trigger**: phrase OR existing-file > 50 LOC (closes "add X to Y" task class)
- **Line count thresholds**: shrink floor 0.85 · growth ceiling 2.0 (default) / 4.0 (allow_additions)
- **Docstring keywords**: 5 EN + 4 中文 = 9 keywords for change-allowed escape
- **Implementation**: 3 NEW independent functions in `phase3/backend/engine/checks.py` + 1 wiring update in `ship.py`
- **Tests**: 19 new (baseline 179 → 198 expected green after Gap 1 ship)

## Plan-phase decisions still in force (from 5/25 + 5/26)

1. DSN reuse `DATABASE_URL` env var
2. pytest convention `<dir>/tests/test_<basename>.py` only
3. Permissive Spec-Meta parser (malformed → NULL)
4. Hybrid cycle_id (`{YYYYMMDD}_{sha8(task)}` auto · `--cycle-id` override)
5. CLI `--cycle-id` flag (wired this session)
6. emit-skip guard: `apply=False AND no errors AND has blocks → skip emit` (this session)

## Out of scope (do not start in next session)

- Computer Use / Browser Harness / GUI desktop product layer
- Self_modify + outcomes integration (V5 dialog territory)
- GUI Electron / Tauri client
- Alembic versions/ touches (cross-dialog · Gap 3 awaits inbound)
- Backfill historic dry-run row in `engine_cycle_outcomes` (defer to Gap 2 next phase)
- Anchor #2 OSS pivot (re-decide after Gap 1+2 ship · ~5h)

## Test count summary

| Stage | Engine | CLI | Total |
|---|---|---|---|
| 5/25 master tip | 173 | 0 | 173 |
| Option C quick wins (5/26) | 177 | 2 | 179 |
| After Gap 1 ship (planned) | 196 | 2 | **198** |

## Things NOT to do in next session

- Don't push past R3 4h cap without explicit user override (Gap 1 ship estimate ~80 min · within cap)
- Don't touch `alembic/versions/` without cross-dialog coordination
- Don't invoke `brainstorming` for Gap 1 again — design is approved + committed
- Don't add LICENSE root file or rewrite root README again (Option A scope · re-decide after C)

## Linguistic drift reminder

5/25 handoff flagged "真" overload (17 in one response). This session held to ≤3/paragraph cap throughout. Continue replacing with `actually` / `其实` / `确实` / delete entirely.

— platform dialog · session handoff · 2026-05-26

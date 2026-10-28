# Platform Dialog · Fresh Session Handoff · 2026-05-27 → next

> **Read this first** in next session before any action.
> Supersedes `docs/SESSION_HANDOFF_20260526_TO_FRESH.md` (which assumed Gap 1
> ship would happen next session · actually shipped in 5/26 same session under
> user R3 override).

## TL;DR (5/26 session · ~4h · R3 cap explicitly overridden)

- **Path C complete**: Gap 1 (semantic guard) + Gap 2 (dogfood backfill) both shipped this session.
- Master ahead origin **13** commits · token rotate still pending → user push manually after rotating.
- Engine tests: 173 baseline → **196** green (177 quick-wins → +19 Gap 1 → 196). CLI: 2 green. v_engine_progress: avg_composite **1.000** verified.
- **Strategic decision locked**: A first (OSS pivot · 5-7 d to anchor #2 6/20 deadline) → B after (Stage 2 driver · 2-3 w · Gap 3-5).
- Dual-track A+B rejected explicitly per handoff 142-146 solo capacity warning.

## Master state · git

```
9ef65b80c  fix(engine): Gap 2 · backfill historic dogfood dry-run row (avg 0.875→1.000)
717161a55  feat(engine): Gap 1 · ship.py wires preservation checks
7f2929b8c  feat(engine): Gap 1 · should_apply_preservation_checks OR trigger
a1c24fbbd  feat(engine): Gap 1 · check_docstring_preserve guard (9 keywords · EN+中文)
a251f9222  feat(engine): Gap 1 · check_line_count guard (0.85/2.0/4.0)
9bcd4e993  docs: writing-plans · Gap 1 implementation plan (5 phases · 19 tests · TDD)
e6bfdf222  docs: brainstorming · Gap 1 semantic guard design + 5/26 handoff (superseded)
4df87f791  docs: introduce Nautilus Soul product name + root README subsection
aeb1f5f5b  feat(cli): wire --cycle-id flag (plan decision #5)
e4660a37e  fix(engine): Stage 1 · skip emit for dry-run cycles (closes handoff Gap 2 future)
d75e79b33  docs: implementation plan · 4 phases · TDD per item
2fdb0c89f  docs: brainstorming approved · 3 quick wins design
e160f0d51  docs: fresh-session handoff · platform dialog 2026-05-25 stop
```

## Active anchors

| # | Anchor | Status |
|---|---|---|
| #1 | Agent first / protocol activation | Stage 2 driver path locked for W3-6 · post anchor #2 deadline |
| #2 | 30-day real customer land (deadline 2026-06-20 · **25 days remaining**) | **PRIORITY for W1-2** — Path A OSS pivot is now the next-session focus |
| #5 | Schema audit cheatsheet | Held — Stage 1 schema still raw SQL (alembic migration in Gap 4 · post Gap 3 cross-dialog) |
| #6 | Institutional guardrails | Path C complete · 198 tests green · v_engine_progress avg=1.000 |
| #7 | Don't touch other dialogs' maintenance | Held — Gap 3 inbound to V5/Kairos/V7/compass still pending (W3+) |

## Strategic plan (locked 5/26)

### W1 (5/27 - 6/2) · Path A part 1

- A1 root LICENSE file (MIT vs Apache decision · setup.py says MIT · root README cites Apache 2.0 platform · resolve inconsistency)
- A2 README hero rewrite (D1 drift evidence + cycle 17 self-catch + Stage 1 closed-loop demo)
- A3 `nautilus-soul demo` 1-command wrapper (cycle 17 dogfood end-to-end)
- A4 dev.to article draft 1500-2000 words (git log + before/after fidelity)

### W2 (6/3 - 6/9) · Path A part 2

- A5 Show HN draft (title + 200w + comment FAQ pre-answered)
- A6 8-channel outreach kit refresh (`docs/ANCHOR2_OUTREACH_KIT_20260525.md` · Nautilus Soul rename)
- A7 PyPI publish (twine + Trusted Publishers + version tag)
- A8 1st dev pilot contact (founder Twitter/Discord/HN comment channels)

### W3 (6/10 - 6/20) · Anchor #2 land or fail

- Monitor dev.to / Show HN / outreach response
- Convert engagement to dev pilot LOI / star / paid customer (per "真客户" definition · TBD with user)
- 6/20 anchor #2 deadline · honest accounting

### W4-6 (6/21 - 7/11) · Path B (Stage 2 driver)

- B1 (Gap 3) cross-dialog 4 inbound · V5/Kairos/V7/compass · alembic 3 dup ID coordination
- B2 (Gap 4) Stage 1 schema 入 alembic migration (post-Gap 3)
- B3 (Gap 5) `engine/driver.py` v0 polling loop + cooldown + budget cap
- B4 N=1 closed-loop verify (driver ships 10 cycles · composite trend report)
- B5 trend up → expand · trend flat → diagnose · user decision

## Next session boot sequence

1. **Token rotate** (5/25 handoff hard prereq · STILL PENDING · revoke 2 exposed tokens + generate fine-grained PAT)
2. `git push origin master` (pushes 13 commits)
3. `/clear` this session, start fresh
4. New session start prompt (cold pickup):
   > Path A W1 启动 · brainstorming A1 (LICENSE 决断 · MIT vs Apache) → writing-plans → executing-plans skill chain · 不动 alembic · 不动 cross-dialog · 不动 Path B.

A1 LICENSE decision is the cleanest entry: zero-coupling decision (no test impact), unblocks A2 README hero (which links to LICENSE), and forces explicit reconciliation of root README (Apache 2.0 cited) vs setup.py (MIT). Recommended approach: keep MIT in setup.py · update root README to clarify "MIT for engine subpackage · platform layer separately Apache 2.0" · add root LICENSE file pointing to MIT.

## Plan-phase decisions still in force

1. DSN reuse `DATABASE_URL` env var
2. pytest convention `<dir>/tests/test_<basename>.py` only
3. Permissive Spec-Meta parser (malformed → NULL)
4. Hybrid cycle_id (`{YYYYMMDD}_{sha8(task)}` auto · `--cycle-id` override)
5. CLI `--cycle-id` flag (wired 5/26)
6. emit-skip guard: `apply=False AND no errors AND has blocks → skip emit` (5/26)
7. Semantic guard thresholds: shrink 0.85 / growth 2.0 / allow_add growth 4.0 (5/26 Gap 1)
8. Docstring escape keywords: 9 total (5 EN + 4 中文 · 5/26 Gap 1)
9. Preservation check trigger: phrase OR existing-file > 50 LOC (5/26 Gap 1)
10. Path A first then B sequential (5/26 strategic lock)

## Out of scope (do not start in next session)

- Path B work (Gap 3-5) — deferred to W4+
- Computer Use / Browser Harness / GUI desktop product layer
- Self_modify + outcomes integration (V5 dialog territory)
- GUI Electron / Tauri client
- Alembic versions/ touches (cross-dialog · Gap 3 awaits inbound in W4)
- Function-level / class-level docstring preservation (semantic guard scope frozen)
- Override flag for line_count false-reject (documented edge · not added)

## Test count summary

| Stage | Engine | CLI | Total |
|---|---|---|---|
| 5/25 master tip | 173 | 0 | 173 |
| 5/26 quick wins | 177 | 2 | 179 |
| 5/26 Gap 1 + Gap 2 | 196 | 2 | 198 |

All 198 green · 6 skipped (PG integration tests when DATABASE_URL unset).
v_engine_progress: ship_count=7 · avg_composite=1.000 · success_ratio=1.000.

## Tools added this session

- `tools/backfill_dogfood_row.py` · 1-shot idempotent DELETE of historic dogfood row · keep for cross-environment use (cloud PG when promoted)

## Things NOT to do in next session

- DON'T start Path B work this round — Path A W1-3 has priority for anchor #2 deadline
- DON'T touch `alembic/versions/` — cross-dialog coordination first (W4)
- DON'T re-run `tools/backfill_dogfood_row.py` on cloud PG without inspecting first — local dev DB already done
- DON'T push past R3 4h cap without explicit user override — A1 LICENSE decision is small (~30 min), A2 README hero is medium (~90 min)
- DON'T merge MIT vs Apache 2.0 license blindly · A1 decision needs user resolution

## Linguistic drift status

5/26 session held the 真/paragraph cap consistently. Continue replacement strategy (`actually` / `其实` / `确实` / delete entirely).

— platform dialog · session handoff · 2026-05-27

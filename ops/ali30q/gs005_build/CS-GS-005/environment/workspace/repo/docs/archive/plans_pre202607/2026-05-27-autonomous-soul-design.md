# Autonomous Nautilus Soul · Design

> Path: let Soul grow continuously (instead of being human-invoked via `nautilus code`).
> Brainstorming output · 2026-05-27 · design-only (no code shipped this session).
> 5 decisions locked with user. Execution deferred to fresh session via writing-plans.

## Strategic context + honest tension

User wants Soul to "grow up" autonomously. This design captures that vision BUT carries
a real tension flagged during brainstorming:

- **anchor #2** deadline is 2026-06-20 (24 days). The real fire is landing the first paid
  customer, not internal autonomy.
- memory (`truth_real_bucket_460_94pct_self_loop_20260518`) documents a 94% self-loop
  anti-pattern: platform serves itself, no external customers.
- An autonomous self-improving Soul, naively built, deepens that self-loop.

Platform-dialog pushed back (recommended outreach-first), user chose to proceed with Soul
autonomy anyway. This design therefore builds **anti-self-loop guards as first-class
components** (section 5), and the work is gated behind design+plan approval, not shipped
mid-session.

Persona-drift daemon flagged score=-0.061 (toward anti-anchor) when this design was
discussed — consistent with the tension above. Acknowledged, not suppressed.

## 5 locked decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Soul identity | **D · Hybrid** · tool + GitHub PR-bot · NO wallet · NO marketplace · output = OSS artifacts |
| 2 | Goal source | **D · priority queue** · goals.yaml > reflection > docs scrape |
| 3 | Cadence + budget | **Aggressive** · every 2h · unlimited cycles/run · ~$5-20/day hard cap |
| 4 | Resource scope | **All, phased** · MVP (own repo + public API + Google SA) → cross-repo read → auth platform + compass → skills-hub |
| 5 | Safety gate | **Standard** · PR draft only · max 500 LOC diff · file blacklist · N=5 consecutive-failure circuit breaker |

## Daemon location (resolved)

**C-corrected · independent clean workspace on cloud-server.**

Earlier I wrongly coupled "Soul on cloud" with "must run on the diverged `~/nautilus-mvp`".
That coupling was fictional. Soul only needs a clean origin-synced checkout.

```
~/nautilus-soul-workspace/   ← fresh git clone of origin/master · Soul-only · clean
~/nautilus-mvp/              ← the 79+commit diverged repo · Soul never touches · merge plan handles separately
```

Benefits: always-online (cloud) + clean checkout (origin synced) + zero dependency on the
cloud-origin merge plan + zero pollution of the diverged repo. **0 delay, fully decoupled.**

Soul workspace gets its own: DEEPSEEK_API_KEY, Google SA path, systemd timer (every 2h),
independent of `~/nautilus-mvp` backend cron.

## 1. Architecture · 7 components

```
soul-daemon (systemd timer · every 2h)
  1. budget_gate    daily cost / cycle counter · over cap → exit 0
  2. pause_check    .soul-pause file exists → exit 0
  3. goal_selector  priority queue: goals.yaml > reflection > docs scrape → 1 task
  4. engine.ship()  existing engine · dry_run → checks → preservation guards
  5. pr_gate        diff <=500 LOC · blacklist check · gh pr create --draft
  6. outcome_emit   write engine_cycle_outcomes (existing table)
  7. failure_track  N=5 consecutive fail → touch .soul-pause + GitHub issue alert
```

New code lives in `phase3/cli/nautilus_cli/` (or a new `soul/` package) — exact placement
decided in writing-plans. Reuses existing `engine.ship()`, `outcome_emit`,
`v_engine_progress`.

## 2. Cycle lifecycle (data flow)

```
cron 2h fire
  → budget_gate: today cost < $20 AND cycle quota OK? else exit 0
  → pause_check: .soul-pause present? yes → exit 0
  → goal_selector:
      goals.yaml has undone entry? → take highest priority
      else → reflection: v_engine_progress finds composite<0.7 cycle → retry
      else → docs scrape: README/handoff TODO/FIXME/Pending → take 1
  → engine.ship(task, dry_run=True):
      LLM gen (deepseek-v4-pro) → ast checks → preservation guards → compute diff LOC
  → pr_gate:
      diff >500 LOC? → reject + log + no PR
      hits blacklist (.env/alembic/migrations/contracts/secrets/_dead_code_backup)? → reject
      pass → git branch soul/<cycle_id> + commit + gh pr create --draft
  → outcome_emit: composite score + pr_url → engine_cycle_outcomes
  → failure_track: 5 consecutive cycle failures (checks fail OR pr_gate reject)?
      → touch .soul-pause + create GitHub issue alert
```

## 3. Safety · Inversion of Control (core)

The user asked Claude to "stand guard." Claude is session-bound and cannot. Safety must be
**in-code, 4 layers**:

1. **PR draft only** — Soul never auto-merges. Human reviews draft PR then merges. Human is
   the final gate.
2. **Budget hard cap** — daily $20 + cycle quota. Over cap → daemon self-halts. Writes cost
   ledger (`~/nautilus-soul-workspace/.soul-cost-ledger.jsonl`).
3. **Blacklist + diff cap** — touching `.env`/`alembic`/`migrations`/`contracts`/`secrets`/
   `_dead_code_backup` → reject. Single PR >500 LOC → reject.
4. **Failure circuit breaker** — N=5 consecutive failures → `touch .soul-pause`. Daemon
   sees this file and sleeps. Requires manual `rm .soul-pause` to resume.

All 4 are code/filesystem/systemd mechanisms, not conversational reminders (per anchor #6:
don't rely on "I'll remind myself").

## 4. Phased resource rollout

| Phase | Resource | Prerequisite |
|---|---|---|
| **P0 MVP** | own repo + public platform API + Google SA Vertex AI fallback | none · ships first |
| **P1** | cross-repo read (V5/Kairos/Compass docs · GitHub raw via PAT) | V5/Kairos/Compass dialog consent (anchor #7 inbound) |
| **P2** | authenticated platform API + Compass memory layer (recall/ingest/drift) | compass-dialog consent + Soul gets a nautilus API key |
| **P3** | skills-hub external API | research skillhub.cn API doc first · confirm product fit |

P1-P3 each gated on cross-dialog sign-off. MVP (P0) ships standalone.

## 5. Anti-self-loop guard (anchor #2 critical)

memory warns of 94% self-loop recurrence. Built-in countermeasures:

- `goals.yaml` top section pins **anchor #2 external-facing goals** (README hero rewrite,
  dev.to article draft, demo upgrades, outreach artifacts). These rank **above** reflection
  (engine self-improvement).
- Weekly outcome report splits into 2 buckets: **external-facing artifacts** (OSS pivot
  contribution) vs **internal self-improvement**. If external bucket < 50% → alert "Soul is
  self-looping again."
- Reflection-class tasks have a daily cap (e.g. <=2/day) to prevent Soul spending all cycles
  on self-refactoring.

## 6. Cost model

- deepseek-v4-pro ~$0.001-0.005/cycle · every 2h = 12 fires/day
- unlimited cycles/fire BUT daily $20 hard cap → natural limit ~4000-20000 cycles/day
  (real goals queue can't feed that many · realistic ~10-50 cycles/day)
- ~$5-20/day · ~$150-600/month · Google SA Vertex AI fallback lowers average
- Cost ledger written per cycle · budget_gate reads it

## 7. Success metrics

- **Health**: daemon uptime · 0 budget breach · 0 blacklist violation · 0 auto-merge
- **Output**: draft PRs/week · human merge rate · external-artifact bucket share > 50%
- **Anti-loop**: external/internal bucket ratio reported weekly · < 50% external = fail
- **anchor #2 contribution**: how many Soul PRs directly feed A2/A4/A5/A6 outreach

## 8. Out of scope

- Soul wallet / NAU / marketplace participation (excluded by decision D)
- Auto-merge (always human review)
- Cross-repo WRITE (own repo PR only)
- alembic / migrations / contracts edits (blacklist)
- Path B needs_review extension (separate work)
- Running on the diverged `~/nautilus-mvp` (uses independent clean workspace instead)
- skills-hub in MVP (P3 · after research)

## Open items for writing-plans

1. Exact package placement (`soul/` new package vs extend `nautilus_cli/`)
2. `goals.yaml` schema (priority · category · status · acceptance criteria)
3. Reflection query exact SQL against `v_engine_progress`
4. docs-scrape parser rules (which files · which markers)
5. systemd timer unit + service file for `~/nautilus-soul-workspace`
6. Bootstrap script: clone origin → set env → install deps → enable timer
7. Cost ledger format + budget_gate read/write logic
8. GitHub issue alert mechanism (gh CLI · which repo · labels)
9. P0 acceptance test: dry-run 1 full cycle end-to-end, confirm draft PR created

## Risks

- **Self-loop drift** — mitigated by section 5 but needs weekly human check of bucket ratio
- **Cost runaway** — mitigated by daily hard cap + cost ledger
- **Bad PRs flooding** — mitigated by draft-only + N=5 breaker + human merge gate; aggressive
  2h cadence means review queue could still grow · human must triage daily
- **Cross-dialog friction** — P1-P3 stall if other dialogs don't consent; MVP unaffected
- **Strategic distraction** — building Soul autonomy during anchor #2 crunch may divert from
  the real fire (customer acquisition). User accepted this trade-off explicitly.

## Next step

Invoke writing-plans skill → `docs/plans/2026-05-27-autonomous-soul-plan.md`. No code this
session. Execution in a fresh session, MVP (P0) first.

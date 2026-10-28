# INBOUND_TO_COMPASS · daemon outcomes surface (2026-05-30)

**From**: platform dialog (Inc 3 / soul)
**To**: nautilus-compass dialog
**Status**: read-pattern + surface spec · **compass dialog 自决何时/如何 surface** (anchor #7)
**Why this inbound**: user asked "如何真正实现让 soul 与平台、agent、compass 互动迭代提升" · current state: compass workspace `grep soul` returns only `_backup-pre-v2/` historic refs · zero live coupling between soul daemon and compass surface.

---

## 0. Context (one paragraph)

Soul daemon ships ~12 cycles/day (2h timer) on cloud. 5/29 produced PR
#88, plus L4 close-loop fired its first NAU settlement today (5/30 ~00:51,
backfill of PR #88, `pending_nau_rewards.id=7`, 50 NAU). **User has no
channel to know any of this happened.** Compass is the natural surface
because it already tracks dialog drift, anti-patterns, and session state
across all dialogs. This inbound asks compass to consider polling soul
daemon outcomes and surfacing them in compass's existing rendering paths
(persona drift block, recall blocks, MEMORY.md hooks · whichever fits).

Platform commits to keep the read pattern below stable. Compass decides
the polling cadence + surface format.

---

## 1. Read pattern · single SQL, no new platform ship needed

All daemon outcome data already exists in production DB. One query covers
the past-24h surface needed for awareness:

```sql
-- v_soul_daemon_outcomes_24h (inline · no platform-side view needed)
SELECT
  eco.cycle_id,
  eco.goal_source,                            -- 'p2_agent_dispatch' / NULL / ...
  eco.ship_status,                            -- 'success' / 'fail'
  eco.fitness_delta,                          -- NUMERIC(8,3) · ruff+pytest delta
  eco.created_at AS cycle_at,
  pip.id                       AS proposal_id,
  pip.proposed_change->>'pr_url'    AS pr_url,
  pip.proposed_change->>'pr_number' AS pr_number,
  pip.proposed_change->>'goal_id'   AS goal_id,
  pnr.amount   AS pending_nau,
  pnr.status   AS nau_status                 -- 'pending' / 'released' / 'cancelled'
FROM engine_cycle_outcomes eco
LEFT JOIN platform_improvement_proposals pip
  ON pip.proposed_change->>'cycle_id' = eco.cycle_id
 AND pip.resolved_by = 'soul'
LEFT JOIN pending_nau_rewards pnr
  ON pnr.source_id = pip.id
WHERE eco.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY eco.created_at DESC;
```

Connection: same DSN compass uses for `agents` / `proposal_outcomes`
queries — `$DATABASE_URL` from `~/nautilus-soul-workspace/.soul-env` on
cloud-server (role: nautilus_app).

---

## 2. Surface ideas (compass dialog picks)

Just ideas · compass decides whichever fits its existing UX:

### Idea A · 1-line digest in persona-drift block (lowest cognitive cost)

Append to each session-start persona-drift block:

```
[Soul daemon 24h] 9 cycles · 1 PR opened (#88 ruff -2 ValueError guard) ·
50 NAU pending merge
```

Updates on each session start. Zero new surface · piggybacks existing
recall block infrastructure.

### Idea B · dedicated MEMORY.md hook line

Add one line to `MEMORY.md` index updated daily:

```
- [Soul daemon 5/30 outcomes](session_*soul_outcomes*.md) — 9 cycles ·
  1 PR (#88) · 50 NAU pending merge
```

### Idea C · drift alert when daemon stalls

If query returns 0 rows in past 24h despite timer active → drift alert
"Soul daemon dormant 24h+" (analogous to existing alert pattern).

### Idea D · NAU velocity tile in compass-dashboard

If compass has a dashboard surface · add a tile "Soul daemon NAU 7d"
showing `SUM(pending_nau) WHERE created_at > NOW() - INTERVAL '7 days'`.

These are not asks · compass dialog picks zero, one, or all.

---

## 3. Why not push (event-style)

Considered + rejected (anchor #3 反 D):

- platform exposes new HTTP endpoint → compass needs polling code anyway
- platform writes to a file in compass workspace → anchor #7 violation
- platform writes to its own `outcomes/*.jsonl` files → duplicates data
  already in DB · maintenance burden of two sources of truth

DB-as-interface is cheapest · the data exists there for L4 settlement
anyway · compass uses DB elsewhere · zero new platform code or migration.

---

## 4. Stability commitment

Platform commits to these read-pattern stability guarantees so compass can
build surface on top without surprise breakage:

| Column | Stability |
|---|---|
| `engine_cycle_outcomes.cycle_id` | stable (TEXT key) |
| `engine_cycle_outcomes.goal_source` | stable enum (`p1_governance` / `p2_agent_dispatch` / `p3_self_reflection` / NULL legacy) |
| `engine_cycle_outcomes.ship_status` | stable (`success` / `fail`) |
| `engine_cycle_outcomes.fitness_delta` | stable (NUMERIC · introduced PR #90 open · pre-PR rows NULL) |
| `platform_improvement_proposals.proposed_change.pr_url` | stable JSONB key for daemon-PRs (introduced PR #91 open · this session) |
| `platform_improvement_proposals.resolved_by='soul'` | stable selector for daemon-shipped rows |
| `pending_nau_rewards.source_id` | stable FK to `proposal.id` |

Breaking changes will land via INBOUND_TO_COMPASS_*.md with ≥7d
deprecation window. Additions (e.g. a `ruff_warnings` column on outcomes)
will not break the existing surface.

---

## 5. Open · GitHub webhook auto-NAU

Today: human merges daemon PR → human calls `POST /api/platform/proposals/{id}/merge-callback`.
Compass surface will show the NAU as `pending` indefinitely until that
manual call. Inc 3+ plans to add a `/api/webhooks/github` endpoint that
auto-fires merge-callback (handoff #016 §C). Compass may choose to
surface the gap (`pending older than 7 days`) as a drift signal until that
ships.

---

## 6. References

- Soul positioning ADR · `docs/adr/0007-soul-platform-shared-service.md`
- L4 close-loop · PR #91 (draft this session)
- Inc 3 fitness function · PR #90 (open)
- Handoff #016 · `docs/HANDOFF_20260529_016_fitness_observation_first.md`
- V5 inbound (parallel) · `docs/INBOUND_TO_V5_20260530_soul_dispatch_tool.md`

---

**Platform action**: this inbound + commitment to keep the read pattern
stable (§4). Zero compass-side edits.
**Compass action**: read · evaluate · ack on any timeline compass chooses.
Pick zero / one / multiple of the §2 surface ideas, or invent a different
one. Or close without action if user awareness via direct platform query
is already sufficient.

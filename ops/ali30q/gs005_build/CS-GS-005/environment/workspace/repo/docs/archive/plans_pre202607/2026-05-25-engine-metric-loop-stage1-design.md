# Engine Metric Closed-Loop · Stage 1 Wire · Design

> **Author**: platform-dialog
> **Date**: 2026-05-25
> **Status**: Design approved · awaiting implementation plan
> **Goal**: 30 天将 engine recursive self-improvement composite_score 从基线 → 0.80
> **Related**: `docs/WEDGE_PIVOT_DECISION_AUDIT_20260525.md` · `memory/foundation_audit_recursive_closed_loop_gram_fused_20260523.md` · `memory/plan_phase2_karpathy_council_auction.md`

---

## 1. Context

### 1.1 当前 engine state (master tip `3739410cb`)

- Engine MVP cycle 1-9 production · 88 unit + 6 cloud PG tests GREEN · 17 commits
- Cycle 12-16 在 PR #46 (engine-cycle-12-15-16-2026-05-25 · awaiting review): MINIMAL CHANGE MODE prompt · ast semantic_preservation check · few-shot · file context injection · allow_additions policy
- Cycle 17 / D1 在 PR #47 (today): `truncate` edge case fix + dogfood drift evidence proving cycle 12-16 load-bearing

### 1.2 What "recursive self-improvement" already works

✅ **Single-step self-bootstrap done once**: Cycle 15 — engine 用自己的 RAID-2 council pipeline ship 出 `_inject_file_context` (Karpathy Fix 1) · 38 LOC · 0 manual edits · git trail 完整

### 1.3 What's missing for a real closed-loop

| Gap | Current | Needed |
|---|---|---|
| Goal | Scattered in docs (anchor #2 / Karpathy / wedge) | Single queryable `improvement_goals` schema with metric + target + deadline |
| Self-improve signal | cycle 15 was one-shot · no trigger for next round · no "is this better" metric | Per-cycle outcome metric (composite_score) persisted to platform DB |
| Platform ↔ engine coupling | 0 · engine ship doesn't write platform · platform doesn't review engine | `engine_cycle_outcomes` table populated by ship.py hook |
| Agent ↔ engine | V5/Kairos/V7 have mcp/a2a/spool tools · don't auto-plan "what engine should improve next" | Stage 2 `improvement-driver` agent (out of scope here) |
| Continuous loop | Existing crons handle governance/health/bounty · none drive self-improvement | Stage 2 driver cron (out of scope here) |

### 1.4 Stage roadmap

- **Stage 1 (THIS DOC · 4-7 days · ~300 LOC)** — Wire metric closed-loop "eye". Read-only after ship.
- **Stage 2 (2-3 weeks · separate plan)** — `improvement-driver` agent reads outcomes + goals · LLM-plans next spec · drives engine ship. First real N=1 closed loop.
- **Stage 3 (1-2 months · uses `plan_phase2_karpathy_council_auction.md`)** — Multi-agent recursive (3-stage council auction · parallel blind proposal · anonymous peer review · chairman arbitration).

---

## 2. Goal & North Star

**North Star**: 30 天内 engine `composite_score` rolling 7-day average 从 baseline → 0.80。

**Why composite (not LLM-judge fidelity)**:
- `fidelity_checker` (Karpathy Fix 2 · LLM-as-judge) 未 ship · 且 compass dialog 5/21 audit 暴露其前身被 hack 风险高 (quality 0.51 baseline + 100% success 虚标)
- Composite 由 3 个 **mechanical ground-truth signals** 合成 · hack 必 break compile/test/git-diff · 比 LLM-judge sturdier
- Stage 1 完成后 Karpathy Fix 2 ship 可加为 composite 第 4 项 · 此时已有 mechanical baseline 做 reward-hacking 对比

---

## 3. Architecture

### 3.1 Data flow

```
┌─────────────────────────────────────────────────────────┐
│  engine ship pipeline (phase3/backend/engine/ship.py)    │
│                                                          │
│  1. generate → parse → stage → check → audit (existing) │
│  2. (NEW) compute composite metric:                      │
│      semantic_pass  — cycle 12 P1 AST check (existing)  │
│      tests_pass     — pytest run (NEW)                  │
│      drift_ratio    — git diff vs spec_expected (NEW)   │
│      composite     = (sem + tests + clamp(1-drift)) / 3 │
│  3. (NEW) classify outcome:                              │
│      success | partial | fail | deadletter             │
│  4. (NEW) emit to platform DB                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Platform PostgreSQL                                     │
│                                                          │
│  engine_cycle_outcomes — true ship outcomes              │
│  engine_cycle_deadletter — environmental errors          │
│  v_engine_progress — 30-day rolling histogram view       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                   read-only query
              (humans, future driver agent)
```

### 3.2 Components

**A. Schema (alembic migration · ~60 LOC)**

```sql
CREATE TABLE engine_cycle_outcomes (
    cycle_id              text PRIMARY KEY,
    spec                  text NOT NULL,
    spec_expected_added   int,                    -- nullable for legacy specs
    spec_expected_removed int,
    ship_status           text NOT NULL CHECK (ship_status IN ('success','partial','fail')),
    semantic_pass         bool,
    tests_pass            bool,
    actual_lines_added    int,
    actual_lines_removed  int,
    drift_ratio           numeric(6,3),           -- nullable when spec_expected_* null
    composite_score       numeric(6,3) NOT NULL,
    git_sha               text,
    cert_id               text,
    created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_engine_outcomes_created ON engine_cycle_outcomes(created_at DESC);

CREATE TABLE engine_cycle_deadletter (
    cycle_id    text,
    reason      text NOT NULL CHECK (reason IN ('parse_error','runtime_crash','retry_exhausted','db_emit_failed')),
    raw_error   text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_engine_dl_created ON engine_cycle_deadletter(created_at DESC);

CREATE VIEW v_engine_progress AS
  SELECT date_trunc('day', created_at)::date AS day,
         count(*)                              AS ship_count,
         avg(composite_score)::numeric(6,3)    AS avg_composite,
         avg(drift_ratio)::numeric(6,3)        AS avg_drift,
         (sum(CASE ship_status WHEN 'success' THEN 1 ELSE 0 END)::float
            / nullif(count(*),0))::numeric(6,3) AS success_ratio
  FROM engine_cycle_outcomes
  WHERE created_at > now() - interval '30 days'
  GROUP BY 1
  ORDER BY 1;
```

**B. ship.py classify + metric compute (~80 LOC)**

New module `phase3/backend/engine/outcomes.py`:

```python
def classify(result: ShipResult) -> str:
    # 'success' | 'partial' | 'fail' | 'deadletter'
    ...

def compute_composite(semantic: bool|None, tests: bool|None, drift: float|None) -> float:
    # Degrade gracefully when any signal None.
    signals = []
    if semantic is not None: signals.append(int(semantic))
    if tests is not None:    signals.append(int(tests))
    if drift is not None:    signals.append(max(0.0, min(1.0, 1.0 - drift)))
    return sum(signals) / max(1, len(signals))

def parse_spec_meta(task: str) -> dict:
    # Returns {"expected_added": int|None, "expected_removed": int|None}
    ...
```

`ship.py` adds final step before return:

```python
outcome = _build_outcome(result, base, task)
_emit_outcome(outcome)  # DB or deadletter or jsonl fallback
```

**C. pytest runner integration (~40 LOC)**

New module `phase3/backend/engine/pytest_runner.py`:

```python
def run_pytest_for_changed(base: Path, applied_paths: list[str]) -> bool:
    # Map applied source files → corresponding test files (simple convention:
    # path/to/foo.py → path/to/tests/test_foo.py · skip if no test file).
    # Run pytest -q · return True iff exit 0.
    ...
```

**D. DB emit + dead-letter routing + jsonl fallback (~50 LOC)**

New module `phase3/backend/engine/outcome_emit.py`:

```python
def emit_outcome(row: dict, db_url: str|None = None) -> None:
    # 1. Try INSERT into engine_cycle_outcomes via psycopg.
    # 2. On any DB exception → write to local .engine-outcomes.jsonl AND
    #    insert deadletter row 'db_emit_failed' (best-effort second attempt).
    # 3. Both fail → only jsonl + stderr warn (never raise · ship must not break).
    ...
```

**E. Spec format extension (~20 LOC)**

`spec_meta` block appended to `task` string:

```
<existing task text>

Spec-Meta:
  expected_added: 2
  expected_removed: 0
```

Backward-compat: missing block → `expected_added/removed = NULL` · `drift_ratio = NULL` · `composite_score = (semantic + tests) / 2` (degraded).

**F. Tests (~50 LOC)**

- Unit: `test_outcomes.py` — classify · compute_composite · parse_spec_meta
- Integration: full ship + emit dry-run with mock LLM on a text_utils-like task

---

## 4. Error handling

| Failure mode | Behavior |
|---|---|
| LLM produced no parseable blocks | `deadletter` reason=`parse_error` |
| Python exception in ship pipeline | `deadletter` reason=`runtime_crash` (caught at top of `_emit_outcome`) |
| `max_retries` exhausted with check fail | `fail` status in main table (not deadletter — meaningful negative sample) |
| DB connection refused | `jsonl` fallback file + best-effort deadletter `db_emit_failed` |
| Spec lacks `Spec-Meta:` | `drift_ratio = NULL` · `composite_score = (sem + tests) / 2` · `ship_status` still computed |
| pytest timeout > 60s | `tests_pass = NULL` (signal unavailable · not False — avoid false-fail bias) |

**Invariant**: `_emit_outcome` MUST never raise. Ship pipeline correctness must not depend on telemetry success.

---

## 5. Backfill + dogfood plan

### 5.1 Backfill historical cycles (Day 5)

Manual annotation for 6 historical cycles:

| Cycle | Commit | Source | spec_expected_added | spec_expected_removed |
|---|---|---|---|---|
| 5 | (engine-cycle-5) | session memory | TBD | TBD |
| 5b | (engine-cycle-5b) | session memory | TBD | TBD |
| 9 | `f6ba569d7` | git show | 18 | 0 |
| 12 P0 | `343fd53ef` | git show | TBD | TBD |
| 15 | `e4f5aca40` | git show | 38 | 0 |
| 17 / D1 | `13752bb7a` | today | 2 | 0 |

Compute baseline composite for these 6 → establish "0.51 → 0.80" trajectory anchor.

### 5.2 Dogfood Stage 1 (Day 6-7)

Use engine cycle 12-16 pipeline (PR #46) to ship `phase3/backend/engine/outcomes.py` itself:

- cycle_id: `stage1_self_emit_2026-05-XX`
- spec: `_build_outcome` function signature + body
- spec_expected_added: ~30 · spec_expected_removed: 0
- Verifies: cycle 15 self-bootstrap pattern is repeatable on Stage 1 components

---

## 6. Scope decisions (explicit non-goals)

❌ **Driver agent** — Stage 2. Stage 1 is read-only outcomes recording.
❌ **`fidelity_checker` (Karpathy Fix 2)** — W2 ship · adds as composite signal #4 later.
❌ **Multi-agent council auction** — Stage 3 · uses existing `plan_phase2_karpathy_council_auction.md`.
❌ **Web UI for `v_engine_progress`** — Stage 1 read via psql or future dashboard.
❌ **Driving Anchor #2 OSS pivot** — Orthogonal to this loop. Per user choice 2026-05-25 · loop targets internal engine quality, not external buyers. Anchor #2 stays on separate track (see WEDGE_PIVOT_DECISION_AUDIT § 6 Option F · deferred).

---

## 7. LOC budget

| Component | LOC |
|---|---|
| alembic migration | 60 |
| `outcomes.py` (classify + compute) | 80 |
| `pytest_runner.py` | 40 |
| `outcome_emit.py` (DB + jsonl + deadletter) | 50 |
| `ship.py` hook | 20 |
| spec format parser (inside `outcomes.py`) | 20 |
| Tests (unit + integration) | 50 |
| **Total** | **~320** |

Slightly over 200 LOC original Stage 1 estimate (because user picked dead-letter table). Acceptable for 4-7 day budget.

---

## 8. Open questions (for plan phase · not blocking design approval)

1. Which Postgres DSN? Re-use `agent_engine` config or new env var `ENGINE_METRICS_DB_URL`?
2. `pytest_runner.py` test-file convention: `path/to/foo.py` → `path/to/tests/test_foo.py` only · or also `tests/test_<basename>.py` at module root?
3. Spec-Meta block parser strict (reject malformed) or permissive (warn + NULL)?
4. `cycle_id` generation: SHA256 of (task + ts)? Or human-readable like `D1_2026-05-25_truncate_edge`?
5. Should `engine ship` CLI gain `--cycle-id` flag (override auto-generated)?

These are plan-level decisions · covered when invoking writing-plans skill next.

---

## 9. Approval

Design approved by user 2026-05-25 via session AskUserQuestion.

Next step: invoke `writing-plans` skill to generate per-day implementation steps.

— platform dialog · 2026-05-25

# FDE Verdict-Bus Contract (W1 · 4-way coupling event spine)

> Platform OWNs the verdict-bus. compass / v5 / soul are consumers/producers.
> Schema locked 2026-06-05 with the compass PoI consumer.
>
> **STATUS 2026-06-06 · PRODUCTION LIVE ✅** — `fde_verdicts` table + `GRANT
> SELECT TO compass_sub` applied on nautilus_production (verified: 11 cols,
> items/artifacts jsonb, role_table_grants = compass_sub|SELECT). V5 loaded 4
> real verdicts (data_001 1.0 / data_002 0.833 / data_003 fail 0.917 / data_004
> 0.75 · source=fde-capsule-v5), platform idempotent-verified present. compass
> runs `ops/fde_verdict_reconcile.py` → settle → PoI live = FDE verdict→PoI loop
> closed. Three-framework aligned on `fde_verdicts` (zero divergence; V5's
> reuse/ALTER was for the SEPARATE event spine `platform_external_events`).

## Why

The FDE live loop (v5 产物 → soul QC → compass PoI → 用户感知) wrote checklist
verdicts to a shared file + an invisible DB write. `fde_verdicts` persists them as
the platform substrate's first-class event — the **external buyer-acceptance
fitness signal** (the only fitness that escapes the self-referential internal
economy; anchor #3). Two real verdicts already exist to replay: **data_001
(11/11)** and **data_002 (overall_pass, 10/12)**.

Deliberately SEPARATE from `engine_cycle_outcomes` (internal RSI semantics). Do
not merge.

## Table: `fde_verdicts`

| column        | type              | notes |
|---------------|-------------------|-------|
| id            | SERIAL PK         | surrogate |
| verdict_id    | VARCHAR(200) UNIQUE NOT NULL | **idempotency / dedup key** |
| task_uid      | VARCHAR(120) NOT NULL | e.g. `data_001` · **PoI credit attribution** |
| source        | VARCHAR(32) NOT NULL | producer: `v5` \| `soul` |
| checklist_uid | VARCHAR(200)      | which RUBRIC §9 checklist scored it |
| overall_pass  | BOOLEAN NOT NULL  | verdict gate |
| veto_failed   | BOOLEAN NOT NULL  | true → forced fail (否决项) |
| score         | DOUBLE PRECISION NOT NULL | passed/total · **compass PoI delta** |
| items         | JSONB NOT NULL    | `[{id, pass, veto, reason}]` · 打回 reason = 避坑 feed (W6) |
| artifacts     | JSONB             | deliverable paths |
| created_at    | TIMESTAMP NOT NULL DEFAULT NOW() | PoI settle window |

Indexes: `verdict_id`, `task_uid`, `(task_uid, created_at)`.

Migration: `phase3/backend/alembic/versions/a7f3c1d2e4b5_fde_verdicts.py`
(idempotent `CREATE TABLE IF NOT EXISTS`).

## Ingest API (platform owns)

- `POST /api/platform/fde/verdict` — body = the verdict json (fields above).
  Idempotent on `verdict_id` (re-ingest returns the stored row with
  `idempotent: true`, never duplicates). Required: verdict_id, task_uid, source,
  overall_pass, score. `items` must be a list.
- `GET /api/platform/fde/verdict/{task_uid}` — read back all verdicts for a task,
  most recent first. Envelope: `{success, data, error}`.

## compass read path (compass owns the PoI mapping · G-turf: platform does not touch it)

compass `from_checklist_verdict()` reads `fde_verdicts` directly (read-only) and
maps verdict → PoI. The platform guarantees the column contract above; the
PoI boost logic stays in compass.

Contract fields compass depends on (drift-guarded by
`tests/test_fde_verdict_contract.py`): `verdict_id, task_uid, overall_pass,
veto_failed, score, items, created_at`.

> **2026-06-06 compass ack (rule A):** `source` is NOT a compass dependency
> (题级 PoI credit keys on `task_uid` only). The table keeps the `source` column
> for soul-activity / producer attribution, but compass's reader does not select
> it. The event spine (`platform_external_events`) is a SEPARATE table (V5
> reuse+non-breaking-ALTER, anchor #5) — distinct from this verdict-bus, zero
> impact on the compass read path.

Example read:

```sql
SELECT verdict_id, task_uid, source, overall_pass, veto_failed, score, created_at
FROM fde_verdicts
WHERE created_at > :since
ORDER BY created_at ASC;
```

## Cloud apply runbook (GATED · run via SSH on nautilus_production · G-cloud)

```sql
-- 1. DDL (idempotent · same as the alembic migration body)
CREATE TABLE IF NOT EXISTS fde_verdicts (
    id            SERIAL PRIMARY KEY,
    verdict_id    VARCHAR(200) NOT NULL UNIQUE,
    task_uid      VARCHAR(120) NOT NULL,
    source        VARCHAR(32)  NOT NULL,
    checklist_uid VARCHAR(200),
    overall_pass  BOOLEAN      NOT NULL DEFAULT FALSE,
    veto_failed   BOOLEAN      NOT NULL DEFAULT FALSE,
    score         DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    items         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    artifacts     JSONB        DEFAULT '{}'::jsonb,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fde_verdict_verdict_id   ON fde_verdicts (verdict_id);
CREATE INDEX IF NOT EXISTS idx_fde_verdict_task_uid     ON fde_verdicts (task_uid);
CREATE INDEX IF NOT EXISTS idx_fde_verdict_task_created ON fde_verdicts (task_uid, created_at);

-- 2. GRANT read to the compass subscriber (minimal · SELECT only)
GRANT SELECT ON fde_verdicts TO compass_sub;
```

After cloud apply: compass's live PoI read path is unblocked. Until then,
compass can build/test `from_checklist_verdict()` against the locked schema +
the local ingest endpoint.

## Local verification evidence (2026-06-05)

- `tests/test_fde_verdict_model.py` — 3 green (sqlite roundtrip, UNIQUE idempotency, veto/reason persist)
- `tests/test_fde_verdict_api.py` — 4 green (POST+GET readback, idempotent, missing-field reject, empty-task)
- `tests/test_fde_verdict_contract.py` — 3 green (PoI field drift guard)
- Real postgres (localhost:5433) scratch DB: DDL applied, JSONB columns confirmed (`jsonb_typeof(items)=array`), idempotent re-run, roundtrip `items->0->>'id'`.

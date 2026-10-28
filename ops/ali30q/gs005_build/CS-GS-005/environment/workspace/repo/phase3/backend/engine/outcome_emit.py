"""Stage 1 · emit cycle outcome row to platform PG (raw SQL bypass alembic).

Per docs/plans/2026-05-25-engine-metric-loop-stage1-design.md.

PLAN DEVIATION: Day 1 ships raw SQL `CREATE TABLE IF NOT EXISTS` schema
bootstrap on first emit · NOT alembic migration. Reason: existing alembic
versions/ has 3 duplicate revision IDs + multi-head · fixing is cross-dialog
institutional change (V5/Kairos/V7 all share alembic chain). Stage 2 pre-ship
will add proper alembic migration with IF NOT EXISTS guards to re-sync.

INVARIANT: emit_outcome MUST NEVER raise. Ship pipeline correctness must
not depend on telemetry success. All failures degrade silently to jsonl
fallback + stderr warn.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Plan-phase decision #1: reuse DATABASE_URL (no new env var)
_DEFAULT_DSN_ENV = "DATABASE_URL"

# Local fallback when DB unavailable
_JSONL_FALLBACK = Path(".engine-outcomes.jsonl")

# DDL · idempotent · safe to run on every emit
_DDL_OUTCOMES = """
CREATE TABLE IF NOT EXISTS engine_cycle_outcomes (
    cycle_id              text PRIMARY KEY,
    spec                  text NOT NULL,
    spec_expected_added   int,
    spec_expected_removed int,
    ship_status           text NOT NULL CHECK (ship_status IN ('success','partial','fail')),
    semantic_pass         boolean,
    tests_pass            boolean,
    actual_lines_added    int,
    actual_lines_removed  int,
    drift_ratio           numeric(6,3),
    composite_score       numeric(6,3) NOT NULL,
    git_sha               text,
    cert_id               text,
    created_at            timestamptz NOT NULL DEFAULT now()
);
"""

_DDL_OUTCOMES_INDEX = """
CREATE INDEX IF NOT EXISTS idx_engine_outcomes_created
    ON engine_cycle_outcomes(created_at DESC);
"""

_DDL_DEADLETTER = """
CREATE TABLE IF NOT EXISTS engine_cycle_deadletter (
    cycle_id    text,
    reason      text NOT NULL CHECK (reason IN ('parse_error','runtime_crash','retry_exhausted','db_emit_failed')),
    raw_error   text,
    created_at  timestamptz NOT NULL DEFAULT now()
);
"""

_DDL_DEADLETTER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_engine_dl_created
    ON engine_cycle_deadletter(created_at DESC);
"""

_DDL_VIEW = """
CREATE OR REPLACE VIEW v_engine_progress AS
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
"""

_SCHEMA_BOOTSTRAPPED = False  # in-process cache · skip DDL after first success


def _get_dsn(override: str | None = None) -> str | None:
    if override:
        return override
    return os.environ.get(_DEFAULT_DSN_ENV)


def _bootstrap_schema(conn: Any) -> None:
    """Run idempotent DDL · CREATE IF NOT EXISTS · safe to call repeatedly."""
    global _SCHEMA_BOOTSTRAPPED
    if _SCHEMA_BOOTSTRAPPED:
        return
    with conn.cursor() as cur:
        cur.execute(_DDL_OUTCOMES)
        cur.execute(_DDL_OUTCOMES_INDEX)
        cur.execute(_DDL_DEADLETTER)
        cur.execute(_DDL_DEADLETTER_INDEX)
        cur.execute(_DDL_VIEW)
    conn.commit()
    _SCHEMA_BOOTSTRAPPED = True


def _insert_outcome(row: dict, conn: Any) -> None:
    sql = """
        INSERT INTO engine_cycle_outcomes (
            cycle_id, spec, spec_expected_added, spec_expected_removed,
            ship_status, semantic_pass, tests_pass,
            actual_lines_added, actual_lines_removed,
            drift_ratio, composite_score, git_sha, cert_id
        ) VALUES (
            %(cycle_id)s, %(spec)s, %(spec_expected_added)s, %(spec_expected_removed)s,
            %(ship_status)s, %(semantic_pass)s, %(tests_pass)s,
            %(actual_lines_added)s, %(actual_lines_removed)s,
            %(drift_ratio)s, %(composite_score)s, %(git_sha)s, %(cert_id)s
        )
        ON CONFLICT (cycle_id) DO UPDATE SET
            ship_status     = EXCLUDED.ship_status,
            semantic_pass   = EXCLUDED.semantic_pass,
            tests_pass      = EXCLUDED.tests_pass,
            drift_ratio     = EXCLUDED.drift_ratio,
            composite_score = EXCLUDED.composite_score
    """
    with conn.cursor() as cur:
        cur.execute(sql, row)
    conn.commit()


def _insert_deadletter(row: dict, conn: Any) -> None:
    sql = """
        INSERT INTO engine_cycle_deadletter (cycle_id, reason, raw_error)
        VALUES (%(cycle_id)s, %(reason)s, %(raw_error)s)
    """
    with conn.cursor() as cur:
        cur.execute(sql, {
            "cycle_id": row.get("cycle_id"),
            "reason": row.get("reason", "db_emit_failed"),
            "raw_error": (row.get("raw_error") or "")[:4000],
        })
    conn.commit()


def _jsonl_append(row: dict, path: Path = _JSONL_FALLBACK) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")


def _warn(msg: str) -> None:
    sys.stderr.write(f"[engine.outcome_emit] {msg}\n")


def emit_outcome(row: dict, dsn: str | None = None) -> None:
    """Emit outcome row to PG · NEVER raises.

    Routing:
    - row.ship_status == 'deadletter' OR row.reason set → engine_cycle_deadletter
    - else → engine_cycle_outcomes
    - DB fail → jsonl fallback + best-effort deadletter row

    Schema bootstrap (CREATE IF NOT EXISTS) runs on first call per process.
    """
    real_dsn = _get_dsn(dsn)
    if not real_dsn:
        _warn("no DATABASE_URL set · jsonl fallback only")
        try:
            _jsonl_append(row)
        except Exception as e:
            _warn(f"jsonl fallback failed: {type(e).__name__}: {e}")
        return

    is_dl = row.get("ship_status") == "deadletter" or row.get("reason") is not None

    try:
        # Lazy import · no psycopg dep when emit never called.
        import psycopg  # type: ignore
        with psycopg.connect(real_dsn, connect_timeout=5) as conn:
            _bootstrap_schema(conn)
            if is_dl:
                _insert_deadletter(row, conn)
            else:
                _insert_outcome(row, conn)
        return
    except Exception as e:
        _primary_err = f"{type(e).__name__}: {str(e)[:200]}"
        _warn(f"DB emit failed ({type(e).__name__}): {str(e)[:200]}")

    # Fallback chain
    try:
        _jsonl_append(row)
    except Exception as e:
        _warn(f"jsonl fallback failed: {type(e).__name__}: {e}")

    # Best-effort deadletter row recording the db_emit_failed event
    if real_dsn and not is_dl:
        try:
            import psycopg  # type: ignore
            with psycopg.connect(real_dsn, connect_timeout=5) as conn:
                _bootstrap_schema(conn)
                _insert_deadletter({
                    "cycle_id": row.get("cycle_id"),
                    "reason": "db_emit_failed",
                    "raw_error": f"primary insert failed · row jsonl-archived · {_primary_err}",
                }, conn)
        except Exception:
            pass  # truly silent · already in jsonl
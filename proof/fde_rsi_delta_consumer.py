"""cnt_c3 · PoI consumer for soul's rsi_delta ΔReward feed (pre-built · wire on deploy).

soul's `GET /api/platform/fde/rsi_delta/{task_uid}?escapes_only=true` returns the
PoI-eligible rows (escapes_noise=True only · spec
`_outbound_from_soul_to_compass_20260609_PoI_feed_consumption_spec_c3.md`). Each
row → a PoI credit on the central ledger, honoring the spec's hard rules:

  · credit ∝ delta_reward (>0 · already past the escapes gate)
  · idempotent by delta_id (same delta never double-credits · DB-backed dedup)
  · attribution: credit accrues to producer_model + grounding_source.policy — the
    WINNING strategy, so external selection pressure points at "what produces"
    (not a flat per-task average).
  · escapes_noise=False NEVER credits (feed pre-filters; we self-filter defensively
    in case a caller ever reads the full / escapes_only=false feed).

Reuses proof.poi_credit_store.upsert_credit (central ledger · design §4.1). NO LLM.
The feed FETCH (`fetch_rsi_delta_feed`) is wire-time only — exercised after G-cloud
deploy, not in CI. The credit logic below is fully unit-tested against soul's exact
fixture schema so it is correct the moment the endpoint goes live.
"""
from __future__ import annotations

from .poi_credit_store import upsert_credit

# credit bucket for a producer×policy pair · `fde-rsi::<producer>::<policy>`.
# A distinct policy is a distinct bucket so the ledger surfaces which produce
# strategy actually earns external reward (correctness-first vs aggressive …).
KEY_PREFIX = "fde-rsi"


def rsi_delta_memory_key(row: dict) -> str:
    """Attribution key = producer_model + grounding_source.policy (the winning
    strategy). Stable + lowercased so the same strategy accrues into one bucket."""
    producer = str(row.get("producer_model") or "unknown").strip().lower()
    gs = row.get("grounding_source") or {}
    policy = str(gs.get("policy") or "unknown").strip().lower()
    return f"{KEY_PREFIX}::{producer}::{policy}"


def consume_rsi_delta(conn, row: dict, now_iso: str, *, placeholder: str = "%s",
                      is_processed=None, mark_processed=None) -> dict:
    """Turn ONE rsi_delta feed row into a PoI credit (or a no-op with a reason).

    Gates, in order: escapes_noise → dedup(delta_id) → delta_reward>0. Only a row
    passing all three upserts `delta_reward` onto `rsi_delta_memory_key(row)`.
    `is_processed(delta_id)->bool` / `mark_processed(delta_id)` inject the dedup
    store (DB-backed helpers below · or an in-memory set). placeholder='%s'
    psycopg2 / '?' sqlite.

    Returns {credited: bool, reason, delta?, memory_key?, delta_id}.
    """
    delta_id = str(row.get("delta_id") or "")
    # 1 · escapes gate (defensive · feed should already pre-filter)
    if row.get("escapes_noise") is not True:
        return {"credited": False, "reason": "not_escapes", "delta_id": delta_id}
    # 2 · idempotent dedup
    if is_processed is not None and delta_id and is_processed(delta_id):
        return {"credited": False, "reason": "duplicate", "delta_id": delta_id}
    # 3 · positive delta only (escapes feed should never carry ≤0, but guard)
    try:
        delta = float(row.get("delta_reward") or 0.0)
    except (TypeError, ValueError):
        delta = 0.0
    if delta <= 0.0:
        return {"credited": False, "reason": "non_positive", "delta_id": delta_id}
    key = rsi_delta_memory_key(row)
    upsert_credit(conn, key, round(delta, 4), now_iso, placeholder)
    if mark_processed is not None and delta_id:
        mark_processed(delta_id)
    return {"credited": True, "reason": "ok", "delta": round(delta, 4),
            "memory_key": key, "delta_id": delta_id}


def consume_rsi_delta_feed(conn, rows, now_iso: str, *, placeholder: str = "%s",
                           is_processed=None, mark_processed=None) -> dict:
    """Consume a list of feed rows. Returns {results, credited_count, total_delta}."""
    results = [consume_rsi_delta(conn, r, now_iso, placeholder=placeholder,
                                 is_processed=is_processed, mark_processed=mark_processed)
               for r in rows]
    credited = [r for r in results if r["credited"]]
    return {"results": results, "credited_count": len(credited),
            "total_delta": round(sum(r["delta"] for r in credited), 4)}


# ── DB-backed idempotency ledger (delta_id seen-set · survives restarts) ─────
PROCESSED_DDL = ("CREATE TABLE IF NOT EXISTS rsi_delta_credited "
                 "(delta_id TEXT PRIMARY KEY, credited_at TEXT)")


def ensure_processed_table(conn) -> None:
    cur = conn.cursor()
    cur.execute(PROCESSED_DDL)
    conn.commit()


def db_is_processed(conn, delta_id: str, placeholder: str = "%s") -> bool:
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM rsi_delta_credited WHERE delta_id={placeholder}", (delta_id,))
    return cur.fetchone() is not None


def db_mark_processed(conn, delta_id: str, now_iso: str, placeholder: str = "%s") -> None:
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO rsi_delta_credited (delta_id, credited_at) VALUES ({placeholder},{placeholder}) "
        "ON CONFLICT (delta_id) DO NOTHING", (delta_id, now_iso))
    conn.commit()


# ── feed fetch · WIRE-TIME ONLY (after G-cloud deploy · not exercised in CI) ─
def fetch_rsi_delta_feed(base_url: str, task_uid: str, timeout: int = 10) -> list:
    """GET the escapes_only PoI-eligible feed for task_uid. Returns the data rows.

    Wire this to the live endpoint ONLY after platform deploys
    `/api/platform/fde/rsi_delta` (currently G-cloud gated). The credit logic above
    is endpoint-independent and already verified, so the moment the endpoint is up
    this is the only line that goes live."""
    import json
    import urllib.request
    url = (f"{base_url.rstrip('/')}/api/platform/fde/rsi_delta/{task_uid}"
           "?escapes_only=true")
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        env = json.loads(resp.read().decode("utf-8"))
    return env.get("data") or []

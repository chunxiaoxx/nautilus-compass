"""compass read path over the platform verdict-bus (`fde_verdicts`).

Platform owns the bus + schema (locked 2026-06-05 ·
docs/FDE_VERDICT_BUS_CONTRACT.md); compass owns the PoI mapping. This reader
SELECTs verdict rows read-only and credits TASK-LEVEL PoI
(fde-capsule-<task_uid>) into the central poi_credit table via the existing
checklist-verdict adapter — the external buyer-acceptance fitness signal that
escapes the self-referential internal economy (anchor #3).

Buildable + testable NOW against the locked schema (sqlite mock); the LIVE cloud
read is gated on G-cloud (GRANT SELECT ON fde_verdicts TO compass_sub). Until
then this replays the contract's two real verdicts (data_001 11/11, data_002
10/12) from any conforming connection. NO LLM.

Dimension-level PoI (proof.fde_batch_ingest) needs the checklist content, which
the bus row does NOT carry (only checklist_uid) — that path stays fed by the
local checklist+verdict pair. This reader is the task-level spine.
"""
from __future__ import annotations

import json

from .fde_poi_adapter import credit_from_checklist_verdict

# contract columns compass depends on (drift-guarded platform-side by
# tests/test_fde_verdict_contract.py)
_SELECT = ("SELECT verdict_id, task_uid, overall_pass, veto_failed, score, "
           "items, created_at FROM fde_verdicts")


def _coerce_items(raw):
    """Bus `items` is JSONB (psycopg2 → list) in prod, json TEXT in the sqlite
    mock. Accept both; never raise on a malformed cell (items is not needed for
    the task-level delta, only carried through)."""
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []


def from_fde_verdicts(bus_conn, credit_conn, since=None, placeholder="%s",
                      reject_delta=None):
    """Read `fde_verdicts` rows (created_at > since, ascending) and credit
    task-level PoI for each into credit_conn's poi_credit table.

    `since` is an exclusive created_at watermark (ISO8601) so already-settled
    verdicts are not double-credited; pass the previous call's `last_created_at`.
    `bus_conn` / `credit_conn` may be the same connection (one DB) or distinct.
    placeholder='%s' psycopg2 / '?' sqlite.

    Returns {processed, credited:[{task_uid, verdict_id, delta, action_outcome}],
    last_created_at}."""
    sql = _SELECT
    params: tuple = ()
    if since is not None:
        sql += f" WHERE created_at > {placeholder}"
        params = (since,)
    sql += " ORDER BY created_at ASC"

    cur = bus_conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    credited = []
    last_created_at = since
    for verdict_id, task_uid, overall_pass, veto_failed, score, items, created_at in rows:
        verdict = {
            "overall_pass": bool(overall_pass),
            "veto_failed": bool(veto_failed),
            "score": float(score),
            "items": _coerce_items(items),
        }
        kwargs = {} if reject_delta is None else {"reject_delta": reject_delta}
        res = credit_from_checklist_verdict(
            credit_conn, verdict, task_uid, created_at, placeholder, **kwargs)
        credited.append({"task_uid": task_uid, "verdict_id": verdict_id,
                         "delta": res["delta"], "action_outcome": res["action_outcome"]})
        last_created_at = created_at

    return {"processed": len(rows), "credited": credited,
            "last_created_at": last_created_at}

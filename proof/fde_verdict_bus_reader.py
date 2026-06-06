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
import os
import sys

from .fde_poi_adapter import (
    DEFAULT_DIM_PROJECT, credit_dimensions_from_verdict,
    credit_from_checklist_verdict)

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


def peek_fde_verdicts(bus_conn, since=None, placeholder="%s"):
    """Read-only dry-run · list the verdicts that WOULD settle (created_at >
    since, ascending) WITHOUT crediting anything. Lets a caller verify the GRANT
    SELECT is live on a strictly read-only connection before any write.

    Returns [{verdict_id, task_uid, overall_pass, veto_failed, score,
    created_at}]."""
    sql = ("SELECT verdict_id, task_uid, overall_pass, veto_failed, score, "
           "created_at FROM fde_verdicts")
    params: tuple = ()
    if since is not None:
        sql += f" WHERE created_at > {placeholder}"
        params = (since,)
    sql += " ORDER BY created_at ASC"
    cur = bus_conn.cursor()
    cur.execute(sql, params)
    return [{"verdict_id": r[0], "task_uid": r[1], "overall_pass": bool(r[2]),
             "veto_failed": bool(r[3]), "score": float(r[4]), "created_at": r[5]}
            for r in cur.fetchall()]


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


def _load_local_checklist(checklist_dir, task_uid):
    """Read `<checklist_dir>/<task_uid>_checklist.json` (UTF-8 · the files are
    CJK). Returns the checklist dict, or None when absent/unreadable so the caller
    can skip the dimension credit without stalling the verdict stream."""
    path = os.path.join(checklist_dir, f"{task_uid}_checklist.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        print(f"[bus] unreadable checklist {path}: {e}", file=sys.stderr)
        return None


def credit_dimensions_from_bus(bus_conn, credit_conn, checklist_dir, since=None,
                               placeholder="%s", dimension_for=None,
                               project=DEFAULT_DIM_PROJECT, pass_score=None):
    """Credit DIMENSION-level PoI from the verdict-bus (Option C · design §45).

    The bus row carries the verdict items but not the checklist content (only
    checklist_uid), so dimension granularity needs the checklist. This joins each
    bus verdict to its LOCAL `<task_uid>_checklist.json` by task_uid and runs the
    existing credit_dimensions_from_verdict (passed item → +score on its mapped
    dimension key; failed item → 0). A verdict whose local checklist is missing is
    skipped for dimension crediting (recorded · the task-level spine
    `from_fde_verdicts` still covers it) but the watermark still advances so a
    missing checklist never stalls the stream. `dimension_for` is injected (compass
    core stays decoupled from vtf); production wires map_to_rubric_dimension.

    `since` is an exclusive created_at watermark. Returns {processed,
    credited:[{task_uid, verdict_id, credited:{dim:delta}, events}],
    skipped_no_checklist:[task_uid...], last_created_at}."""
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
    skipped_no_checklist = []
    last_created_at = since
    for verdict_id, task_uid, overall_pass, veto_failed, score, items, created_at in rows:
        last_created_at = created_at
        checklist = _load_local_checklist(checklist_dir, task_uid)
        if checklist is None:
            skipped_no_checklist.append(task_uid)
            continue
        verdict = {
            "overall_pass": bool(overall_pass),
            "veto_failed": bool(veto_failed),
            "score": float(score),
            "items": _coerce_items(items),
        }
        summary = credit_dimensions_from_verdict(
            credit_conn, task_uid, checklist, verdict, created_at, placeholder,
            dimension_for=dimension_for, pass_score=pass_score, project=project)
        credited.append({"task_uid": task_uid, "verdict_id": verdict_id,
                         "credited": summary["credited"], "events": summary["events"]})

    return {"processed": len(rows), "credited": credited,
            "skipped_no_checklist": skipped_no_checklist,
            "last_created_at": last_created_at}

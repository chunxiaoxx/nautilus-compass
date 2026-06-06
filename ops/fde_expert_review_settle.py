"""compass · expert-review → PoI settle runner (north-star fuel intake).

The human expert review is the FIRST external, non-self-referential PoI signal
(anchor #3) — soul's M3 一审 scores v5's own output, so it is self-referential;
a real domain expert verdict is not. The expert verdict is the 复核状态/分项分
format (NOT the soul checklist format the fde_verdicts bus carries), so it does
NOT go through SETTLE_SOURCES / the bus reader — it flows through the DIRECT
credit_from_verdict adapter. This runner consumes filled expert review records
(the 飞书 Bitable rows · field contract: T3_feishu_retention_design §2) and
credits PoI on fde-capsule-<task_uid> — the SAME key the soul task-level + capsule
pipeline credit, so the expert signal COMPOUNDS on the task capsule.

Idempotent via a 复核时间 watermark (settle only reviews newer than the last).
NO LLM. Pure mapping + reuse of fde_poi_adapter.credit_from_verdict.

Source of `reviews`: a feishu Bitable export (G3 connected) or any list of
{task_uid, 复核状态, 分项分, 复核时间} dicts. Wire the feishu fetch in main()
when the real review table is populated.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from proof.fde_poi_adapter import (  # noqa: E402
    DEFAULT_REJECT_DELTA, credit_from_verdict, verdict_memory_key, verdict_to_outcome)

# 复核状态 values that are not yet a verdict (no credit · re-checked next run)
_PENDING = {"待复核", "pending", "复核中", ""}

# the 分项分 columns the expert fills in the 飞书 Bitable (packet form §3 · RUBRIC §10).
SCORE_FIELDS = ("引用准确性", "覆盖完整性", "防编造(幻觉)", "附件运用",
                "计算/定量", "产物格式可用", "行业体例", "时效性")


def bitable_record_to_review(record: dict, score_fields=SCORE_FIELDS) -> dict:
    """Map a feishu Bitable record ({record_id, fields:{列名:值}}) → review dict
    {task_uid, 复核状态, 分项分, 复核理由, 复核人, 复核时间}. 分项分 collects the
    numeric score columns present. No 复核状态 → '' → pending (skipped on settle)."""
    f = record.get("fields") or record
    scores = {k: f[k] for k in score_fields if isinstance(f.get(k), (int, float))}
    return {
        "task_uid": str(f.get("task_uid") or f.get("题目编号") or "").strip(),
        "复核状态": str(f.get("复核状态") or "").strip(),
        "分项分": scores,
        "复核理由": f.get("复核理由") or "",
        "复核人": f.get("复核人") or "",
        "复核时间": str(f.get("复核时间") or ""),
    }


def _review_time(r: dict) -> str:
    return str(r.get("复核时间") or r.get("review_at") or r.get("time") or "")


def _is_pending(r: dict) -> bool:
    status = str(r.get("复核状态") or r.get("status") or "").strip()
    if status in _PENDING:
        return True
    # neither pass nor reject label → treat as pending (unknown, don't credit)
    return verdict_to_outcome(r)["success"] is None


def settle_expert_reviews(conn, reviews, now_iso, placeholder="%s", since=None,
                          reject_delta=DEFAULT_REJECT_DELTA):
    """Credit PoI from filled expert review records.

    Each review = {task_uid, 复核状态(通过/打回/待复核), 分项分:{dim:score}, 复核时间}.
    Reviews are processed in 复核时间 order; only those with 复核时间 > `since` are
    considered (exclusive watermark · no double-credit · pass the previous
    last_review_at). 待复核/unknown → skipped (recorded). 通过 → +mean(分项分)/10;
    打回 → reject_delta. Credit lands on fde-capsule-<task_uid>. The review's
    复核时间 is the credit timestamp. placeholder='%s' psycopg2 / '?' sqlite.

    Returns {processed, settled:[{task_uid, delta, action_outcome}],
    skipped_pending:[task_uid...], last_review_at}."""
    ordered = sorted(reviews, key=_review_time)
    settled = []
    skipped_pending = []
    last_review_at = since
    processed = 0
    for r in ordered:
        rt = _review_time(r)
        if since is not None and rt <= since:
            continue  # already settled (at/under watermark)
        processed += 1
        last_review_at = rt or last_review_at
        uid = str(r.get("task_uid") or r.get("source_uid") or "").strip()
        if _is_pending(r):
            skipped_pending.append(uid)
            continue
        mk = verdict_memory_key(r)
        res = credit_from_verdict(conn, r, mk, rt or now_iso, placeholder,
                                  reject_delta=reject_delta)
        settled.append({"task_uid": uid, "delta": res["delta"],
                        "action_outcome": res["action_outcome"]})

    return {"processed": processed, "settled": settled,
            "skipped_pending": skipped_pending, "last_review_at": last_review_at}


# ─── main() · read reviews (feishu Bitable or local JSON) → settle ───────────

def _load_feishu_records(app_token, table_id):
    """Read all records from a feishu Bitable via the vtf feishu_client (G3
    connected). main()-only; resolves the client from $COMPASS_VTF_DIR or sibling."""
    import importlib.util
    candidates = []
    env = os.environ.get("COMPASS_VTF_DIR")
    if env:
        candidates.append(Path(env))
    candidates.append(_HERE.parent.parent / "vertical-task-factory" / "fde-toolbox")
    for c in candidates:
        fc = c / "feishu_client.py"
        if fc.exists():
            spec = importlib.util.spec_from_file_location("feishu_client", fc)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            token = mod.tenant_token()
            resp = mod.read_bitable_records(app_token, table_id, token)
            return (resp.get("data") or {}).get("items") or []
    raise SystemExit("[expert] feishu_client not found — set COMPASS_VTF_DIR")


def main(argv=None):
    import argparse
    import json
    import sqlite3
    ap = argparse.ArgumentParser(description="Settle expert reviews → PoI.")
    ap.add_argument("--input", help="local JSON file: list of bitable records or reviews")
    ap.add_argument("--feishu", action="store_true", help="read from a feishu Bitable")
    ap.add_argument("--app-token", help="feishu Bitable app_token (with --feishu)")
    ap.add_argument("--table-id", help="feishu Bitable table_id (with --feishu)")
    ap.add_argument("--credit-db", help="sqlite path for poi_credit (default: in-memory dry-run)")
    ap.add_argument("--since", help="exclusive 复核时间 watermark (skip already-settled)")
    args = ap.parse_args(argv)

    if args.feishu:
        records = _load_feishu_records(args.app_token, args.table_id)
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            records = json.load(f)
    else:
        raise SystemExit("[expert] give --input <json> or --feishu --app-token --table-id")

    reviews = [bitable_record_to_review(r) for r in records]
    now_iso = os.environ.get("COMPASS_EXPERT_NOW") or _utc_now()

    conn = sqlite3.connect(args.credit_db or ":memory:")
    conn.execute("CREATE TABLE IF NOT EXISTS poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    res = settle_expert_reviews(conn, reviews, now_iso, placeholder="?", since=args.since)
    conn.commit()
    print(f"[expert] processed={res['processed']} settled={len(res['settled'])} "
          f"pending={res['skipped_pending']} watermark→{res['last_review_at']}")
    for s in res["settled"]:
        print(f"  · {s['task_uid']}: {s['delta']:+.4f} ({s['action_outcome']})")
    return 0


def _utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())

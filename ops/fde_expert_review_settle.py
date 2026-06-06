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

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from proof.fde_poi_adapter import (  # noqa: E402
    DEFAULT_REJECT_DELTA, credit_from_verdict, verdict_memory_key, verdict_to_outcome)

# 复核状态 values that are not yet a verdict (no credit · re-checked next run)
_PENDING = {"待复核", "pending", "复核中", ""}


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

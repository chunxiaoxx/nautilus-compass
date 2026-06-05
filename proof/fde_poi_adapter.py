"""FDE expert-review verdict → PoI credit adapter (dual-flywheel bite · T3/T4).

The expert review verdict (通过/打回 + 分项分) is the EXTERNAL ground truth the
RSI flywheel has been starving for — not an internal self-score (the platform's
RSI self-eval went three-times-negative; only an outside signal closes the loop).
A passed review credits the FDE task-template / capsule memory_key, so
expert-approved task patterns accrue PoI and get boosted in future recall (the
compounding loop). A rejection applies a negative signal (aligned with the V5
ruling that executed_failed is a negative PoI input).

This is feed (a) of the expert-review回路; feed (b) is the capsule pipeline in
vertical-task-factory/fde-toolbox/feishu_retention_scaffold.py. Both consume the
same structured verdict.

NO LLM. Pure mapping + reuse of proof.poi_credit_store.upsert_credit and
proof.poi_reconciler.outcome_to_action_outcome. Mock verdicts until a real soul
checklist_scorer verdict stream / real feishu review batch lands (G-verdict /
G-batch).
"""
from __future__ import annotations

from .poi_credit_store import upsert_credit
from .poi_reconciler import outcome_to_action_outcome

# expert verdict labels (zh primary · en aliases) → pass / reject
PASS_LABELS = {"通过", "pass", "passed", "approve", "approved", "accept", "accepted"}
REJECT_LABELS = {"打回", "reject", "rejected", "fail", "failed", "退回"}

# a rejection is a negative external signal (V5 executed_failed-as-negative ruling)
DEFAULT_REJECT_DELTA = -0.5


def _status(verdict: dict) -> str:
    return str(verdict.get("复核状态") or verdict.get("status") or "").strip()


def verdict_to_outcome(verdict: dict) -> dict:
    """Map an FDE review verdict to an L4-style outcome {success: bool|None}."""
    raw = _status(verdict)
    low = raw.lower()
    if raw in PASS_LABELS or low in PASS_LABELS:
        return {"success": True}
    if raw in REJECT_LABELS or low in REJECT_LABELS:
        return {"success": False}
    return {"success": None}


def verdict_delta(verdict: dict, reject_delta: float = DEFAULT_REJECT_DELTA) -> float:
    """PoI delta from a verdict.

    · pass    → mean(分项分) / 10  (0..1 · the expert's dimension scores)
    · pass w/o scores → 1.0 (unit positive)
    · reject  → reject_delta (negative)
    · pending → 0.0 (no-op)
    """
    s = verdict_to_outcome(verdict)["success"]
    if s is None:
        return 0.0
    if s is False:
        return reject_delta
    scores = (verdict.get("分项分") or verdict.get("dimension_scores") or {})
    vals = [float(v) for v in scores.values() if isinstance(v, (int, float))]
    if not vals:
        return 1.0
    return round(sum(vals) / len(vals) / 10.0, 4)


def verdict_memory_key(verdict: dict) -> str:
    """Credit target key · matches feishu_retention_scaffold capsule naming
    (`fde-capsule-<task_uid lower>`) so the SAME memory that the capsule pipeline
    ingests is the one credited → approved task patterns get boosted in recall."""
    uid = str(verdict.get("task_uid") or verdict.get("source_uid") or "").strip().lower()
    return f"fde-capsule-{uid}"


def credit_from_verdict(conn, verdict: dict, memory_key: str, now_iso: str,
                        placeholder: str = "%s",
                        reject_delta: float = DEFAULT_REJECT_DELTA) -> dict:
    """Upsert a PoI credit for memory_key from an FDE verdict.

    Returns {action_outcome, delta, memory_key}. A pending / zero-delta verdict
    is a no-op (nothing written). placeholder='%s' for psycopg2, '?' for sqlite.
    """
    outcome = verdict_to_outcome(verdict)
    action = outcome_to_action_outcome(outcome)
    delta = verdict_delta(verdict, reject_delta)
    if delta != 0.0:
        upsert_credit(conn, memory_key, delta, now_iso, placeholder)
    return {"action_outcome": action, "delta": delta, "memory_key": memory_key}

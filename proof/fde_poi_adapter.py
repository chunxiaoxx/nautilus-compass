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
from .poi_memory_key import derive_memory_key
from .poi_reconciler import outcome_to_action_outcome

# project namespace the dimension atoms are ingested under
# (~/.claude/projects/fde-knowledge/memory/) — the central-ledger / boost key is
# project-qualified (<project>/<basename>), so a dimension credit MUST use this
# key or no boost lookup will ever hit it (dead credit). design §3 / boost chain.
DEFAULT_DIM_PROJECT = "fde-knowledge"

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


# ─── soul checklist_scorer real format ───────────────────────────────────────
# soul emits {score, passed, total, veto_failed, overall_pass, items:[...]}
# (the actual verdict stream / fde_verdicts table shape) — NOT the mock
# 复核状态/分项分. These consume that real format directly.

def checklist_verdict_to_outcome(verdict: dict) -> dict:
    """soul checklist verdict → {success: bool}. veto_failed forces failure."""
    if verdict.get("veto_failed"):
        return {"success": False}
    return {"success": bool(verdict.get("overall_pass"))}


def checklist_verdict_delta(verdict: dict, reject_delta: float = DEFAULT_REJECT_DELTA) -> float:
    """Pass → `score` (= passed/total · the checklist pass rate, GOAL's
    "checklist 通过率"). Fail / veto_failed → reject_delta (negative)."""
    if not checklist_verdict_to_outcome(verdict)["success"]:
        return reject_delta
    score = verdict.get("score")
    if score is None:
        total = verdict.get("total") or 0
        score = (verdict.get("passed", 0) / total) if total else 1.0
    return round(float(score), 4)


def credit_from_checklist_verdict(conn, verdict: dict, task_id: str, now_iso: str,
                                  placeholder: str = "%s",
                                  reject_delta: float = DEFAULT_REJECT_DELTA) -> dict:
    """Upsert a PoI credit from a soul checklist_scorer verdict for task_id.

    memory_key = fde-capsule-<task_id> (same as the capsule pipeline). Pending is
    not a checklist outcome (a scored verdict is always pass or fail), so this
    always writes. placeholder='%s' psycopg2 / '?' sqlite."""
    memory_key = verdict_memory_key({"task_uid": task_id})
    outcome = checklist_verdict_to_outcome(verdict)
    action = outcome_to_action_outcome(outcome)
    delta = checklist_verdict_delta(verdict, reject_delta)
    if delta != 0.0:
        upsert_credit(conn, memory_key, delta, now_iso, placeholder)
    return {"action_outcome": action, "delta": delta, "memory_key": memory_key}


# ─── dimension-level PoI credit · Layer2↔3 tie (T1) ──────────────────────────
# A passed checklist item credits its RUBRIC dimension key fde-dim-<dimension>;
# a failed item credits 0 (the avoid-pitfall capsule is retained by the vtf
# capsule pipeline, not here — "fail must not also add score", design §3/§64).
# The most-validated dimension thus accrues the most PoI and surfaces first in
# recall, closing the recursive flywheel at dimension granularity.

def _default_dimension(item: dict) -> str:
    """Fallback item→dimension when no mapper is injected. Keeps compass
    standalone WITHOUT duplicating the vtf keyword rules: a generic RUBRIC
    dimension already on the item is used verbatim; an unmapped / 'task-specific'
    item degrades to 'uncategorized'. Production injects
    fde_knowledge_capsule.map_to_rubric_dimension via `dimension_for`."""
    raw = str(item.get("dimension", "")).strip().lower()
    if not raw or raw == "task-specific":
        return "uncategorized"
    return raw.replace(" ", "-")


def dimension_filename(dimension: str) -> str:
    """The capsule pipeline's ingest_atoms file stem (`fde-dim-<dimension>.md`).
    This is the file the SAME accumulated dimension memory lives in."""
    return f"fde-dim-{str(dimension).strip().lower()}.md"


def dimension_memory_key(dimension: str, project: str = DEFAULT_DIM_PROJECT) -> str:
    """Central-ledger / boost key for a dimension atom = <project>/<filename>,
    exactly what memory_key_from_path / _v14_poi_boost derive for the ingested
    `fde-knowledge/memory/fde-dim-<dimension>.md` file. Crediting THIS key (not a
    bare `fde-dim-<dimension>`) is what makes the boost actually fire on the
    dimension atom — closing Layer2↔3 for real, not just in the table."""
    return derive_memory_key(project, dimension_filename(dimension))


def dimension_pass_score(verdict: dict) -> float:
    """Per-passed-item positive credit = the verdict's checklist score (pass
    rate, 0..1). Falls back to passed/total, then 1.0. Mirrors
    checklist_verdict_delta's positive branch so a dimension proven in a
    higher-quality submission earns proportionally more credit."""
    score = verdict.get("score")
    if score is None:
        total = verdict.get("total") or 0
        score = (verdict.get("passed", 0) / total) if total else 1.0
    return round(float(score), 4)


def credit_dimensions_from_verdict(conn, task_id: str, checklist: dict,
                                   verdict: dict, now_iso: str,
                                   placeholder: str = "%s",
                                   dimension_for=None,
                                   pass_score: "float | None" = None,
                                   project: str = DEFAULT_DIM_PROJECT) -> dict:
    """Upsert per-dimension PoI credits from a soul checklist_scorer verdict.

    For each SCORED verdict item joined to its checklist item by `id`:
      · passed → upsert_credit(<project>/fde-dim-<dimension>.md, +pass_score)
      · failed → 0 (no write · only the avoid-pitfall capsule is retained)
    `dimension_for(item)->str` maps a checklist item to its RUBRIC dimension
    (injected; defaults to `_default_dimension`). `pass_score` overrides the
    per-passed-item credit (defaults to the verdict score). `project` is the
    namespace the dimension atoms are ingested under, so the credited key matches
    the boost key. placeholder='%s' psycopg2 / '?' sqlite.

    Returns {credited:{dim:delta}, events:{dim:count}, skipped_fail:[ids],
    skipped_unmatched:[ids], memory_keys:{dim:key}, pass_score}."""
    dim_of = dimension_for or _default_dimension
    delta = dimension_pass_score(verdict) if pass_score is None else round(float(pass_score), 4)
    cl_by_id = {it.get("id"): it for it in (checklist.get("items") or [])}

    credited: dict = {}
    events: dict = {}
    memory_keys: dict = {}
    skipped_fail: list = []
    skipped_unmatched: list = []

    for v in (verdict.get("items") or []):
        vid = v.get("id")
        item = cl_by_id.get(vid)
        if item is None:
            skipped_unmatched.append(vid)
            continue
        if not bool(v.get("pass")):
            skipped_fail.append(vid)  # fail → 0 credit (keep only the capsule)
            continue
        dim = dim_of(item)
        key = dimension_memory_key(dim, project)
        if delta != 0.0:
            upsert_credit(conn, key, delta, now_iso, placeholder)
        credited[dim] = round(credited.get(dim, 0.0) + delta, 4)
        events[dim] = events.get(dim, 0) + 1
        memory_keys[dim] = key

    return {"credited": credited, "events": events, "skipped_fail": skipped_fail,
            "skipped_unmatched": skipped_unmatched, "memory_keys": memory_keys,
            "pass_score": delta}

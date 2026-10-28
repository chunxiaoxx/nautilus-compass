"""W-D soul scoring poller · produced → RUBRIC score → verdict-bus (platform-soul turf).

The FDE flywheel's last hop. Polls produced FDE tasks, scores each output with the
soul RUBRIC checklist_scorer, and writes the verdict to the existing verdict-bus
(POST /api/platform/fde/verdict) — which flips the task to 'settled' in the /tasks view.

The verdict source is `'soul'` (in the compass PoI allowlist), the EXTERNAL buyer-
acceptance fitness signal (anchor #3 — not internal NAU). V5's feishu scorer-front
writes human verdicts in parallel with `source='feishu-expert'`; distinct source +
distinct verdict_id means no double-write conflict (V5 6/7 design ruling).

Effect-injected like services/fde_poller.py: the produced-task read, the RUBRIC
scorer (checklist_from_task + harness/checklist_scorer + LLM judge), and the verdict
POST are all injected, so the orchestration core is pure + unit-tested without
HTTP/LLM. fail-soft: one task's failure never aborts the batch.
"""
from __future__ import annotations

import json
from typing import Callable, Iterable, Protocol

# 第3类确定性 verifier 题的 kind 标记 = compass/bench_eval 或 swebench harness 的 turf
# (非 soul checklist)。swe-rsi-fuel = SWE patch·正确性只能 swebench 跑·soul checklist 判=facade
# (6/20 requests-2148 facade bug 根因)。
_DETERMINISTIC_KINDS = frozenset({"code-fix-with-deterministic-verifier", "swe-rsi-fuel"})


# 6/21 autolab bogus-pass 回归门:producer 没拿到题 → 产出占位/求输入闲聊
# ({"code":"v5-daemon-fde-produce","text":"…现在需要您提供具体的题目…"})。output 非空 →
# 绕过下方空守卫 → LLM judge 太宽松给闲聊打 pass(实证 soul bvh_cuda 0.833)。
# 实质性守卫 = 占位/求输入产出 → 非交付物 → 不送判不写 verdict(避免盖章垃圾·反 facade)。
# 只匹配具体占位短语(不设长度门)以免误杀正常短交付。
_PLACEHOLDER_MARKERS = (
    "需要您提供", "请提供具体", "请您提供", "等待您提供", "提供具体的题目",
    "提供具体的任务", "我才能开始作答", "请提供题目", "无法开始作答",
    "尚未收到", "未收到题目", "未提供题目", "请提供任务内容",
    "please provide the", "waiting for the task", "i need the actual",
    "provide the specific task", "no task was provided",
)


def is_substantive_output(task: dict) -> bool:
    """产出是否含真交付物(非占位/求输入闲聊)。

    防 6/21 autolab bogus-pass:producer 没拿到题时产出"现在需要您提供具体的题目"占位 ·
    output 非空(绕过空守卫)· LLM judge 太宽松会给闲聊打 pass。占位类 → 非实质 → 不送判。
    仅匹配具体占位短语(无长度门)以免误杀正常短交付。
    """
    out = task.get("output")
    if isinstance(out, dict):
        text = (out.get("text") or out.get("answer") or "")
    elif isinstance(out, str):
        text = out
    else:
        return False
    text = text.strip()
    if not text:
        return False
    low = text.lower()
    return not any(m.lower() in low for m in _PLACEHOLDER_MARKERS)


def is_deterministic_kind(task: dict) -> bool:
    """题是否为「带确定性 verifier」类(soul 不该 LLM-checklist 双判·让 bench_eval 权威)。

    解析 task['description'](FDE desc = JSON 串·含 ``kind``)。非 JSON / 无 kind →
    False(默认非确定性·继续走 soul 判·不误跳)。
    """
    desc = task.get("description")
    if not isinstance(desc, str):
        return False
    try:
        obj = json.loads(desc)
    except (ValueError, TypeError):
        return False
    if not isinstance(obj, dict):
        return False
    # 防御:SWE 题(有 swe_instance_id)即便 kind 缺失也视确定性(swebench harness 权威)。
    if obj.get("swe_instance_id"):
        return True
    return obj.get("kind") in _DETERMINISTIC_KINDS


class ProducedTaskSource(Protocol):
    """Read produced FDE tasks (the platform-binding seam).

    Each task is a dict with at least ``task_uid`` and (when scorable) ``output``
    (the produced deliverable persisted by POST /report).
    """

    def list_produced_tasks(self) -> Iterable[dict]:  # pragma: no cover - protocol
        ...


def build_verdict_body(task: dict, scored: dict) -> dict:
    """Map a scored RUBRIC result → POST /verdict body (matches ingest _REQUIRED).

    ``scored`` is checklist_scorer.score_checklist output augmented with
    ``checklist_uid``. verdict_id is deterministic (``soul|{task_uid}|{checklist_uid}``)
    so re-scoring the same task+checklist is idempotent at ingest. source='soul'.
    """
    task_uid = task["task_uid"]
    checklist_uid = scored.get("checklist_uid") or "default"
    return {
        "verdict_id": f"soul|{task_uid}|{checklist_uid}",
        "task_uid": task_uid,
        "source": "soul",
        "checklist_uid": checklist_uid,
        "overall_pass": bool(scored.get("overall_pass")),
        "veto_failed": bool(scored.get("veto_failed")),
        "score": float(scored.get("score", 0.0)),
        "items": scored.get("items") or [],
    }


def poll_and_score(
    source: ProducedTaskSource,
    score_fn: Callable[[dict], dict],
    verdict_fn: Callable[[dict], object],
    already_scored: Iterable[str] | None = None,
    should_score: Callable[[dict], bool] | None = None,
) -> dict:
    """Read produced tasks → score output → POST verdict. fail-soft per task.

    Args:
        source: produced-task read seam (``list_produced_tasks()``).
        score_fn: ``task -> scored`` (RUBRIC checklist_scorer + LLM judge, injected).
        verdict_fn: post one verdict body (POST /api/platform/fde/verdict wrapper).
        already_scored: task_uids already settled by soul (cross-poll idempotency).

    Returns:
        ``{"scored": [uid…], "skipped": [uid…], "failed": [uid…]}``.
    """
    seen = set(already_scored or ())
    scored_uids: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for task in source.list_produced_tasks():
        uid = task.get("task_uid")
        if not uid or uid in seen:
            skipped.append(uid)
            continue
        if task.get("output") in (None, "", {}, []):
            # produced but nothing to score → skip (don't emit an empty verdict).
            skipped.append(uid)
            seen.add(uid)
            continue
        if not is_substantive_output(task):
            # 非实质产出(producer 没拿到题的占位/求输入闲聊)→ 不送判·不写 verdict。
            # 防 LLM judge 给闲聊盖 pass 章(6/21 autolab bogus-pass·反 facade)。
            skipped.append(uid)
            seen.add(uid)
            continue
        if should_score is not None and not should_score(task):
            # 该题不归 soul 判(如 deterministic-kind = bench_eval turf)→ 跳过不发 verdict。
            skipped.append(uid)
            seen.add(uid)
            continue
        try:
            scored = score_fn(task)
            verdict_fn(build_verdict_body(task, scored))
        except Exception:  # fail-soft: one task's scorer/post failure never aborts batch
            failed.append(uid)
            seen.add(uid)
            continue
        scored_uids.append(uid)
        seen.add(uid)

    return {"scored": scored_uids, "skipped": skipped, "failed": failed}

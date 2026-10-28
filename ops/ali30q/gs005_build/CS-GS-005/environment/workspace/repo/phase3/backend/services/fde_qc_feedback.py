"""S2 亲笔提交→QC 反馈环 · 纯核心.

turf:平台 own 提交轮询+反馈写回;QC 判分=soul lane 现成件(线1 checklist_scorer·
线2 assemble_tutorial.validate·均 effect 注入);引擎=现成 report/verdict API(零改动)。
🔴 人是作者:本模块只判+给 reason,绝不生成/改写稿件正文。
🔴 顺序契约:verdict 先于 report POST(verdict-join 遮蔽反用·防 soul-scorer 双判)。
"""
from __future__ import annotations

import hashlib
import re
from typing import Callable

from services.fde_task_form_schema import claim_agent_id, normalize_task_line


def line_code(raw) -> str:
    """与历史入口兼容: 统一由 schema 层做业务线归一化。"""
    return normalize_task_line(raw)

_SEC = {
    "instruction": r"一[、.]\s*Instruction",
    "knowledge_points": r"二[、.]\s*Knowledge\s*Points",
    "background_knowledge": r"三[、.]\s*Background\s*Knowledge",
    "task_example": r"四[、.]\s*Task\s*示例",
}
# 节边界=四个已知节标题之一(不能用裸「一|二|三|四、」——正文中文枚举行会假截断·review 实证)
_NEXT_SEC = "|".join(_SEC.values())
_TE_LABELS = r"输入|执行|步骤|结果/?答案|答案|结果"


def _emit_attention(attention_fn, **payload: object) -> None:
    if attention_fn is None:
        return
    try:
        attention_fn(payload)
    except Exception:
        pass


def _section(text: str, pat: str) -> str:
    """取「节标题行之后到下一节标题/文末」的正文。"""
    m = re.search(r"^[#\s]*(?:" + pat + r")\s*$(.*?)(?=^[#\s]*(?:" + _NEXT_SEC + r")\s*$|\Z)",
                  text, re.M | re.S | re.I)
    return m.group(1).strip() if m else ""


def parse_tutorial_md(text: str) -> dict:
    """飞书「提交内容」md/草稿 → 买方教案 material dict(缺段=空值·交 validate 报)。"""
    text = text or ""
    # (?!#) 防 ## 节标题被吃成标题(review 实证)
    m = re.search(r"^#(?!#)\s*(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()
    else:
        m = re.search(r"^(?:任务)?标题[::]\s*(.+)$", text, re.M)
        title = m.group(1).strip() if m else ""
    l1 = l2 = ""
    m = re.search(r"^\**领域(?:tag)?\**[::]\**\s*([^/\n]+?)\s*/\s*(.+?)\**\s*$", text, re.M)
    if m:
        l1, l2 = m.group(1).strip(), m.group(2).strip()
    kp_raw = _section(text, _SEC["knowledge_points"])
    kps = [ln.lstrip("-•* ").strip() for ln in kp_raw.splitlines()
           if ln.strip().lstrip("-•* ").strip()]
    te_raw = _section(text, _SEC["task_example"])

    def _te(label_pat: str) -> str:
        # 标签行锚定(^·re.M):正文行中的「执行:」不得劫持字段(review 实证)
        m2 = re.search(r"^\s*\**(?:" + label_pat + r")\**[::]\**\s*(.*?)"
                       r"(?=^\s*\**(?:" + _TE_LABELS + r")\**[::]|\Z)",
                       te_raw, re.M | re.S)
        return m2.group(1).strip() if m2 else ""

    return {
        "title": title,
        "l1": l1, "l2": l2,
        "instruction": _section(text, _SEC["instruction"]),
        "knowledge_points": kps,
        "background_knowledge": _section(text, _SEC["background_knowledge"]),
        "task_example": {"input": _te("输入"), "steps": _te("执行|步骤"),
                         "answer": _te(r"结果/?答案|答案|结果")},
    }


# 线2 教案 QC 维度(validate() violations 正则 → 维度归属·与 assemble_tutorial.py 文案锚定)
# complete 必须 ^缺 锚定:'Task示例缺 输入' 含子串「缺 」,裸子串会连坐 complete(review 实证)
_L2_DIMS = (
    ("complete", "五部分齐全(标题/领域/Instruction/KP/Background)", (r"^缺 ",)),
    ("domain", "领域一级 ∈ {金融,法律,医疗,工程,农业,其他}", (r"领域一级非法",)),
    ("bk_chars", "Background Knowledge 字数 ∈ [1000,30000]", (r"字数",)),
    ("task_example", "Task示例含 输入+执行+结果/答案", (r"^Task示例缺",)),
)


def line2_score(report: dict) -> dict:
    """assemble_tutorial.validate() 报告 → checklist_scorer 同形 scored dict。

    买方红线维度(完整性/字数/领域/示例)任一违反 = veto(打回);
    density advisory 只预警不否决(终判=买方 AI 检测·专家自检)。
    """
    violations = report.get("violations") or []
    items = []
    for dim_id, text, needles in _L2_DIMS:
        hits = [v for v in violations if any(re.search(n, v) for n in needles)]
        items.append({"id": dim_id, "text": text, "veto": True,
                      "pass": not hits, "reason": "; ".join(hits) if hits else "ok"})
    advisory = (report.get("density_advisory") or "").strip()
    items.append({"id": "density", "text": "知识密度/反AI自检(advisory)", "veto": False,
                  "pass": True,
                  "reason": advisory if advisory else
                  f"ok(数值数={report.get('bk_digits', 0)}·终判=买方AI检测·请专家自检)"})
    passed = sum(1 for i in items if i["pass"])
    compliant = bool(report.get("compliant"))
    return {"score": passed / len(items), "passed": passed, "total": len(items),
            "veto_failed": not compliant, "overall_pass": compliant,
            "items": items, "checklist_uid": "tutorial_v1"}


def _sub_hash(submission: str) -> str:
    return hashlib.sha1((submission or "").strip().encode("utf-8")).hexdigest()[:10]


def build_qc_verdict_body(task_uid: str, scored: dict, submission: str) -> dict:
    """scored → POST /verdict body。verdict_id 含稿 hash:同稿幂等·改稿新 verdict。

    (镜像 services.fde_scorer_poll.build_verdict_body·区别=按提交版本留痕)
    """
    return {
        "verdict_id": f"soul|qc|{task_uid}|{_sub_hash(submission)}",
        "task_uid": task_uid,
        "source": "soul",
        "checklist_uid": scored.get("checklist_uid") or "default",
        "overall_pass": bool(scored.get("overall_pass")),
        "veto_failed": bool(scored.get("veto_failed")),
        "score": float(scored.get("score", 0.0)),
        "items": scored.get("items") or [],
    }


def format_feedback(body: dict) -> str:
    """verdict body → 飞书「QC反馈」逐项文本(专家可读·指出哪不达标·不代写)。"""
    items = body.get("items") or []
    passed = sum(1 for i in items if i.get("pass"))
    head = ("✅ 已通过" if body.get("overall_pass") else "❌ 已打回") + \
        f" · {passed}/{len(items)} 项过 · QC批次 {body['verdict_id'].rsplit('|', 1)[-1]}"
    lines = [head]
    for i in items:
        mark = "✓" if i.get("pass") else "✗"
        veto = "(红线)" if i.get("veto") and not i.get("pass") else ""
        lines.append(f"{mark} {i.get('id')}{veto}: {str(i.get('reason') or '')[:160]}")
    if not body.get("overall_pass"):
        lines.append("→ 请按 ✗ 项修改后将状态改回「已提交」(正文须专家亲笔·QC不代写)")
    return "\n".join(lines)[:1900]


def sync_submissions(
    source,
    qc_fn: Callable[[dict, str], dict],
    verdict_fn: Callable[[dict], object],
    report_fn: Callable[[str, str, str], object],
    attention_fn: Callable[[dict], None] | None = None,
) -> dict:
    """读「已提交」行 → QC → verdict → report → 反馈汇总。fail-soft 单行不拖批。

    顺序契约(🔴):verdict_fn 必须先于 report_fn —— verdict-join 遮蔽反用,
    使 soul-scorer 的 produced+无verdict 过滤器跳过 human 稿(防 T1 checklist 双判)。
    Returns {"results": [{task_uid, passed, feedback}], "skipped": [...], "failed": [...]}
    """
    results, skipped, failed = [], [], []
    for row in source.read_submission_rows():
        uid = str(row.get("task_uid") or "").strip() or None
        sub = str(row.get("submission") or "").strip()
        if not uid or not sub:
            if uid:
                _emit_attention(
                    attention_fn,
                    stage="s2",
                    code="s2_empty_submission",
                    task_uid=uid,
                    severity="warning",
                    title="S2 提交内容为空",
                    detail="已提交行缺少正文，需返回飞书提醒专家补填提交内容后重走提交",
                    context={"row": {"task_uid": uid, "line": row.get("line", ""),
                                     "title": row.get("title", "")}},
                )
            skipped.append(uid)
            continue
        try:
            scored = qc_fn(row, sub)
            body = build_qc_verdict_body(uid, scored, sub)
            verdict_fn(body)
            expert = claim_agent_id(row)
            if expert:
                report_fn(uid, expert, sub)
        except Exception:  # noqa: BLE001 – fail-soft·runner 日志暴露
            _emit_attention(
                attention_fn,
                stage="s2",
                code="s2_qc_or_report_fail",
                task_uid=uid,
                severity="error",
                title="S2 QC/提交链路失败",
                detail="QC 判断、verdict 写入或 report 回写任意一环失败，请重跑本行",
                context={"task_uid": uid},
            )
            failed.append(uid)
            continue
        results.append({"task_uid": uid, "passed": bool(body["overall_pass"]),
                        "feedback": format_feedback(body)})
    return {"results": results, "skipped": skipped, "failed": failed}

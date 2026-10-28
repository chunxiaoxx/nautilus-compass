"""S3 交付+财务最小记账 · 纯核心.

turf:平台 own 交付组装+结算记账;飞书读写=effect runner;
QC 判分=S2 已落 verdict-bus(本模块只读 verdict 门控,零改动)。
🔴 人是作者:本模块只组装专家原稿+记账,绝不生成/改写正文。
🔴 门:仅 verdict.overall_pass=True 的稿可交付。
🔴 交付样本标 provisional:正文须专家过买方 AI 检测后才是终品(charter §2)。
🔴 买方机密走独立 base 物理隔离(charter §E·runner 侧落地)。

design: docs/plans/2026-06-11-fde-org-production-engine-design.md §S3。
复用:services.fde_qc_feedback.parse_tutorial_md(线2 结构抽取·零重复)。
"""
from __future__ import annotations

from typing import Callable

from services.fde_task_form_schema import display_expert
from services.fde_expert_rates import price_settlement
from services.fde_qc_feedback import parse_tutorial_md

# 透明定价表(USD / 1k tokens·公开报价口径·estimate 用·非账单真值)。
# 教案/线2 QC 离线 validate 无 LLM 花费 → token_cost=0。
# 线1/线3 LLM judge/solver 花费按本表估;真账单以网关账单为准(此处仅最小记账)。
_PRICE_USD_PER_1K = {
    "doubao-seed-2.0-pro": {"in": 0.0004, "out": 0.0012},
    "default": {"in": 0.0005, "out": 0.0015},
}

_PHASE3_INTERACTIVE_WORKFLOW = "phase3_interactive_v1"


def _emit_attention(attention_fn, **payload: object) -> None:
    if attention_fn is None:
        return
    try:
        attention_fn(payload)
    except Exception:
        pass


def is_deliverable(row: dict, verdict: dict | None) -> bool:
    """交付门:有非空稿 + verdict.overall_pass=True 才可交付。"""
    if str(row.get("workflow_version") or "").strip() == _PHASE3_INTERACTIVE_WORKFLOW:
        return False
    if not str(row.get("submission") or "").strip():
        return False
    if not verdict or not verdict.get("overall_pass"):
        return False
    return True


def assemble_buyer_payload(row: dict) -> dict:
    """QC 过稿 → 买方交付 payload。

    line2(教案):parse_tutorial_md 抽 4 段结构列 + 交付正文=专家原稿。
    line1(题目):最小路径=原稿+元数据透传(16列 fde-row-assembler 为后续片)。
    🔴 交付正文永远=专家原稿(delivery_body_md),不二次生成。
    """
    line = str(row.get("line") or "").strip()
    sub = str(row.get("submission") or "")
    base = {
        "task_uid": str(row.get("task_uid") or "").strip(),
        "line": line,
        "level": str(row.get("level") or "").strip(),
        "category": str(row.get("category") or "").strip(),
        "domain": str(row.get("domain") or "").strip(),
        "expert": display_expert(row),
        "delivery_body_md": sub,            # 专家原稿=交付正文
        "status": "provisional",            # 待专家过买方 AI 检测
    }
    if line == "2":
        m = parse_tutorial_md(sub)
        base.update({
            "title": m.get("title") or str(row.get("title") or "").strip(),
            "l1": m.get("l1", ""),
            "l2": m.get("l2", ""),
            "instruction": m.get("instruction", ""),
            "knowledge_points": "\n".join(m.get("knowledge_points") or []),
            "background_knowledge": m.get("background_knowledge", ""),
            "task_example": _fmt_task_example(m.get("task_example") or {}),
        })
    else:
        # line1/line3:元数据透传·正文原样进交付表(结构化 16 列 = 后续片)
        base["title"] = str(row.get("title") or "").strip()
        base["acceptance"] = str(row.get("acceptance") or "").strip()
    return base


def _fmt_task_example(te: dict) -> str:
    return (f"输入:{te.get('input', '')}\n"
            f"执行:{te.get('steps', '')}\n"
            f"结果/答案:{te.get('answer', '')}").strip()


def estimate_token_cost(line: str, model_calls: list | None = None) -> dict:
    """最小 token 成本记账(透明估算·非账单真值)。

    教案/线2 QC = 离线 validate 无 LLM → 0。
    线1/线3 = 按 model_calls 估(input/output tokens × 公开报价表)。
    """
    if not model_calls:
        return {"model": "none", "input_tokens": 0, "output_tokens": 0,
                "token_cost_usd": 0.0}
    in_tok = sum(int(c.get("input_tokens") or 0) for c in model_calls)
    out_tok = sum(int(c.get("output_tokens") or 0) for c in model_calls)
    models = sorted({str(c.get("model") or "default") for c in model_calls})
    cost = 0.0
    for c in model_calls:
        p = _PRICE_USD_PER_1K.get(str(c.get("model")), _PRICE_USD_PER_1K["default"])
        cost += (int(c.get("input_tokens") or 0) / 1000.0) * p["in"]
        cost += (int(c.get("output_tokens") or 0) / 1000.0) * p["out"]
    return {"model": "+".join(models), "input_tokens": in_tok,
            "output_tokens": out_tok, "token_cost_usd": round(cost, 6)}


def build_settlement_record(row: dict, verdict: dict, token_cost: dict,
                            rates: dict | None = None) -> dict:
    """交付 → settlement 最小记录(任务/专家/应付/token/状态)。

    🔴 应付真算(charter §2):rates(专家名册单价)+ row['hours'](工时)齐全
       → payable=单价×工时·status='computed';缺名册/缺工时 → None·pending(不臆造)。
       rates=None(无名册)→ 维持旧行为 None·pending。
    🔴 token_cost=真实估算(教案=0·线1/3=网关用量)。
    """
    record = {
        "task_uid": str(row.get("task_uid") or "").strip(),
        "expert": display_expert(row),
        "line": str(row.get("line") or "").strip(),
        "level": str(row.get("level") or "").strip(),
        "title": str(row.get("title") or "").strip(),
        "verdict_score": float(verdict.get("score") or 0.0),
        "verdict_id": str(verdict.get("verdict_id") or ""),
        "token_cost_usd": float(token_cost.get("token_cost_usd") or 0.0),
        "token_model": str(token_cost.get("model") or "none"),
        "payable_amount": None,          # 待人定价(rates 缺省)
        "payable_status": "pending",     # 应付真专家·未结算
        "status": "delivered_provisional",
    }
    if rates is None:
        return record
    # price_settlement 读 record['expert'] 对名册·row['hours'] 算应付(immutable)
    return price_settlement(record, rates, hours=row.get("hours"))


def sync_deliveries(
    source,
    verdict_fn: Callable[[str], dict | None],
    attention_fn: Callable[[dict], None] | None = None,
) -> dict:
    """读「已通过」行 → 门控 → 组装+记账 → 写交付表+settlement → 标已交付。

    幂等:already_delivered() 里的 task_uid 跳过。fail-soft 单行不拖批。
    🔴 写序:先 write_delivery 再 write_settlement 再 mark_delivered ——
       崩在中途时下一轮重扫该行(状态仍=已通过)幂等重放,不漏账不重账。
    Returns {"delivered": [...], "skipped": [...], "failed": [...]}
    """
    done = set(source.already_delivered())
    # 专家名册单价(RGDK v06_行业专家)·source 无此能力则空名册=应付维持 pending
    read_rates = getattr(source, "read_expert_rates", None)
    rates = read_rates() if callable(read_rates) else None
    delivered, skipped, failed = [], [], []
    for row in source.read_passed_rows():
        uid = str(row.get("task_uid") or "").strip()
        if not uid:
            _emit_attention(
                attention_fn,
                stage="s3",
                code="s3_invalid_row",
                task_uid=uid,
                severity="warning",
                title="S3 缺失 task_uid",
                detail="read_passed_rows 返回了空 task_uid，无法交付",
                context={"row": row},
            )
            skipped.append(uid or None)
            continue
        if not uid or uid in done:
            skipped.append(uid or None)
            continue
        try:
            verdict = verdict_fn(uid)
            if not is_deliverable(row, verdict):
                if verdict is None:
                    _emit_attention(
                        attention_fn,
                        stage="s3",
                        code="s3_verdict_missing",
                        task_uid=uid,
                        severity="warning",
                        title="S3 等待 verdict",
                        detail="未发现通过 verdict，暂不交付，建议确认 QC 与外部验收结果",
                        context={"task_uid": uid},
                    )
                skipped.append(uid)
                continue
            payload = assemble_buyer_payload(row)
            token_cost = estimate_token_cost(str(row.get("line") or ""),
                                             row.get("model_calls"))
            record = build_settlement_record(row, verdict, token_cost, rates=rates)
            source.write_delivery(payload)
            source.write_settlement(record)
            source.mark_delivered(uid)
        except Exception:  # noqa: BLE001 – fail-soft·runner 日志暴露
            _emit_attention(
                attention_fn,
                stage="s3",
                code="s3_delivery_fail",
                task_uid=uid,
                severity="error",
                title="S3 交付失败",
                detail="交付/结算/状态标记任一步失败，建议重跑 S3 runner",
                context={"task_uid": uid},
            )
            failed.append(uid)
            continue
        delivered.append(uid)
        done.add(uid)
    return {"delivered": delivered, "skipped": skipped, "failed": failed}

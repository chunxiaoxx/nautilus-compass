"""FDE verdict-bus ingest API (W1.2) · POST/GET /api/platform/fde/verdict.

The platform's intake for FDE checklist verdicts (soul/v5 producers → platform
substrate). Idempotent on verdict_id. GET reads back by task_uid so compass PoI,
soul-activity (W2), and data_001/data_002 回放 (W3.2) share one persisted source
of truth.

Uses the FdeVerdict ORM model (portable jsonb/JSON). Envelope matches the
platform convention ({success, data, error}).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from datetime import datetime, timezone

from utils.database import get_db
from models.fde_verdict import FdeVerdict
from models.fde_dispatch import FdeDispatch
from services.fde_capability_link import (
    derive_task_type,
    link_capability_from_verdict,
    resolve_agent_id,
)
from services.fde_verdict_guard import apply_verdict_kind_guard
from services.survival_service import SurvivalService

router = APIRouter(prefix="/api/platform/fde", tags=["FDE Verdict Bus"])
logger = logging.getLogger(__name__)

# verdict_id/task_uid/source/overall_pass/score are mandatory; items must be a list.
_REQUIRED = ("verdict_id", "task_uid", "source", "overall_pass", "score")


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


def _coerce_producer_agent_id(db, value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if value is None:
        return None
    if isinstance(value, str) and value.strip().isdigit():
        try:
            return int(value.strip())
        except Exception:  # noqa: BLE001
            return None
    return resolve_agent_id(db, value)


def _resolve_producer_artifacts(db, task_uid: str, artifacts: dict | None) -> tuple[dict, int | None]:
    arts = dict(artifacts if isinstance(artifacts, dict) else {})
    if "producer_agent_id" in arts:
        resolved = _coerce_producer_agent_id(db, arts.get("producer_agent_id"))
        if resolved is not None:
            arts["producer_agent_id"] = resolved
        return arts, resolved

    disp = db.query(FdeDispatch).filter_by(task_uid=task_uid).first()
    if disp is None:
        return arts, None
    if not disp.claimed_by:
        return arts, None
    producer_agent_id = resolve_agent_id(db, disp.claimed_by)
    if producer_agent_id is None:
        return arts, None
    arts["producer_agent_id"] = producer_agent_id
    return arts, producer_agent_id


def _upsert_tasks_ledger(db, row, producer_agent_id) -> None:
    """DMAS task-layer revival (2026-09-10 activation day).

    Land every ingested verdict as a production.tasks row so the task ledger
    (dead since 2026-05-27) reflects executed work again. Idempotent on
    task_id = "verdict-<task_uid>" (SELECT-guard; the column has no DB-level
    unique index despite the ORM declaring unique=True — split-brain, app-level
    dedup is the guard). reward=0 by design: self-mined verdicts are B=0 fuel
    and income accrual stays gated behind external-verify (护栏⑤⑥). Timestamps
    are naive UTC — the columns are timestamp WITHOUT time zone (tz-aware
    values get misread as -8h, see external_verify inline note).
    """
    from models.database import Task, TaskStatus, TaskType

    task_id = f"verdict-{row.task_uid}"[:66]
    if db.query(Task).filter_by(task_id=task_id).first() is not None:
        return
    passed = bool(row.overall_pass)
    now = datetime.utcnow()
    db.add(Task(
        task_id=task_id,
        publisher=str(row.source)[:42],
        description=(f"[{row.source}] {row.task_uid} · verdict {row.verdict_id} "
                     f"pass={str(passed).lower()} score={row.score}"),
        reward=0,
        task_type=TaskType.CODE,
        status=TaskStatus.COMPLETED if passed else TaskStatus.FAILED,
        agent=str(producer_agent_id) if producer_agent_id is not None else "unknown",
        result=f"verdict_id={row.verdict_id} external_verified={bool(row.external_verified)}",
        timeout=3600,
        created_at=now,
        completed_at=now if passed else None,
    ))
    db.commit()


@router.post("/verdict")
def ingest_verdict(body: dict, db=Depends(get_db)):
    """Persist an FDE checklist verdict. Idempotent on verdict_id."""
    missing = [k for k in _REQUIRED if body.get(k) is None]
    if missing:
        return _err(f"missing required field(s): {', '.join(missing)}")

    items = body.get("items")
    if items is None:
        items = []
    if not isinstance(items, list):
        return _err("items must be a list of per-item result objects")

    verdict_id = str(body["verdict_id"])

    existing = db.query(FdeVerdict).filter_by(verdict_id=verdict_id).first()
    # 载荷守卫(2026-09-15 · compass 试点首账:g2-b1 新管自 8/24 起 450/450 items
    # 空,复算不可用)。空载荷仅放行幂等重放;新行拒收,判分方必须逐条落判据/指针。
    if not items and existing is None:
        return _err("items must be non-empty — per-item evidence or reproducible "
                    "pointers required (payload-less verdicts rejected since 2026-09-15)")
    if existing is not None:
        # Idempotent re-ingest · do not duplicate, return the stored row.
        if not existing.artifacts or (
                isinstance(existing.artifacts, dict)
                and existing.artifacts.get("producer_agent_id") is None):
            existing_artifacts, producer_agent_id = _resolve_producer_artifacts(
                db, task_uid=str(existing.task_uid), artifacts=existing.artifacts
            )
            if producer_agent_id is not None:
                existing.artifacts = existing_artifacts
                db.commit()
                db.refresh(existing)
        data = existing.to_dict()
        data["idempotent"] = True
        return _ok(data)

    try:
        score = float(body["score"])
    except (TypeError, ValueError):
        return _err("score must be a number")

    # 齿轮③ verdict 语义守卫:solver_correctness 路径 score=0 强制 pass=false(bvh 类).
    body = apply_verdict_kind_guard(body)
    artifacts, producer_agent_id = _resolve_producer_artifacts(
        db, task_uid=str(body["task_uid"]), artifacts=body.get("artifacts")
    )
    verdict_artifacts = dict(artifacts)
    if body.get("verdict_kind"):
        verdict_artifacts["verdict_kind"] = body["verdict_kind"]
    if producer_agent_id is not None:
        verdict_artifacts["producer_agent_id"] = producer_agent_id

    row = FdeVerdict(
        verdict_id=verdict_id,
        task_uid=str(body["task_uid"]),
        source=str(body["source"]),
        checklist_uid=body.get("checklist_uid"),
        overall_pass=bool(body["overall_pass"]),
        veto_failed=bool(body.get("veto_failed", False)),
        score=score,
        items=items,
        artifacts=verdict_artifacts,
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:  # noqa: BLE001 — surface conflict / DB error cleanly
        db.rollback()
        # A concurrent insert may have won the verdict_id race → treat as idempotent.
        dup = db.query(FdeVerdict).filter_by(verdict_id=verdict_id).first()
        if dup is not None:
            data = dup.to_dict()
            data["idempotent"] = True
            return _ok(data)
        logger.warning("verdict ingest failed: %s", str(exc)[:200])
        return _err("verdict persistence failed", status=500)

    db.refresh(row)

    # Durable writeback(produced→settled)· best-effort.
    # ④ capability LINK 喂点已迁移(2026-08-27 转移线④):自报口径的 settle 喂下线,
    # 能力记账只跟 external-verify 权威转换走(见 PATCH 端点内 feed_capability_on_verify)。
    try:
        disp = db.query(FdeDispatch).filter_by(task_uid=row.task_uid).first()
        if disp is not None and disp.status == "produced":
            disp.status = "settled"
            db.commit()
    except Exception as exc:  # noqa: BLE001 — bookkeeping must not fail the verdict
        db.rollback()
        logger.warning("dispatch settle failed for %s: %s",
                       row.task_uid, str(exc)[:120])

    # DMAS task ledger (2026-09-10): land the tasks row. Fail-soft by contract.
    try:
        _upsert_tasks_ledger(db, row=row, producer_agent_id=producer_agent_id)
    except Exception as exc:  # noqa: BLE001 — bookkeeping must not fail the verdict
        db.rollback()
        logger.warning("tasks ledger upsert failed for %s: %s",
                       row.verdict_id, str(exc)[:120])

    return _ok(row.to_dict())


@router.patch("/verdict/{verdict_id}/external-verify")
def external_verify(verdict_id: str, body: dict, db=Depends(get_db),
                    x_api_key: str | None = Header(None, alias="X-API-Key")):
    """接通 verdict→income 断线(第一刀 · 八代复发根的码级修法)。

    external_verified False→True 是 agent_survival.total_income 的**唯一**入账门。
    只有独立于生产者的 canonical verify 复现产出后才走这里。4 防剧场护栏见内联。
    2026-09-15 鉴权(compass 试点首账:此门原可被任何人换名自置)——X-API-Key
    必填且 verifier_source 必须等于该 key 注册 agent 的名字。
    """
    from api.a2a import _get_agent_from_api_key
    agent = _get_agent_from_api_key(x_api_key, db)  # 401 on missing/invalid key
    verifier_source = (body or {}).get("verifier_source")
    if not verifier_source:
        return _err("verifier_source is required")
    if str(verifier_source).strip().lower() != str(agent.name).strip().lower():
        return _err("verifier_source must match the X-API-Key agent name", status=403)

    row = db.query(FdeVerdict).filter_by(verdict_id=str(verdict_id)).first()
    if row is None:
        return _err("verdict not found", status=404)

    # 护栏 ①:幂等——已 verified 则 no-op,绝不重复入账。
    if row.external_verified:
        data = row.to_dict()
        return _ok({"verdict": data, "income_recorded": False, "amount": 0,
                    "idempotent": True})

    # 护栏 ④:验证器必须独立于生产者(soul ≠ producer)。
    if str(verifier_source) == str(row.source):
        return _err("verifier_source must differ from producer (verdict.source)")

    if row.artifacts is None:
        row.artifacts = {}
    artifacts, producer_agent_id = _resolve_producer_artifacts(db, row.task_uid, row.artifacts)
    row.artifacts = artifacts
    if not isinstance(producer_agent_id, int):
        if "producer_agent_id" in row.artifacts:
            row.artifacts = dict(row.artifacts)
            row.artifacts["producer_agent_id"] = str(row.artifacts["producer_agent_id"])
        return _err("artifacts.producer_agent_id (int) required to record income")

    # 置 external_verified(护栏 ②:income 只在此 False→True 转换记账)。
    # tz-aware:naive utcnow 进 timestamptz 会被 session 时区错解(实测偏 -8h)。
    row.external_verified = True
    row.external_verified_at = datetime.now(timezone.utc)

    # ④ 权威能力喂点(2026-08-27 转移线④):验证转换即记能力(与 income 门独立——
    # 难度档拒铸不影响能力事实)。fail-soft,绝不炸 verdict 主链。
    try:
        from services.capability_feed import feed_capability_on_verify
        feed_capability_on_verify(
            db, agent_id=producer_agent_id, task_uid=str(row.task_uid),
            score=float(row.score or 0.0), success=True)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("capability feed on verify failed for %s: %s",
                       row.verdict_id, str(exc)[:120])

    # 经济门(C 口径 · 2026-07-06 用户拍):验证(认识论)与入账(经济)解耦。
    # 护栏 ⑤ 难度档合格才铸(Rejected/too-easy ≠ 买方可接受价值);
    # 护栏 ⑥ 同 (task_uid × producer) 只铸一次(堵同题重跑刷钱向量)。
    income_gate_reason = None
    if not row.overall_pass:
        income_gate_reason = "not_deliverable_grade"
    else:
        from models.agent_survival import AgentTransaction
        prior = (db.query(AgentTransaction)
                 .filter_by(agent_id=producer_agent_id, type="INCOME",
                            category="fde_external_verified", task_id=row.task_uid)
                 .first())
        if prior is not None:
            income_gate_reason = "task_already_rewarded"

    income_recorded = False
    minted = 0
    if income_gate_reason is None:
        amount = round(float(row.score))
        if amount > 0:
            surv = SurvivalService.get_agent_survival(db, producer_agent_id)
            if surv is None:
                surv = SurvivalService.create_agent_survival(db, producer_agent_id)
            tx = SurvivalService.record_income(
                db, agent_id=producer_agent_id, amount=amount,
                category="fde_external_verified", task_id=row.task_uid,
                description=f"external verify by {verifier_source}")
            income_recorded = tx is not None
            minted = amount if income_recorded else 0

    db.commit()
    db.refresh(row)
    return _ok({"verdict": row.to_dict(), "income_recorded": income_recorded,
                "amount": minted, "income_gate_reason": income_gate_reason})


@router.get("/my-status")
def my_status(agent_id: int, claimed_by: str = None, db=Depends(get_db)):
    """镜子端点(方案② · 2026-07-06 用户拍):agent 可见的 grounded 自身经济真值。

    settled 由 verdict 落库自动翻,不提供自报动词——给镜子不给橡皮图章。
    prime-001 fake-success 1233 次的根源是看不见自己 0 settled;此端点即反馈信号。
    """
    from sqlalchemy import func
    from models.agent_survival import AgentSurvival, AgentTransaction

    pid = FdeVerdict.artifacts["producer_agent_id"].as_integer()
    rows = (db.query(FdeVerdict.overall_pass, FdeVerdict.external_verified)
              .filter(pid == agent_id).all())
    verdicts = {
        "total": len(rows),
        "external_verified": sum(1 for r in rows if r.external_verified),
        "deliverable_grade": sum(1 for r in rows if r.overall_pass),
    }

    surv = db.query(AgentSurvival).filter_by(agent_id=agent_id).first()
    tx_q = db.query(AgentTransaction).filter_by(
        agent_id=agent_id, type="INCOME", category="fde_external_verified")
    last_tx = tx_q.order_by(AgentTransaction.created_at.desc()).first()
    income = {
        "total_income": int(surv.total_income or 0) if surv else 0,
        "tx_count": tx_q.count(),
        "last_income_at": (last_tx.created_at.isoformat()
                           if last_tx and last_tx.created_at else None),
    }

    dispatch = None
    if claimed_by:
        counts = dict(db.query(FdeDispatch.status, func.count(FdeDispatch.id))
                        .filter(FdeDispatch.claimed_by == claimed_by)
                        .group_by(FdeDispatch.status).all())
        dispatch = {"claimed": counts.get("claimed", 0),
                    "produced": counts.get("produced", 0),
                    "settled": counts.get("settled", 0),
                    "total": sum(counts.values())}

    return _ok({
        "agent_id": agent_id,
        "claimed_by": claimed_by,
        "verdicts": verdicts,
        "income": income,
        "dispatch": dispatch,
        "mirror_note": ("settled flips only when an external verdict lands; income "
                        "mints only on external_verified × overall_pass × first-per-task"),
    })


@router.get("/verdict/{task_uid}")
def get_verdicts(task_uid: str, db=Depends(get_db)):
    """Read back all verdicts for a task_uid, most recent first."""
    rows = (
        db.query(FdeVerdict)
        .filter_by(task_uid=task_uid)
        .order_by(FdeVerdict.created_at.desc(), FdeVerdict.id.desc())
        .all()
    )
    return _ok([r.to_dict() for r in rows])

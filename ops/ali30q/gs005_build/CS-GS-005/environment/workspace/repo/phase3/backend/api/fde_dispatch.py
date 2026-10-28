"""DMAS #3 · FDE 生产线 dispatch substrate (platform turf · v1).

The CLEAN dispatch track V5 asked for ("#3 唯一卡点·请建 substrate"). Deliberately
SEPARATE from academic_tasks / platform_bounties (the deprecated internal NAU bounty
market · V5 红线别复活 · G-held). Lifecycle:

    open → (POST /claim) claimed → (POST /report) produced → (verdict-bus) settled

Reward signal = EXTERNAL FDE verdict (fde_verdicts · already LIVE), NOT internal NAU.
The 3 platform-citizen agents (nautilus-prime-001 / v7-telegram / kairos) pull via
GET /tasks?status=open, claim, produce, report. Scoring rides the existing verdict-bus.

Schema answer to V5:
  - 派单表 = fde_dispatch (models/fde_dispatch.py)
  - agent pull   = GET  /api/platform/fde/tasks?status=open
  - agent claim  = POST /api/platform/fde/claim   {task_uid, agent_id}
  - agent report = POST /api/platform/fde/report  {task_uid, agent_id}
  - reward       = external verdict (GET /tasks joins fde_verdicts → settled)

Admin posting (dispatch) is gated by require_platform_key; claim/report carry
agent_id (v1 trust · agent-key hardening tracked).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from utils.database import get_db
from utils.platform_auth import require_platform_key
from models.fde_dispatch import FdeDispatch

router = APIRouter(prefix="/api/platform/fde", tags=["FDE Dispatch Substrate"])
logger = logging.getLogger(__name__)

# A claimed task that never reports within this window is presumed abandoned (the
# claiming daemon died / serves stale code · V5 split-brain orphan 2026-06-20) and
# is reclaimed to `open` so a healthy agent can re-claim it. Env-overridable.
DEFAULT_CLAIM_TIMEOUT_SECONDS = int(os.environ.get("FDE_CLAIM_TIMEOUT_SECONDS", "1800"))


def reap_stale_claims(db, timeout_seconds: int = DEFAULT_CLAIM_TIMEOUT_SECONDS) -> list[str]:
    """Reclaim `claimed` tasks whose claim is older than `timeout_seconds` → `open`.

    Returns the list of reclaimed task_uids. Only touches status=='claimed' rows;
    produced/settled/open are left alone (scope locked). A claimed row with a NULL
    claimed_at (legacy) is treated as stale (unknown age → safe to reclaim).
    """
    cutoff = datetime.utcnow() - timedelta(seconds=max(0, int(timeout_seconds)))
    rows = db.query(FdeDispatch).filter(FdeDispatch.status == "claimed").all()
    reclaimed: list[str] = []
    for row in rows:
        if row.claimed_at is not None and row.claimed_at > cutoff:
            continue  # claim still fresh — an agent may be actively working
        # 9/19 锁丢失根因修(521):reap 只清 claimed_* 三列,**不动
        # description 内的 reserved_for**——回池后正确臂可即刻 reclaim,
        # 其他臂仍被 claim 端点 403 硬门挡,三方抢食不再回归。
        row.status = "open"
        row.claimed_by = None
        row.claimed_at = None
        reclaimed.append(row.task_uid)
    if reclaimed:
        db.commit()
        logger.info("fde reaper reclaimed %d stale claim(s): %s",
                    len(reclaimed), ", ".join(reclaimed))
    return reclaimed


# A `produced` task that never gets a verdict within this window is presumed stuck —
# its output can't be verified (malformed diff / daemon produce-format inconsistency
# 2026-06-21) so the verify poller errors on it every cycle forever. Drain it to a
# terminal status so the poller stops re-picking it. Env-overridable.
DEFAULT_PRODUCED_TIMEOUT_SECONDS = int(os.environ.get("FDE_PRODUCED_TIMEOUT_SECONDS", "1800"))

# #948 (2026-09-24 jumpc): a judge's NON-terminal deferred verdict must hold the task
# out of the drain for a bounded 补件窗 — the 30-min produced window was killing
# "判分已受理等补件" tasks (补件通道名存实亡). Convention: judges write deferred
# verdicts into fde_verdicts with source='deferred' (overall_pass/score carry NO
# semantics for that source — consumers MUST filter by source so deferred rows never
# count as reward-0 fails into the ratchet). Hold is anchored at the LATEST deferred
# verdict's created_at; lapse with no 补件/round2 drains honestly. Env-overridable.
DEFAULT_DEFERRED_HOLD_SECONDS = int(os.environ.get("FDE_DEFERRED_HOLD_SECONDS", "172800"))  # 48h

DEFERRED_VERDICT_SOURCE = "deferred"


def _as_utc(value):
    """sqlite returns created_at as str; postgres as datetime. Unparseable → None
    (caller treats as hold-on-doubt: never kill a task on timestamp ambiguity)."""
    if value is None or isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def reap_stale_produced(db, timeout_seconds: int = DEFAULT_PRODUCED_TIMEOUT_SECONDS,
                        deferred_hold_seconds: int = DEFAULT_DEFERRED_HOLD_SECONDS) -> list[str]:
    """Drain `produced` tasks that are stale AND have no verdict → `abandoned`.

    Returns the list of drained task_uids. A `produced` task with a terminal verdict
    (verified fine) or recently reported (verify may be in flight) is left alone.
    A task whose LATEST verdict is source='deferred' is held while that verdict is
    younger than `deferred_hold_seconds` (判分受理等补件, #948); once the 补件窗
    lapses with no round2 it drains like any other stuck produce. Deliberately does
    NOT write a reward-0 verdict — an unverifiable/malformed output is
    verifier-self-failure (ok=False), not a legit reward 0; fabricating a 0 would
    pollute the ratchet (per fde_bench_poll's contract). A NULL reported_at (legacy)
    is treated as stale. Only touches status=='produced'.
    """
    cutoff = datetime.utcnow() - timedelta(seconds=max(0, int(timeout_seconds)))
    hold_cutoff = datetime.utcnow() - timedelta(seconds=max(0, int(deferred_hold_seconds)))
    rows = db.query(FdeDispatch).filter(FdeDispatch.status == "produced").all()
    drained: list[str] = []
    for row in rows:
        if row.reported_at is not None and row.reported_at > cutoff:
            continue  # recently produced — verify may still be in flight
        verdict = db.execute(
            text("SELECT source, created_at FROM fde_verdicts WHERE task_uid=:tu "
                 "ORDER BY created_at DESC LIMIT 1"),
            {"tu": row.task_uid}).fetchone()
        if verdict is not None:
            if verdict[0] != DEFERRED_VERDICT_SOURCE:
                continue  # terminal verdict — leave it (settled-in-view)
            deferred_at = _as_utc(verdict[1])
            if deferred_at is None or deferred_at > hold_cutoff:
                continue  # 补件窗内 hold(时间戳存疑也 hold——不在存疑时杀单)
            # deferred 窗走完零补件 → fall through, drain honestly
        row.status = "abandoned"
        drained.append(row.task_uid)
    if drained:
        db.commit()
        logger.info("fde drain abandoned %d stuck produced task(s): %s",
                    len(drained), ", ".join(drained))
    return drained


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


def _merge_reserved_for(body: dict):
    """Fold a top-level `reserved_for` into the description JSON (no schema
    change · fuel minters already store JSON strings here). Returns the possibly
    new description value for FdeDispatch."""
    import json as _json

    desc = body.get("description") or ""
    reserved = body.get("reserved_for")
    # dict descriptions are serialized for the Text column (a bare dict used to
    # 500 on bind · p5 rows are minted as JSON strings; accepting dicts outright
    # is strictly better than the old crash).
    if not reserved and not isinstance(desc, dict):
        return desc  # untouched string/None · caller's own contract
    # normalize to a dict for merging (never mutate caller's body)
    if isinstance(desc, dict):
        d = dict(desc)
    else:
        try:
            parsed = _json.loads(desc) if isinstance(desc, str) and desc.strip().startswith("{") else None
        except ValueError:
            parsed = None
        d = dict(parsed) if isinstance(parsed, dict) else ({"_original_description": desc} if desc else {})
    if reserved:
        d["reserved_for"] = str(reserved)  # top-level wins; only when provided
    return _json.dumps(d, ensure_ascii=False)


def _reserved_for(row: FdeDispatch):
    """Read the claim reservation back out of the description JSON, if any."""
    desc = row.description
    if isinstance(desc, dict):
        r = desc.get("reserved_for")
        return str(r) if r else None
    if isinstance(desc, str) and desc.strip().startswith("{"):
        try:
            import json as _json
            d = _json.loads(desc)
            r = d.get("reserved_for") if isinstance(d, dict) else None
            return str(r) if r else None
        except ValueError:
            return None
    return None


@router.post("/dispatch")
def dispatch_fde_task(body: dict, db=Depends(get_db), _=Depends(require_platform_key)):
    """派单: register an FDE buyer task on the production line (status=open). Idempotent."""
    task_uid = body.get("task_uid")
    if not task_uid:
        return _err("task_uid is required")
    existing = db.query(FdeDispatch).filter_by(task_uid=str(task_uid)).first()
    if existing is not None:
        d = existing.to_dict()
        d["idempotent"] = True
        return _ok(d)
    row = FdeDispatch(
        task_uid=str(task_uid),
        title=body.get("title") or f"FDE buyer task {task_uid}",
        description=_merge_reserved_for(body) or "",
        status="open",
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:  # noqa: BLE001 — concurrent insert → idempotent
        db.rollback()
        dup = db.query(FdeDispatch).filter_by(task_uid=str(task_uid)).first()
        if dup is not None:
            d = dup.to_dict(); d["idempotent"] = True
            return _ok(d)
        logger.warning("fde dispatch failed: %s", str(exc)[:160])
        return _err("dispatch persistence failed", status=500)
    db.refresh(row)
    d = row.to_dict(); d["idempotent"] = False
    return _ok(d)


@router.post("/claim")
def claim_fde_task(body: dict, request: Request, db=Depends(get_db)):
    """agent pulls + claims an open task (open → claimed). 409 if already claimed."""
    task_uid, agent_id = body.get("task_uid"), body.get("agent_id")
    if not task_uid or not agent_id:
        return _err("task_uid and agent_id are required")
    from api.org import _auth_check  # 2026-10-11 收口⑩:claimed_by 只认 key 绑定身份
    denied = _auth_check(db, request, str(agent_id))
    if denied:
        return denied
    row = db.query(FdeDispatch).filter_by(task_uid=str(task_uid)).first()
    if row is None:
        return _err("task not found", status=404)
    if row.status != "open":
        return _err(f"task already {row.status} (claimed_by={row.claimed_by})", status=409)
    # Named-claim gate (2026-08-25 · kairos 抢 p5 燃料): a task minted with
    # reserved_for may only be claimed by that agent_id. Unreserved tasks keep
    # the original first-come-first-served open market (S1 unnamed flow).
    reserved = _reserved_for(row)
    if reserved and str(agent_id) != reserved:
        logger.warning("fde claim DENIED: task=%s reserved_for=%s claimed_by=%s",
                       task_uid, reserved, agent_id)
        return _err(f"task reserved for {reserved} (claimed_by={agent_id} not allowed)",
                    status=403)
    # P2 交付率换拉单权(A2 五件套 561 · 平台半边,9/23 落):claimed≥3 且 produced=0
    # → 0 配额(reborn 半成品出局);produced/settled 算交付;新 agent 冷启动放行
    # (阈值前不卡,慢≠半成品)。只看本表 claimed→produced,不掺判分结果(settled 归判分方)。
    _hist = (db.query(FdeDispatch.status)
             .filter(FdeDispatch.claimed_by == str(agent_id)).all())
    _claimed_n = len(_hist)
    _delivered = sum(1 for h in _hist if h[0] in ("produced", "settled"))
    if _claimed_n >= 3 and _delivered == 0:
        logger.warning("fde claim DENIED by P2 quota: agent=%s claimed=%d produced=0",
                       agent_id, _claimed_n)
        return _err(f"P2 quota: {_claimed_n} claimed, 0 produced — deliver before claiming more",
                    status=403)
    row.status = "claimed"
    row.claimed_by = str(agent_id)
    row.claimed_at = datetime.utcnow()
    db.commit(); db.refresh(row)
    return _ok(row.to_dict())


@router.post("/report")
def report_fde_task(body: dict, request: Request, db=Depends(get_db)):
    """agent reports completion + produced output (claimed → produced).

    The `output` (produced answer / deliverable · {text, artifacts, files} or any
    JSON) is PERSISTED here so soul's checklist_scorer / V5 dual-review can read it
    to score → verdict → verdict-bus. This is the produce→verdict spine link
    (V5 6/6 flag · without it the flywheel's produce→verdict half stays open)."""
    task_uid, agent_id = body.get("task_uid"), body.get("agent_id")
    if not task_uid or not agent_id:
        return _err("task_uid and agent_id are required")
    from api.org import _auth_check  # 2026-10-11 收口⑪
    denied = _auth_check(db, request, str(agent_id))
    if denied:
        return denied
    row = db.query(FdeDispatch).filter_by(task_uid=str(task_uid)).first()
    if row is None:
        return _err("task not found", status=404)
    if row.status not in ("claimed", "produced"):
        return _err(f"task is {row.status} · must be claimed before report", status=409)
    row.status = "produced"
    row.reported_at = datetime.utcnow()
    if "output" in body:
        row.output = body["output"]   # persist the produced answer for scoring
    db.commit(); db.refresh(row)
    return _ok(row.to_dict())


@router.post("/reap")
def reap_fde_claims(body: dict = None, db=Depends(get_db), _=Depends(require_platform_key)):
    """Reclaim stale `claimed` tasks back to `open` (claimed-timeout reaper).

    Maintenance op for the V5 daemon orphan failure mode: a daemon that claims then
    dies leaves the task stuck `claimed` forever. Call on a timer (or manually) to
    free abandoned claims. Admin-gated. Body: {timeout_seconds?: int}."""
    body = body or {}
    timeout = body.get("timeout_seconds")
    try:
        timeout = int(timeout) if timeout is not None else DEFAULT_CLAIM_TIMEOUT_SECONDS
    except (TypeError, ValueError):
        return _err("timeout_seconds must be an integer")
    try:
        reclaimed = reap_stale_claims(db, timeout_seconds=timeout)
    except Exception as exc:  # noqa: BLE001 — table absent / db error → fail-soft
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("fde reap failed: %s", str(exc)[:160])
        return _err("reap failed", status=500)
    return _ok({"reclaimed": reclaimed, "count": len(reclaimed),
                "timeout_seconds": timeout})


@router.post("/drain")
def drain_fde_produced(body: dict = None, db=Depends(get_db), _=Depends(require_platform_key)):
    """Drain stuck `produced` tasks (no verdict, stale) → `abandoned`.

    Maintenance op for malformed-output tasks that error on verify every cycle
    forever (daemon produce-format inconsistency 2026-06-21). Admin-gated. Body:
    {timeout_seconds?: int, deferred_hold_seconds?: int}. Does NOT write a verdict
    (avoids ratchet pollution). deferred(source='deferred' 最新判分)在 hold 窗内不扫
    (#948 补件通道)。"""
    body = body or {}
    timeout = body.get("timeout_seconds")
    hold = body.get("deferred_hold_seconds")
    try:
        timeout = int(timeout) if timeout is not None else DEFAULT_PRODUCED_TIMEOUT_SECONDS
        hold = int(hold) if hold is not None else DEFAULT_DEFERRED_HOLD_SECONDS
    except (TypeError, ValueError):
        return _err("timeout_seconds/deferred_hold_seconds must be integers")
    try:
        drained = reap_stale_produced(db, timeout_seconds=timeout,
                                      deferred_hold_seconds=hold)
    except Exception as exc:  # noqa: BLE001 — table absent / db error → fail-soft
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("fde drain failed: %s", str(exc)[:160])
        return _err("drain failed", status=500)
    return _ok({"drained": drained, "count": len(drained),
                "timeout_seconds": timeout, "deferred_hold_seconds": hold})


@router.get("/tasks")
def list_fde_tasks(status: str = Query(None), db=Depends(get_db)):
    """List FDE production-line tasks + latest verdict (loop status). Fail-soft.

    A task with a verdict is reported as 'settled' (the external signal closed it)."""
    try:
        q = db.query(FdeDispatch)
        if status:
            q = q.filter_by(status=str(status))
        rows = q.order_by(FdeDispatch.created_at.desc()).all()
    except Exception as exc:  # noqa: BLE001 — table absent → empty
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("list fde tasks skipped: %s", str(exc)[:120])
        rows = []

    tasks = []
    counts = {"open": 0, "claimed": 0, "produced": 0, "settled": 0}
    for r in rows:
        verdict = None
        try:
            v = db.execute(text(
                "SELECT overall_pass, veto_failed, score, source FROM fde_verdicts "
                "WHERE task_uid=:tu ORDER BY created_at DESC, id DESC LIMIT 1"),
                {"tu": r.task_uid}).fetchone()
            if v is not None:
                verdict = {"overall_pass": bool(v[0]), "veto_failed": bool(v[1]),
                           "score": v[2], "source": v[3]}
        except Exception:
            pass
        d = r.to_dict()
        # 9/19 锁丢失误报根因修(521):锁活在 description JSON 里但视图不
        # 展开,v5 看不见→误报丢失→平台误判重锁。观测透明化:输出解析后的
        # reserved_for 字段,此类"看不见当不存在"的误判不再发生。
        d["reserved_for"] = _reserved_for(r)
        # a verdict closes the loop → effective status 'settled' in the view.
        eff_status = "settled" if verdict is not None else d["status"]
        d["status"] = eff_status
        d["verdict"] = verdict
        tasks.append(d)
        counts[eff_status] = counts.get(eff_status, 0) + 1

    return _ok({
        "tasks": tasks,
        "summary": {**counts, "dispatched": len(tasks),
                    "settled": counts.get("settled", 0)},
    })

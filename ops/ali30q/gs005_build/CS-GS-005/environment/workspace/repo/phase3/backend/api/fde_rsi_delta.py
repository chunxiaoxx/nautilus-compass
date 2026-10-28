"""ΔReward → PoI fuel ingest API (Horizon 2 · cnt_c3) · POST/GET /api/platform/fde/rsi_delta.

Platform intake for RSI grounded-vs-bare ΔReward measurements (soul
grounding_probe_twosample → platform substrate). Idempotent on delta_id.
GET reads back by task_uid; ?escapes_only=true returns the PoI-eligible feed
(escapes_noise=True only) compass subscribes to — the gate that keeps PoI honest.

Mirrors fde_verdict.py. Envelope {success, data, error}. Not wired into main.py
until deploy (G-cloud · gated).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from utils.database import get_db
from models.fde_rsi_delta import FdeRsiDelta

router = APIRouter(prefix="/api/platform/fde", tags=["FDE RSI Delta (PoI fuel)"])
logger = logging.getLogger(__name__)

# delta_id/benchmark/task_uid/delta_reward/escapes_noise are mandatory.
_REQUIRED = ("delta_id", "benchmark", "task_uid", "delta_reward", "escapes_noise")


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


@router.post("/rsi_delta")
def ingest_rsi_delta(body: dict, db=Depends(get_db)):
    """Persist an RSI ΔReward measurement. Idempotent on delta_id."""
    missing = [k for k in _REQUIRED if body.get(k) is None]
    if missing:
        return _err(f"missing required field(s): {', '.join(missing)}")

    delta_id = str(body["delta_id"])
    existing = db.query(FdeRsiDelta).filter_by(delta_id=delta_id).first()
    if existing is not None:
        data = existing.to_dict()
        data["idempotent"] = True
        return _ok(data)

    try:
        delta_reward = float(body["delta_reward"])
        bare_mean = float(body.get("bare_mean", 0.0))
        grounded_mean = float(body.get("grounded_mean", 0.0))
        p_value = None if body.get("p_value") is None else float(body["p_value"])
    except (TypeError, ValueError):
        return _err("bare_mean/grounded_mean/delta_reward/p_value must be numbers")

    row = FdeRsiDelta(
        delta_id=delta_id,
        benchmark=str(body["benchmark"]),
        task_uid=str(body["task_uid"]),
        producer_model=body.get("producer_model"),
        n_bare=int(body.get("n_bare", 0) or 0),
        n_grounded=int(body.get("n_grounded", 0) or 0),
        bare_mean=bare_mean,
        grounded_mean=grounded_mean,
        delta_reward=delta_reward,
        p_value=p_value,
        escapes_noise=bool(body["escapes_noise"]),
        grounding_source=body.get("grounding_source") or {},
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        dup = db.query(FdeRsiDelta).filter_by(delta_id=delta_id).first()
        if dup is not None:
            data = dup.to_dict()
            data["idempotent"] = True
            return _ok(data)
        logger.warning("rsi_delta ingest failed: %s", str(exc)[:200])
        return _err("rsi_delta persistence failed", status=500)

    db.refresh(row)
    return _ok(row.to_dict())


@router.get("/rsi_delta/{task_uid}")
def get_rsi_deltas(task_uid: str, escapes_only: bool = False, db=Depends(get_db)):
    """Read back ΔReward rows for a task_uid, most recent first.

    escapes_only=true → the PoI-eligible feed (escapes_noise=True only) that
    compass subscribes to. escapes_noise=False rows persist for transparency /
    复利 time-series but are excluded from PoI crediting.
    """
    q = db.query(FdeRsiDelta).filter_by(task_uid=task_uid)
    if escapes_only:
        q = q.filter_by(escapes_noise=True)
    rows = q.order_by(FdeRsiDelta.created_at.desc(), FdeRsiDelta.id.desc()).all()
    return _ok([r.to_dict() for r in rows])

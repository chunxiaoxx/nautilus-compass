"""Org OS · fuel 轨迹通道(轨迹→燃料采集器,涡轮增压第一环·2026-10-04)。

承 v5 FUEL_ORDER_SPEC_V1 §二(交付物 schema)与 turbo_pipeline.v1 六环坐标表:
  发单环=platform_bounties(task_type=fuel_trajectory,v5 post_fuel_orders.py 已在跑,
  60 单存量);本通道=v5 交付文案点名的 "via writeback kind=fuel_trajectory" 落库件。
  - POST /api/platform/org/fuel/trajectories   轨迹包 upsert(幂等 by traj_id)
  - GET  /api/platform/org/fuel/pipeline       六环坐标(registry 正本)+双环动态读数
判据主权在 v5 四验门:本端点只做 schema 级校验+存档(禁 LLM 自报 label 三态等硬
字段);四验门结果由 v5 侧带 gates 回填,status: received→gated→(v5 池化 in_pool)。
表沿 proposal_outcomes 先例裸 SQL(migration 接最新 tip),鉴权 require_platform_key。
"""
from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text

from utils.database import get_db
from utils.platform_auth import require_platform_key

router = APIRouter(prefix="/api/platform/org/fuel", tags=["Org Fuel Trajectory"])

FUEL_THRESHOLD = 50  # TSI 六环·训练池触发线(v5 pipeline Step2)


class TrajPack(BaseModel):
    """FUEL_ORDER_SPEC_V1 §二 交付物 + 通道元数据。"""
    traj_id: str
    submitter: str
    qid: str
    context: str = Field(min_length=1)  # 四验门第1条 render 非空,schema 层前置
    trajectory: list[dict] = Field(min_length=1)  # OpenAI messages 原文,禁一次性全文
    verdict: Literal["pass", "fail", "insufficient_evidence"]
    label_origin: Literal["verifier", "official_answer"]  # 禁 LLM 自报
    bounty_id: str | None = None
    failure_tag: str | None = None
    gates: dict | None = None  # v5 四验门结果回填槽(四条判定+对口性诊断)


def _load_turbo_registry() -> dict:
    """六环坐标表正本(registry/turbo_pipeline.json,v5 478607a2 转存)。"""
    from pathlib import Path
    f = Path(__file__).resolve().parents[1] / "registry" / "turbo_pipeline.json"
    return json.loads(f.read_text(encoding="utf-8"))


@router.post("/trajectories")
def writeback_trajectory(pack: TrajPack, db=Depends(get_db),
                         _=Depends(require_platform_key)):
    """轨迹包 upsert:新 traj_id=received;已存在且带 gates=v5 四验门回填;余=skip。"""
    inserted = updated = skipped = 0
    row = db.execute(text("SELECT gates FROM fuel_trajectories WHERE traj_id=:t"),
                     {"t": pack.traj_id}).fetchone()
    if row is None:
        db.execute(text(
            "INSERT INTO fuel_trajectories (traj_id, bounty_id, submitter, qid, "
            "context, trajectory, verdict, label_origin, failure_tag, gates, status) "
            "VALUES (:tid, :bid, :sub, :qid, :ctx, CAST(:traj AS jsonb), :ver, :lo, "
            ":ftag, CAST(:gates AS jsonb), :st)"),
            {"tid": pack.traj_id, "bid": pack.bounty_id, "sub": pack.submitter,
             "qid": pack.qid, "ctx": pack.context,
             "traj": json.dumps(pack.trajectory, ensure_ascii=False),
             "ver": pack.verdict, "lo": pack.label_origin, "ftag": pack.failure_tag,
             "gates": json.dumps(pack.gates, ensure_ascii=False) if pack.gates else None,
             "st": "gated" if pack.gates else "received"})
        inserted = 1
    elif pack.gates:
        db.execute(text(
            "UPDATE fuel_trajectories SET gates=CAST(:gates AS jsonb), "
            "verdict=:ver, status='gated' WHERE traj_id=:t"),
            {"gates": json.dumps(pack.gates, ensure_ascii=False),
             "ver": pack.verdict, "t": pack.traj_id})
        updated = 1
    else:
        skipped = 1
    db.commit()
    total = db.execute(text("SELECT COUNT(*) FROM fuel_trajectories")).fetchone()[0]
    return {"success": True, "data": {
        "traj_id": pack.traj_id, "inserted": inserted,
        "updated": updated, "skipped": skipped, "pool_total": total}}


@router.get("/pipeline")
async def fuel_pipeline(db=Depends(get_db)):
    """六环读数面:registry 坐标 verbatim + 发单环/池环 DB 动态读数(六环指标§二)。"""
    reg = _load_turbo_registry()
    bounty_rows = db.execute(text(
        "SELECT status, COUNT(*) FROM platform_bounties "
        "WHERE task_type='fuel_trajectory' GROUP BY status")).fetchall()
    pool_rows = db.execute(text(
        "SELECT status, COUNT(*) FROM fuel_trajectories GROUP BY status")).fetchall()
    gated = db.execute(text(
        "SELECT COUNT(*) FROM fuel_trajectories "
        "WHERE status='gated' AND verdict='pass'")).fetchone()[0]
    return {"success": True, "data": {
        "schema": reg.get("schema", "turbo_pipeline.v1"),
        "stages": reg.get("stages", []),
        "readings": {
            "bounty_stage": {s: n for s, n in bounty_rows},
            "pool_stage": {s: n for s, n in pool_rows},
            "pool_gated_pass": gated,
            "fuel_threshold": FUEL_THRESHOLD,
        }}}

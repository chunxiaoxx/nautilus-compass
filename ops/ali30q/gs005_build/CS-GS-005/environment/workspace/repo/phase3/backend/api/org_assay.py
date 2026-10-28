"""Org OS · assay 数据验证通道(b 档:客户自带轨迹→独立判读,M3 契约草案 v0.1)。

契约正本:chunxiaoxx/nautilus-v5 docs/M3_B_TIER_API_DRAFT_20261006.md(0925295c);
三处 compass 会签补强已入(#10066):独立凭据环境/UNVERIFIABLE 预披露/gates-verdict 分列。
  - POST /api/platform/org/assay/validate        客户轨迹批受理(同步机器门,异步深门)
  - GET  /api/platform/org/assay/validate/{id}   逐条三态判定+gates+摘要
V0 边界(诚实条款):机器门(render 非空/qid 唯一/prompt 去重)本地同步判;深门
(held-out 交集/gold 可解析)判读臂未接入=UNVERIFIABLE 照报——判不动就明说,
禁缺席也禁假绿。表沿 org_fuel 先例裸 SQL。SLA=受理+3 工作日(V0 自然日近似)。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.types import JSON as JSONB

from utils.database import get_db
from utils.platform_auth import require_platform_key

router = APIRouter(prefix="/api/platform/org/assay", tags=["Org Assay Validation (b-tier)"])

SLA_DAYS = 3
_booted = False


def _ensure_tables(db) -> None:
    """幂等同库建表(org_fuel 先例):engagements 主表+判据登记(受理即冻结的物理面)。"""
    global _booted
    if _booted:
        return
    db.execute(text(
        "CREATE TABLE IF NOT EXISTS assay_engagements ("
        "engagement_id TEXT PRIMARY KEY, criteria_sha TEXT NOT NULL, status TEXT NOT NULL, "
        "payload JSONB NOT NULL, created_at TIMESTAMPTZ DEFAULT now(), sla_deadline TIMESTAMPTZ)"))
    db.execute(text(
        "CREATE TABLE IF NOT EXISTS assay_criteria_registry ("
        "sha16 TEXT PRIMARY KEY, name TEXT, registered_at TIMESTAMPTZ DEFAULT now())"))
    db.execute(text(
        "INSERT INTO assay_criteria_registry (sha16, name) VALUES ('ea20d6fd', 'fuel_criteria_v1') "
        "ON CONFLICT (sha16) DO NOTHING"))
    db.commit()
    _booted = True


class CustomerTraj(BaseModel):
    """客户自带轨迹最小契约(verdict schema v2.1 子集,context 可选)。"""
    qid: str = Field(min_length=1)
    trajectory: list[dict]  # OpenAI messages 原文;空=render 门 fail
    context: str | None = None


class ValidateReq(BaseModel):
    engagement_id: str = Field(min_length=1)
    criteria_sha: str = Field(min_length=1)  # 受理即冻结(棘轮);未知 sha=422
    trajectories: list[CustomerTraj] = Field(min_length=1, max_length=500)


def _fp(msgs: list[dict]) -> str:
    """prompt 指纹(去重门):消息序列规范化哈希。"""
    return hashlib.sha1(
        json.dumps(msgs, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


def _machine_gates(items: list[CustomerTraj]) -> list[dict]:
    """三机器门同步判 + 两深门 UNVERIFIABLE 照报(V0)。"""
    seen_qid: set[str] = set()
    seen_fp: set[str] = set()
    out = []
    for it in items:
        fp = _fp(it.trajectory)
        dup_qid = it.qid in seen_qid
        dup_fp = fp in seen_fp
        seen_qid.add(it.qid)
        seen_fp.add(fp)
        gates = {
            "render_nonempty": "fail" if not it.trajectory else "pass",
            "qid_unique": "fail" if dup_qid else "pass",
            "prompt_dedup": "fail" if dup_fp else "pass",
            "heldout_disjoint": "unverifiable",   # 判读臂接入前照报(#10066 二)
            "gold_parseable": "unverifiable",
        }
        verdict = "fail" if "fail" in gates.values() else "unverifiable"
        out.append({"qid": it.qid, "fp16": fp, "gates": gates, "verdict": verdict})
    return out


@router.post("/validate")
def validate(req: ValidateReq, db=Depends(get_db),
             _=Depends(require_platform_key)):
    _ensure_tables(db)
    known = db.execute(text(
        "SELECT 1 FROM assay_criteria_registry WHERE sha16=:s"), {"s": req.criteria_sha}
    ).first()
    if not known:
        raise HTTPException(422, f"unknown criteria_sha {req.criteria_sha}(受理即冻结,须预注册)")
    results = _machine_gates(req.trajectories)
    payload = {"criteria_sha": req.criteria_sha,
               "per_item": [{"qid": r["qid"], "verdict": r["verdict"], "gates": r["gates"]} for r in results]}
    sla_dt = datetime.utcnow() + timedelta(days=SLA_DAYS)
    db.execute(text(
        "INSERT INTO assay_engagements (engagement_id, criteria_sha, status, payload, created_at, sla_deadline) "
        "VALUES (:e, :c, 'machine_gated', CAST(:p AS JSONB), now(), CAST(:sla AS timestamptz)) "
        "ON CONFLICT (engagement_id) DO UPDATE SET payload=CAST(:p AS JSONB), status='machine_gated'"
    ), {"e": req.engagement_id, "c": req.criteria_sha,
        "p": json.dumps(payload, ensure_ascii=False), "sla": sla_dt.isoformat()})
    db.commit()
    return {"engagement_id": req.engagement_id, "received_n": len(req.trajectories),
            "sla_deadline": sla_dt.isoformat(),
            "note": "机器门已判;深门(held-out/gold)判读臂接入前=UNVERIFIABLE 照报"}


@router.get("/validate/{engagement_id}")
def get_result(engagement_id: str, db=Depends(get_db),
               _=Depends(require_platform_key)):
    _ensure_tables(db)
    row = db.execute(text(
        "SELECT payload, status, sla_deadline FROM assay_engagements WHERE engagement_id=:e"
    ), {"e": engagement_id}).first()
    if not row:
        raise HTTPException(404, "engagement not found")
    p = row[0]
    n = len(p["per_item"])
    return {"engagement_id": engagement_id, "status": row[1],
            "sla_deadline": row[2].isoformat() if row[2] else None,
            "per_item": p["per_item"],
            "summary": {"n": n,
                        "fail": sum(1 for i in p["per_item"] if i["verdict"] == "fail"),
                        "unverifiable": sum(1 for i in p["per_item"] if i["verdict"] == "unverifiable"),
                        "pass": sum(1 for i in p["per_item"] if i["verdict"] == "pass")}}

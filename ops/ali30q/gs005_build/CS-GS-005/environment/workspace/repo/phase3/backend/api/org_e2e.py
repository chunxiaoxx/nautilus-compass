"""Org OS · 管道 E2E 验证端点(每单五段链活读数,数据飞轮可验证性的一站面)。

GET /api/platform/org/pipeline/e2e?lo=b-turbo-f196&hi=b-turbo-f215
  → {units:[{bounty_id,qid,verdict,stages{S1..S5},full_loop}],summary{total,full,broken}}
与 v5 侧 pipeline_e2e_verify.py 同逻辑(跨框正本=DB 实态,双端重跑一致)。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from utils.database import get_db
from utils.platform_auth import require_platform_key

router = APIRouter(prefix="/api/platform/org/pipeline", tags=["Org Pipeline E2E"])


@router.get("/e2e")
def e2e(lo: str = Query(...), hi: str = Query(...), db=Depends(get_db)):
    """公开只读(2026-10-07 免认证):逐单五段链=对外透明验证件(pipeline_platform.html SPA 公网 fetch),
    范围由 lo/hi 限定且仅 SELECT;写路径/判分写回仍在别处严鉴权。"""
    bounties = dict(db.execute(text(
        "SELECT bounty_id, status FROM platform_bounties "
        "WHERE bounty_id LIKE 'b-turbo-f%' AND bounty_id >= :lo AND bounty_id <= :hi"),
        {"lo": lo, "hi": hi}).fetchall())
    trajs = {r[0]: r for r in db.execute(text(
        "SELECT bounty_id, qid, verdict, gates IS NOT NULL AS has_gates, created_at "
        "FROM fuel_trajectories WHERE bounty_id LIKE 'b-turbo-f%' "
        "AND bounty_id >= :lo AND bounty_id <= :hi"),
        {"lo": lo, "hi": hi}).fetchall()}
    ledger = dict(db.execute(text(
        "SELECT linked_bounty_id, sum(delta) FROM platform_nau_ledger "
        "WHERE linked_bounty_id LIKE 'b-turbo-f%' "
        "AND linked_bounty_id >= :lo AND linked_bounty_id <= :hi GROUP BY linked_bounty_id"),
        {"lo": lo, "hi": hi}).fetchall())

    units, full = [], 0
    for bid in sorted(bounties):
        status = bounties[bid]
        t = trajs.get(bid)
        pay = ledger.get(bid)
        stages = {
            "S1_dispatch": "PASS" if status else "ABSENT",
            "S2_delivery": "PASS" if t else ("FAIL" if status in ("scored", "completed") else "PENDING"),
            "S3_fourgate": ("PASS" if t[3] else "FAIL(no-gates)") if t else "PENDING",
            "S4_pool": "PASS" if t else "PENDING",
            "S5_settle": "PASS" if pay else ("PENDING" if status == "scored" else "N/A"),
        }
        chain_ok = all(v in ("PASS", "N/A") for v in stages.values())
        full += chain_ok
        units.append({"bounty_id": bid, "bounty_status": status,
                      "qid": t[1] if t else None, "verdict": t[2] if t else None,
                      "ledger_delta": pay, "stages": stages, "full_loop": chain_ok})
    broken = [u["bounty_id"] for u in units if not u["full_loop"]]
    return {"range": [lo, hi], "total": len(units), "full_loop": full,
            "broken": broken, "units": units}

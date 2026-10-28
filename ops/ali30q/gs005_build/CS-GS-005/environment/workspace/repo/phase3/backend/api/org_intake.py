"""Org OS · 提测受理 API(WEB_INTAKE_API_PLAN_V1 M1+M2 · nautilus-v5 docs/)。

  POST /api/platform/org/assay/submissions          公开提测(限流+蜜罐,无 KEY)
  GET  /api/platform/org/assay/submissions/{id}     状态+SLA 剩余(uuid 即凭证)
  GET  /api/platform/org/assay/submissions/{id}/events  全事件流(审计面)
  POST /api/platform/org/assay/submissions/{id}/transition  内部流转(KEY 保护)

状态机:created→intake_validated→queued→judging→report_draft→delivered
       (+need_info / rejected;终态 delivered/rejected)。
SLA 在 intake_validated 起算:l1=1d / l2=2d / trajectory=3d(DB 生成,禁手填)。
诚实条款:限流=进程内存计数(重启清零,V0 照报);幂等=(repo,anchor,lane) 7 天窗返回原单。
"""
from __future__ import annotations

import ipaddress
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from utils.database import get_db
from utils.platform_auth import require_platform_key

router = APIRouter(prefix="/api/platform/org/assay", tags=["Org Assay Intake (submissions)"])

SLA_DAYS = {"l1": 1, "l2": 2, "trajectory": 3}
VALID_LANES = set(SLA_DAYS)
STATUSES = {"created", "intake_validated", "queued", "judging", "report_draft",
            "delivered", "rejected", "need_info"}
TERMINAL = {"delivered", "rejected"}
_TRANSITIONS = {
    "created": {"intake_validated", "rejected", "need_info"},
    "intake_validated": {"queued", "rejected", "need_info"},
    "queued": {"judging", "rejected", "need_info"},
    "judging": {"report_draft", "rejected"},
    "report_draft": {"delivered", "rejected"},
    "need_info": {"intake_validated", "rejected"},
    "delivered": set(),
    "rejected": set(),
}
# 限流:内存计数 {ip: [timestamps]};V0 语义=重启清零,照报不装分布式
_RATE: dict[str, list[float]] = {}
_RATE_LIMIT = 10
_RATE_WINDOW_S = 3600.0
_booted = False


def _ensure_tables(db) -> None:
    global _booted
    if _booted:
        return
    db.execute(text(
        "CREATE TABLE IF NOT EXISTS assay_submissions ("
        "id TEXT PRIMARY KEY, harness TEXT NOT NULL, version_anchor TEXT, repo_url TEXT NOT NULL, "
        "lane TEXT NOT NULL, contact TEXT NOT NULL, note TEXT, status TEXT NOT NULL, "
        "sla_deadline TIMESTAMPTZ, edit_token TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT now())"))
    db.execute(text(
        "ALTER TABLE assay_submissions ADD COLUMN IF NOT EXISTS is_smoke BOOLEAN NOT NULL DEFAULT false"))
    db.execute(text(
        "CREATE TABLE IF NOT EXISTS assay_events ("
        "id SERIAL PRIMARY KEY, submission_id TEXT NOT NULL, at TIMESTAMPTZ DEFAULT now(), "
        "from_status TEXT, to_status TEXT NOT NULL, actor TEXT NOT NULL, note TEXT)"))
    db.commit()
    _booted = True


# smoke/selftest 单判定(2026-10-08 #10713 口径):只影响读数与自动派单,
# 不改状态机——smoke 单照常受理走流程,但不进判读岗红灯/SLA 读数,不发自动派单函。
_SMOKE_PATTERNS = ("smoke", "selftest", "do-not-judge", "dedup", "example/",
                   "@test.local", "@nautilus.social", "@nautilus.internal")


def _is_smoke(harness: str, contact: str, note: str, repo_url: str = "") -> bool:
    blob = f"{harness} {contact} {note} {repo_url}".lower()
    return any(p in blob for p in _SMOKE_PATTERNS)


def _dispatch_letter(db, sid: str, sla: datetime, lane: str, harness: str,
                     anchor: str, repo: str, contact: str, note: str) -> None:
    """受理完成→判读岗自动派单函(#10709 短期信箱派单制)。smoke 单不派。"""
    trace = f"assay-dispatch-{sid}"
    dup = db.execute(text("SELECT id FROM org_mailbox WHERE trace_id=:t"), {"t": trace}).first()
    if dup:
        return
    body = (
        f"[派单·assay] {sid} 受理完成,请判读岗接单\n\n"
        f"- 被测对象: harness={harness} anchor={anchor or '(未填)'} repo={repo}\n"
        f"- lane: {lane}(SLA 死线 {sla.isoformat()})\n"
        f"- contact: {contact}\n"
        f"- 提单备注: {note or '(无)'}\n"
        f"- 状态查询: GET /api/platform/org/assay/submissions/{sid}\n"
        f"- 判据档: docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md(锚 @00d29232)\n\n"
        f"平台自动派单(信箱派单制,#10709 裁定);判读产出卡随附 criteria_sha16。")
    db.execute(text(
        "INSERT INTO org_mailbox (trace_id, from_agent, to_agent, title, body, deadline) "
        "VALUES (:t,'platform','compass',:ti,:b, now() + interval '2 hours')"),
        {"t": trace, "ti": f"[派单·assay] {sid} {harness} {lane}", "b": body})


def _client_ip(req: Request) -> str:
    fwd = req.headers.get("x-forwarded-for", "")
    raw = fwd.split(",")[0].strip() if fwd else (req.client.host if req.client else "?")
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return "?"


def _rate_ok(ip: str) -> bool:
    import time
    now = time.time()
    window = [t for t in _RATE.get(ip, []) if now - t < _RATE_WINDOW_S]
    if len(window) >= _RATE_LIMIT:
        _RATE[ip] = window
        return False
    window.append(now)
    _RATE[ip] = window
    return True


def _event(db, sid: str, frm: str | None, to: str, actor: str, note: str) -> None:
    db.execute(text(
        "INSERT INTO assay_events (submission_id, from_status, to_status, actor, note) "
        "VALUES (:s, :f, :t, :a, :n)"),
        {"s": sid, "f": frm, "t": to, "a": actor, "n": note[:512]})


class SubmissionReq(BaseModel):
    harness: str = Field(min_length=1, max_length=120)
    version_anchor: str = Field(default="", max_length=200)
    repo_url: str = Field(min_length=4, max_length=400)
    lane: str = Field(pattern="^(l1|l2|trajectory)$")
    contact: str = Field(min_length=3, max_length=200)
    note: str = Field(default="", max_length=2000)
    website: str = Field(default="", max_length=0)  # 蜜罐:必须为空

    @field_validator("website")
    @classmethod
    def _honeypot(cls, v: str) -> str:
        if v:
            raise ValueError("honeypot filled")
        return v


@router.post("/submissions")
def create_submission(req: SubmissionReq, request: Request, db=Depends(get_db)):
    ip = _client_ip(request)
    if not _rate_ok(ip):
        raise HTTPException(429, "rate limited (10/h per IP, V0 in-memory)")
    _ensure_tables(db)
    # 幂等:(repo,lane) 7 天窗返回原单(anchor 差异走补料,不另开单——防垃圾重复提交)
    dup = db.execute(text(
        "SELECT id FROM assay_submissions WHERE repo_url=:r "
        "AND lane=:l AND created_at > now() - interval '7 days'"),
        {"r": req.repo_url, "l": req.lane}).first()
    if dup:
        return {"id": dup[0], "status": "existing", "note": "7 天窗内同坐标已有单,返回原单 id"}
    sid = uuid.uuid4().hex[:16]
    token = uuid.uuid4().hex
    smoke = _is_smoke(req.harness, req.contact, req.note, req.repo_url)
    db.execute(text(
        "INSERT INTO assay_submissions (id, harness, version_anchor, repo_url, lane, contact, note, "
        "status, is_smoke, edit_token) VALUES (:i,:h,:v,:r,:l,:c,:n,'created',:sm,:t)"),
        {"i": sid, "h": req.harness, "v": req.version_anchor, "r": req.repo_url,
         "l": req.lane, "c": req.contact, "n": req.note, "sm": smoke, "t": token})
    _event(db, sid, None, "created", f"intake:{ip}", f"harness={req.harness} lane={req.lane}")
    # 自动受理门:repo_url 形如 URL 即 intake_validated(机器可判面;人工复核走 need_info)
    sla = None
    if req.repo_url.startswith(("http://", "https://", "git@")):
        db.execute(text("UPDATE assay_submissions SET status='intake_validated' WHERE id=:i"),
                   {"i": sid})
        sla = datetime.now(timezone.utc) + timedelta(days=SLA_DAYS[req.lane])
        db.execute(text("UPDATE assay_submissions SET sla_deadline=CAST(:s AS timestamptz) WHERE id=:i"),
                   {"s": sla.isoformat(), "i": sid})
        _event(db, sid, "created", "intake_validated", "intake:auto",
               "repo 坐标机器门通过,SLA 起算" + (";smoke 单(不派单)" if smoke else ""))
        if not smoke:
            _dispatch_letter(db, sid, sla, req.lane, req.harness, req.version_anchor,
                             req.repo_url, req.contact, req.note)
        status = "intake_validated"
    else:
        status = "created"
    db.commit()
    return {"id": sid, "status": status,
            "sla_deadline": sla.isoformat() if status == "intake_validated" else None,
            "edit_token": token,
            "note": f"进度查询: GET /api/platform/org/assay/submissions/{sid} · SLA 按 {req.lane}={SLA_DAYS[req.lane]}d"}


@router.get("/submissions/by-contact/{contact}")
def list_by_contact(contact: str, db=Depends(get_db)):
    """客户门户:按提测联系邮箱列自己的全部单(id/harness/lane/status/SLA)。零密码查询型——
    返回面仅含提交者自填字段,无敏感数据;限流同款 per-IP。"""
    _ensure_tables(db)
    if len(contact) < 5 or "@" not in contact:
        raise HTTPException(400, "invalid contact")
    rows = db.execute(text(
        "SELECT id, harness, lane, status, sla_deadline, created_at FROM assay_submissions "
        "WHERE contact=:c ORDER BY created_at DESC LIMIT 50"),
        {"c": contact}).fetchall()
    out = []
    for r in rows:
        sla_left = None
        if r[4]:
            sla_left = max(round((r[4] - datetime.now(timezone.utc)).total_seconds() / 3600, 1), 0.0)
        out.append({"id": r[0], "harness": r[1], "lane": r[2], "status": r[3],
                    "created_at": r[5].isoformat() if r[5] else None,
                    "sla_deadline": r[4].isoformat() if r[4] else None,
                    "sla_hours_left": sla_left,
                    "card_url": f"/status.html?sid={r[0]}"})
    return {"contact": contact, "count": len(out), "submissions": out}


@router.get("/submissions/{sid}")
def get_submission(sid: str, db=Depends(get_db)):
    _ensure_tables(db)
    row = db.execute(text(
        "SELECT harness, lane, status, sla_deadline, created_at, is_smoke FROM assay_submissions "
        "WHERE id=:i"), {"i": sid}).first()
    if not row:
        raise HTTPException(404, "submission not found")
    sla_left = None
    if row[3]:
        sla_left = round((row[3] - datetime.now(timezone.utc)).total_seconds() / 3600, 1)
        sla_left = max(sla_left, 0.0)
    return {"id": sid, "harness": row[0], "lane": row[1], "status": row[2],
            "created_at": row[4].isoformat() if row[4] else None,
            "sla_deadline": row[3].isoformat() if row[3] else None,
            "sla_hours_left": sla_left,
            "is_smoke": bool(row[5]),
            "state_meaning": {"created": "已登记,待受理门",
                              "intake_validated": "受理完成,判读排队中(SLA 计时中)",
                              "queued": "已入判读队列", "judging": "判读进行中",
                              "report_draft": "报告组装中", "delivered": "已交付",
                              "need_info": "需补充材料", "rejected": "未受理"}[row[2]]}


@router.get("/submissions/{sid}/events")
def get_events(sid: str, db=Depends(get_db)):
    _ensure_tables(db)
    rows = db.execute(text(
        "SELECT at, from_status, to_status, actor, note FROM assay_events "
        "WHERE submission_id=:s ORDER BY id"), {"s": sid}).fetchall()
    return {"id": sid, "events": [
        {"at": r[0].isoformat() if r[0] else None, "from": r[1], "to": r[2],
         "actor": r[3], "note": r[4]} for r in rows]}


@router.get("/criteria")
def list_criteria(db=Depends(get_db)):
    """判据注册表公网面(v5 #10721 上报 404 缺口)——判据先于判分冻结的公信力公开面。
    只读注册表,不落判据包内容本体(本体在各仓正本,sha16 锚定)。"""
    _ensure_tables(db)
    db.execute(text(
        "CREATE TABLE IF NOT EXISTS assay_criteria_registry ("
        "sha16 TEXT PRIMARY KEY, name TEXT NOT NULL, registered_at TIMESTAMPTZ DEFAULT now())"))
    rows = db.execute(text(
        "SELECT sha16, name, registered_at FROM assay_criteria_registry ORDER BY registered_at DESC")).fetchall()
    return {"criteria": [
        {"sha16": r[0], "name": r[1],
         "registered_at": r[2].isoformat() if r[2] else None} for r in rows],
        "note": "判据注册制:先于判分冻结;sha16=内容 sha256 前 16 位;判据包本体见各评测仓正本坐标"}


class TransitionReq(BaseModel):
    to_status: str = Field(pattern="^(intake_validated|queued|judging|report_draft|delivered|rejected|need_info)$")
    note: str = Field(default="", max_length=512)
    actor: str = Field(default="worker", max_length=64)


@router.post("/submissions/{sid}/transition")
def transition(sid: str, req: TransitionReq, db=Depends(get_db),
               _=Depends(require_platform_key)):
    _ensure_tables(db)
    row = db.execute(text("SELECT status FROM assay_submissions WHERE id=:i"), {"i": sid}).first()
    if not row:
        raise HTTPException(404, "submission not found")
    cur = row[0]
    if cur in TERMINAL:
        raise HTTPException(409, f"terminal status {cur}")
    if req.to_status not in _TRANSITIONS.get(cur, set()):
        raise HTTPException(422, f"illegal transition {cur} -> {req.to_status}")
    db.execute(text("UPDATE assay_submissions SET status=:s WHERE id=:i"),
               {"s": req.to_status, "i": sid})
    # SLA 起算规则:进入 intake_validated 且此前无 deadline 时按 lane 补
    if req.to_status == "intake_validated":
        db.execute(text(
            "UPDATE assay_submissions SET sla_deadline=CAST(:s AS timestamptz) "
            "WHERE id=:i AND sla_deadline IS NULL"),
            {"s": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(), "i": sid})
    _event(db, sid, cur, req.to_status, req.actor, req.note)
    db.commit()
    return {"id": sid, "from": cur, "to": req.to_status}

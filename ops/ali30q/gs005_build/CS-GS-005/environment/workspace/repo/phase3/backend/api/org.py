"""Org OS P0 · mailbox:跨框函件必达(org/bootstrap 设计 §3)。

- POST /api/platform/org/mailbox          投递(幂等 trace_id+to;必带 deadline)
- GET  /api/platform/org/mailbox?to=X     收件(to 可选 unread=1 默认只看未读)
- POST /api/platform/org/mailbox/{id}/ack 回执(幂等)
- POST /api/platform/org/task             发组织任务(五件套强制,§⓪-E 派单)
- GET  /api/platform/org/tasks            任务清单(task_meta 非空)
"""
from __future__ import annotations

import json
import os
import re
from datetime import timedelta, datetime, date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from models.fde_dispatch import FdeDispatch
from models.org_mailbox import OrgMailbox
from models.platform_audit import PlatformAudit
from models.database import APIKey
from utils.database import get_db
from sqlalchemy import text as _text

router = APIRouter(prefix="/api/platform/org", tags=["Org OS"])

_REQUIRED = ("from_agent", "to_agent", "trace_id", "title", "deadline")
_TASK_REQUIRED = ("task_type", "acceptance", "deliverable_format", "consumer")


def _auth_check(db, request: Request, from_agent: str):
    """投函身份鉴权(9/17 上线,预告函 306-309)。

    key 命名约定 name="org-auth:<frame>":key 与 from_agent 绑定。
    宽限期(ORG_AUTH_GRACE 缺省 true):无 key 警告放行(72h 迁移窗口);
    有 key 但 from 不匹配 = 误用,立即 401(与迁移无关,不宽限)。"""
    key = request.headers.get("X-API-Key", "")
    if not key:
        if os.environ.get("ORG_AUTH_GRACE", "true").lower() != "false":
            print(f"ORG-AUTH grace-warning: no X-API-Key from={from_agent}", flush=True)
            return None
        return _err("missing X-API-Key (grace period ended)", status=401)
    row = db.query(APIKey).filter_by(key=key, is_active=True).first()
    if row is None or not str(row.name or "").startswith("org-auth:"):
        return _err("invalid X-API-Key", status=401)
    bound = str(row.name).split(":", 1)[1]
    if bound != from_agent:
        return _err(f"X-API-Key bound to '{bound}', from_agent claims '{from_agent}'", status=401)
    row.last_used_at = datetime.now()
    db.commit()
    return None


def _ok(data, status=200):
    return {"success": True, "data": data, "error": None} if status == 200 else \
        JSONResponse(status_code=status, content={"success": True, "data": data, "error": None})


def _err(msg, status=400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


def _parse_deadline(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


# 收件方白名单(2026-09-29 b-mailbox-schema 判据配套)——六框+两V5体+kairos+platform
_ORG_MAILBOX_WHITELIST = {
    "platform", "v5", "flywheel", "compass", "soul", "vc_daily", "zenmind",
    "kairos", "nautilus-prime-001", "ag_local_laptop_001",
    "v7", "v7-telegram",  # 2026-10-04 用户批A:生产场开放,v7入列(#2557 P0 断点根除)
    "openclaw",  # 2026-10-18 用户批:Mac mini/openclaw 接入线(compass 11430 催办配套)
}


@router.post("/mailbox")
def post_mail(body: dict, request: Request, db=Depends(get_db)):
    missing = [k for k in _REQUIRED if body.get(k) in (None, "")]
    if missing:
        return _err(f"missing required field(s): {', '.join(missing)}")
    to_a = str(body.get("to_agent", "")).strip()
    if to_a and to_a not in _ORG_MAILBOX_WHITELIST:
        return _err(f"recipient '{to_a}' not in org mailbox whitelist", status=400)
    denied = _auth_check(db, request, str(body["from_agent"]))
    if denied is not None:
        return denied
    deadline = _parse_deadline(body["deadline"])
    if deadline is None:
        return _err("deadline must be ISO8601")
    existing = (db.query(OrgMailbox)
                .filter_by(trace_id=str(body["trace_id"]), to_agent=str(body["to_agent"]))
                .first())
    if existing is not None:
        # 9/17 假绿修复(compass 349 反馈):重复 (to,trace) 显式 409+existing_id,
        # 不再静默返回旧函——静默假绿曾让投函方误判已达、收件方从未收到。
        return JSONResponse(status_code=409, content={
            "success": False, "data": {"existing_id": existing.id},
            "error": f"duplicate (to_agent,trace_id); existing id={existing.id}"})
    # 账本身份守卫(9/16):平台自身发函走 DB 直写不走本端点;此处收到
    # from=platform 即外部误标(9/16 实证:飞轮回函被记成 platform)。
    # 不断流(链在推进),打警告留痕,协议修正函告各框。
    if str(body["from_agent"]) == "platform":
        print(f"ORG-MAIL identity-warning: external post claims from=platform"
              f" trace={str(body['trace_id'])[:60]}", flush=True)
    row = OrgMailbox(from_agent=str(body["from_agent"]), to_agent=str(body["to_agent"]),
                     trace_id=str(body["trace_id"]), title=str(body["title"])[:256],
                     body=str(body.get("body", "")), deadline=deadline,
                     created_at=datetime.now())  # 服务端兜底(9/16:回函 created_at=None 缺口)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _ok(row.to_dict())


@router.get("/mailbox")
def list_mail(to: str | None = None, unread: bool = True, db=Depends(get_db)):
    q = db.query(OrgMailbox)
    if to:
        q = q.filter_by(to_agent=to)
    if unread:
        q = q.filter(OrgMailbox.ack_at.is_(None))
    rows = q.order_by(OrgMailbox.deadline.asc()).all()
    return _ok([r.to_dict() for r in rows])


@router.post("/mailbox/{mid}/ack")
def ack_mail(mid: int, body: dict | None = None, db=Depends(get_db)):
    row = db.get(OrgMailbox, mid)
    if row is None:
        return _err("mail not found", status=404)
    if row.ack_at is not None:  # idempotent re-ack
        data = row.to_dict()
        data["idempotent"] = True
        return _ok(data)
    # 时钟列纪律(9/25 实证):本表 created_at/deadline=上海 naive(宿主 now()),
    # ack_at 曾用 utcnow() 混钟——全组织 ack 落库值比列语义早 8h,SLA/EXPIRED
    # 审计按列读即冤 8h(#1007 误诊 v5 写入侧,二次勘误 #1012 撤回,病根在本行)。
    row.ack_at = datetime.now()
    if body:
        row.ack_note = str(body.get("note", ""))[:512]
    db.commit()
    db.refresh(row)
    return _ok(row.to_dict())


@router.post("/task")
def post_task(body: dict, request: Request, db=Depends(get_db)):
    """发组织任务(§⓪-E 派单五件套强制:类型/验收判据/交付格式/SLA/消费者)。

    任务=带 task_meta 的函,同走 mailbox 总线(SLA 执法/回函核销/日报全复用);
    验收判据渲染进 body 头部,读函即见,不依赖 JSON 列。
    """
    missing = [k for k in _REQUIRED + _TASK_REQUIRED if body.get(k) in (None, "")]
    if missing:
        return _err(f"missing required field(s): {', '.join(missing)}")
    denied = _auth_check(db, request, str(body["from_agent"]))
    if denied is not None:
        return denied
    deadline = _parse_deadline(body["deadline"])
    if deadline is None:
        return _err("deadline must be ISO8601")
    existing = (db.query(OrgMailbox)
                .filter_by(trace_id=str(body["trace_id"]), to_agent=str(body["to_agent"]))
                .first())
    if existing is not None:  # duplicate → 显式 409(同 post_mail,假绿修复)
        return JSONResponse(status_code=409, content={
            "success": False, "data": {"existing_id": existing.id},
            "error": f"duplicate (to_agent,trace_id); existing id={existing.id}"})
    meta = {k: str(body[k]) for k in _TASK_REQUIRED}
    head = (f"[任务单 {meta['task_type']}] 验收判据: {meta['acceptance']}\n"
            f"交付格式: {meta['deliverable_format']} · 消费者: {meta['consumer']}")
    row = OrgMailbox(from_agent=str(body["from_agent"]), to_agent=str(body["to_agent"]),
                     trace_id=str(body["trace_id"]), title=str(body["title"])[:256],
                     body=head + "\n\n" + str(body.get("body", "")), deadline=deadline,
                     task_meta=meta, created_at=datetime.now())  # 同上兜底
    db.add(row)
    db.commit()
    db.refresh(row)
    return _ok(row.to_dict())


@router.get("/tasks")
def list_tasks(db=Depends(get_db)):
    """任务清单(task_meta 非空;普通函不混入)。"""
    rows = (db.query(OrgMailbox)
            .filter(OrgMailbox.task_meta.isnot(None))
            .order_by(OrgMailbox.deadline.asc()).all())
    return _ok([r.to_dict() for r in rows])


def _client_ip(request: Request) -> str | None:
    """nginx 反代后 request.client=127.0.0.1;X-Real-IP 由 nginx $remote_addr 覆盖式设置,
    客户端直发该头会被 nginx 盖掉(见 ops/nginx/nautilus.conf),可信。"""
    host = request.client.host if request.client else None
    if host in ("127.0.0.1", "::1"):
        return request.headers.get("X-Real-IP") or host
    return host


@router.post("/audit")
def post_audit(body: dict, request: Request, db=Depends(get_db)):
    """T1-A3 · audit 写入端点——daemon 活性平台直接可观测(治 #779 双库分裂:
    真干活的主脑 cloud audit 0 行,观测面与实干面分离)。

    鉴权:X-API-Key org-auth:<actor> 绑定(同 mailbox 配方,key 冒名即 401);
    ts/ip 服务端记;preview 截 2000;事件流语义不幂等(重试重复调用方自担)。
    """
    if not isinstance(body, dict):
        return _err("body must be a JSON object")
    missing = [k for k in ("actor", "action", "outcome") if not body.get(k)]
    if missing:
        return _err(f"missing required field(s): {', '.join(missing)}")
    denied = _auth_check(db, request, str(body["actor"]))
    if denied is not None:
        return denied
    meta = body.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        return _err("metadata must be a JSON object")
    row = PlatformAudit(
        ts=datetime.now(),                       # 服务端时钟(模型列 timezone=True,PG 落 timestamptz)
        # 缺省对齐生产 NOT NULL 约束(9/23 NotNullViolation 修正):metadata→{}、
        # actor_type→unspecified、target/target_type→'';长度按生产列宽截
        actor=str(body["actor"])[:128],
        actor_type=str(body.get("actor_type") or "unspecified")[:32],
        action=str(body["action"])[:128],
        target=str(body.get("target") or "")[:256],
        target_type=str(body.get("target_type") or "")[:32],
        outcome=str(body["outcome"])[:16],
        input_preview=(str(body.get("input_preview") or "") or None) and str(body.get("input_preview"))[:2000],
        output_preview=(str(body.get("output_preview") or "") or None) and str(body.get("output_preview"))[:2000],
        meta=meta or {},
        ip=str(_client_ip(request) or "unknown")[:64])
    db.add(row)
    db.commit()
    db.refresh(row)
    return _ok(row.to_dict())


@router.get("/audit")
def get_audit_liveness(actor: str | None = None, hours: int = 24, limit: int = 50,
                       db=Depends(get_db)):
    """T1-A3 · 活性读数(值守统一读侧):只回 actor/ts/action/target/outcome 计数与最近行,
    不含 preview/metadata(活性语义不曝内容)。无鉴权只读,同 mailbox GET 先例。"""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(hours=max(1, min(hours, 24 * 30)))
    q = db.query(PlatformAudit).filter(PlatformAudit.ts >= cutoff)
    if actor:
        q = q.filter_by(actor=actor)
    total = q.count()
    rows = q.order_by(PlatformAudit.id.desc()).limit(max(1, min(limit, 200))).all()
    return _ok({"actor": actor, "hours": hours, "total": total,
                "rows": [{"ts": str(r.ts), "actor": r.actor, "action": r.action,
                          "target": r.target, "outcome": r.outcome} for r in rows]})


@router.get("/delivery-clock")
def delivery_clock(window_h: int = 48, db=Depends(get_db)):
    """A2-P1 · 平台侧交付时钟矩阵(561 平台半边第二件):值守看板从进程列表换成交付矩阵。

    三源各自带时区基准(dispatch=utcnow 写 / audit=timestamptz / mail=上海 naive),
    输出统一 h_ago;WARN=超窗 2/3·RED=超窗(默认 48h)。RED 处置走断供处置线
    (协议 V1 §5),**不自动改 agent 数据**——561"自动 parking"降格为亮牌+日报告警,
    框级生死=用户主权(GOAL_STACK 四纪律①)。verdict 源不单列(经 dispatch settled
    链路可见,判分归判分方域);git 源在 frame_snapshot(不进 DB 矩阵)。
    """
    from datetime import timedelta, timezone as _tz
    from sqlalchemy import func
    window = max(1, min(window_h, 24 * 30))
    agents: dict = {}

    def _put(agent, src, dt, now_ref):
        if agent is None or dt is None:
            return
        h = round((now_ref - dt).total_seconds() / 3600, 1)
        d = agents.setdefault(str(agent), {})
        if src not in d or h < d[src]:
            d[src] = h

    now_utc, now_sh = datetime.utcnow(), datetime.now()
    for a, t in db.query(FdeDispatch.claimed_by, func.max(FdeDispatch.reported_at)) \
                  .filter(FdeDispatch.reported_at.isnot(None)).group_by(FdeDispatch.claimed_by):
        _put(a, "dispatch_h_ago", t, now_utc)
    for a, t in db.query(PlatformAudit.actor, func.max(PlatformAudit.ts)).group_by(PlatformAudit.actor):
        if t is not None and t.tzinfo is not None:      # timestamptz → utc naive
            t = t.astimezone(_tz.utc).replace(tzinfo=None)
        _put(a, "audit_h_ago", t, now_utc)
    for a, t in db.query(OrgMailbox.from_agent, func.max(OrgMailbox.created_at)) \
                  .group_by(OrgMailbox.from_agent):
        _put(a, "mail_h_ago", t, now_sh)                # mailbox 列=上海 naive

    rows = []
    for a, srcs in agents.items():
        best = min(srcs.values())
        status = "RED" if best > window else ("WARN" if best > window * 2 / 3 else "GREEN")
        rows.append({"agent": a, "sources": srcs, "best_h_ago": best, "status": status})
    rows.sort(key=lambda x: -x["best_h_ago"])
    return _ok({"window_h": window, "agents": rows,
                "red": [r["agent"] for r in rows if r["status"] == "RED"]})


@router.get("/bootstrap")
def bootstrap(agent: str, db=Depends(get_db)):
    """org/bootstrap P1 · 一次调用治 session 开局(设计 §2 七节包,contracts 节 P2)。"""
    from datetime import timedelta
    from pathlib import Path

    pack: dict = {"agent": agent, "generated_at": datetime.utcnow().isoformat()}

    # identity:按 agent_id 或 name 模糊匹配
    ident = None
    try:
        from models.database import Agent
        q = db.query(Agent)
        row = (q.filter(Agent.agent_id == int(agent)).first()
               if agent.isdigit() else
               q.filter(Agent.name.ilike(f"%{agent}%")).first())
        if row is not None:
            ident = {"agent_id": row.agent_id, "name": row.name,
                     "reputation": row.reputation, "total_earnings": row.total_earnings}
    except Exception as exc:  # noqa: BLE001
        ident = {"err": str(exc)[:80]}
    pack["identity"] = ident

    # state:SSOT canonical 指纹(云仓根文件)
    try:
        import hashlib
        ssot = Path(__file__).resolve().parents[3] / "LOOP_STATE_SSOT.md"
        pack["state"] = {"file": "LOOP_STATE_SSOT.md",
                         "sha1": hashlib.sha1(ssot.read_bytes()).hexdigest()[:12] if ssot.exists() else None,
                         "source": "origin/soul-distill-deploy(与各框副本比对)"}
    except Exception as exc:  # noqa: BLE001
        pack["state"] = {"err": str(exc)[:80]}

    # mailbox:未读(deadline 升序)+12h 内到期计数(牙齿联动)
    try:
        now = datetime.utcnow()
        unread = (db.query(OrgMailbox)
                  .filter_by(to_agent=agent, ack_at=None)
                  .order_by(OrgMailbox.deadline.asc()).all())
        pack["mailbox"] = {"unread": [r.to_dict() for r in unread],
                           "due_12h": sum(1 for r in unread if r.deadline <= now + timedelta(hours=12))}
    except Exception as exc:  # noqa: BLE001
        pack["mailbox"] = {"err": str(exc)[:80]}

    pack["contracts"] = []  # P2:frontmatter 扫描接入
    pack["goals"] = {"file": "docs/GOAL_STACK.md",
                     "note": "loop 唯一目标源;台阶层见文件头"}
    pack["memory"] = {"recall": "compass MCP recall(project=本框)", "note": "记忆本体在 compass,此处只指路"}
    pack["capability_index"] = {"file": "docs/ASSET_LEDGER_20260828.md",
                                "note": "§⓪-E:先查再造;消费者/消费计数列"}

    # health:最小外部读数
    try:
        from sqlalchemy import text as _text
        v = db.execute(_text("SELECT count(*) FROM fde_verdicts WHERE external_verified")).scalar()
        pack["health"] = {"verified_total": int(v or 0)}
    except Exception as exc:  # noqa: BLE001
        pack["health"] = {"err": str(exc)[:80]}
    return _ok(pack)


# ── 四件套固化(2026-09-28 用户批·不新造接线) ───────────────────────
# ②踩坑登记表(免疫册技术陷阱类 DB 化)+④Assay 计量单 v0
# 表在首次调用时 IF NOT EXISTS 建立;登记/检索/回执三组端点。

_DEF_SQL = [
    """CREATE TABLE IF NOT EXISTS org_pitfalls (
        id SERIAL PRIMARY KEY,
        agent VARCHAR(64) NOT NULL,
        category VARCHAR(32) NOT NULL DEFAULT 'tech',
        symptom TEXT NOT NULL,
        root_cause TEXT,
        fix_ref TEXT,
        registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    "CREATE INDEX IF NOT EXISTS org_pitfalls_kw_idx ON org_pitfalls USING gin (to_tsvector('simple', symptom || ' ' || coalesce(root_cause,'')))",
    """CREATE TABLE IF NOT EXISTS assay_meter_records (
        id SERIAL PRIMARY KEY,
        agent VARCHAR(64) NOT NULL,
        target_object VARCHAR(200) NOT NULL,
        judge_version VARCHAR(64) NOT NULL,
        reading_hash VARCHAR(128) NOT NULL,
        category VARCHAR(32) NOT NULL DEFAULT 'assay_certificate',
        note TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
]


def _ensure_tables(db) -> None:
    for stmt in _DEF_SQL:
        db.execute(_text(stmt))
    db.commit()


@router.post("/pitfalls")
async def register_pitfall(body: dict, request: Request, db=Depends(get_db)):
    """踩坑登记(免疫册·技术陷阱类)。一框踩坑,全组织可检索继承。"""
    denied = _auth_check(db, request, str(body.get("agent", "")))  # 2026-10-11 收口⑥(施工单 ORG_AUTH_ROLLOUT)
    if denied:
        return denied
    agent, symptom = body.get("agent", ""), body.get("symptom", "")
    if not agent or not symptom:
        return JSONResponse({"success": False, "error": "agent/symptom required"}, 400)
    _ensure_tables(db)
    db.execute(_text(
        "INSERT INTO org_pitfalls (agent, category, symptom, root_cause, fix_ref) "
        "VALUES (:a, :c, :s, :r, :f)"
    ), {"a": agent[:64], "c": body.get("category", "tech")[:32],
        "s": symptom[:2000], "r": (body.get("root_cause") or "")[:2000],
        "f": (body.get("fix_ref") or "")[:500]})
    db.commit()
    row = db.execute(_text("SELECT max(id) FROM org_pitfalls")).scalar()
    return _ok({"id": row, "registered": True})


@router.get("/pitfalls")
async def search_pitfalls(kw: str = "", db=Depends(get_db)):
    """跨框踩坑检索(GEP 继承面:一个 agent 学会,千万个 agent 查到)。"""
    _ensure_tables(db)
    q = "SELECT id, agent, category, symptom, root_cause, fix_ref, registered_at FROM org_pitfalls"
    if kw:
        q += " WHERE symptom ILIKE :kw OR root_cause ILIKE :kw"
        rows = db.execute(_text(q), {"kw": f"%{kw}%"}).mappings().all()
    else:
        rows = db.execute(_text(q + " ORDER BY id DESC LIMIT 50")).mappings().all()
    return _ok([{k: str(v) for k, v in r.items()} for r in rows])


class _ClaimReq(BaseModel):
    bounty_id: str
    name: str
    contact: str
    note: str = ""


@router.post("/dispatch/claim_request")
async def dispatch_claim_request(req: _ClaimReq, request: Request, db=Depends(get_db)):
    """外部人类接单申请(2026-09-29 · 无鉴权+限流:任务页提交口)。

    仅收四字段落 org_mailbox(to=platform),不触碰金库/claim——防滥用面最小。
    """
    if not req.bounty_id.startswith("b-human") or len(req.name) > 60 or len(req.contact) > 120:
        return _err("invalid claim request", status=400)
    # 2026-10-11 收口②:对外口不装门(v5 #10874 表态同意),from_agent 硬编码 "v5" 改
    # 固定标签 "task-page" 消冒名歧义;trace 的 human-claim 形态保留(榜单 left(id,8) 读取面不破坏)。
    row = OrgMailbox(from_agent="task-page", to_agent="platform",
                     trace_id=f"human-claim-{req.bounty_id}-{int(datetime.now().timestamp())}",
                     title=f"[外部接单申请] {req.bounty_id[:64]} · {req.name[:40]}",
                     body=("外部人类申请接单 | 任务:{b} | 称呼:{n} | "
                           "联系:{c} | 说明:{s}").format(
                               b=req.bounty_id, n=req.name, c=req.contact,
                               s=req.note or "无"),
                     deadline=datetime.now() + timedelta(hours=24))
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": {"id": row.id}}


class _WritebackReq(BaseModel):
    agent_id: str
    judge_type: str
    items: list


@router.post("/judge/writeback")
async def judge_writeback(req: _WritebackReq, request: Request, db=Depends(get_db)):
    """W42 判分结果写回端点(2026-10-01 · flywheel #1748 404 根修 · backprop 环数据格)。

    判分器(judge/soul/外部)将结果批量写回,入库 org_mailbox 供消费方取。
    """
    from sqlalchemy import text as _t3
    if not req.agent_id or not req.items:
        return _err("agent_id and items required", status=400)
    # 鉴权门(2026-10-03 外网零鉴权实测洞):云端设 WRITEBACK_KEY 即强制
    # X-Writeback-Key 头;未设=宽限模式放行(调用方 48h 接线期,日志记 warn)。
    _wb_key = os.environ.get("WRITEBACK_KEY")
    if _wb_key:
        import hmac as _hmac
        if not _hmac.compare_digest(request.headers.get("X-Writeback-Key", ""), _wb_key):
            return _err("writeback key required", status=401)
    else:
        import logging as _log
        _log.getLogger("org.writeback").warning("writeback grace mode: WRITEBACK_KEY unset")
    denied = _auth_check(db, request, str(req.agent_id))  # 2026-10-11 收口①(org-auth 绑定,叠加 WRITEBACK_KEY 门)
    if denied:
        return denied
    # 场分离变更门(U34·场分离终裁后的物理强制件):judge_type 带 lab:* 前缀 =
    # 实验场产物——只入实验池(mailbox title 加 [lab] 前缀),禁直灌生产消费面。
    is_lab = str(req.judge_type or '').startswith('lab:')
    if is_lab:
        req.judge_type = req.judge_type[4:]  # 剥前缀,入库标记在 title
    inserted = 0
    skipped = 0
    for it in req.items:
        if not isinstance(it, dict) or not it.get("id"):
            skipped += 1  # flywheel 10/3 假绿根修:静默跳过改显式计数,全缺 id 拒收
            continue
        db.add(OrgMailbox(
            from_agent=req.agent_id,
            to_agent="platform",
            trace_id=f"writeback:{req.judge_type}:{it['id']}",
            title = ("[lab·" + req.judge_type + "] " if is_lab else "[writeback:" + req.judge_type + "] ") + str(it.get("label", ""))[:40],
            body=str(it),
            deadline=datetime.now() + timedelta(hours=48),
        ))
        inserted += 1
    if inserted == 0:
        db.rollback()
        return _err(
            f"all {skipped} items skipped: each item must be an object with an 'id' field",
            status=422)
    db.commit()
    return {"success": True, "data": {"inserted": inserted, "skipped": skipped, "judge_type": req.judge_type}}


class _FrameDeclareReq(BaseModel):
    frame: str
    mainline: str
    criteria: str
    reach: str
    cadence: str
    plane: str = "prod"


@router.post("/frames/declare")
async def frames_declare(req: _FrameDeclareReq, request: Request, db=Depends(get_db)):
    """框卡声明通道(2026-10-04 · 裁决分级清单配套件)——框按 org_frames.v1 schema
    机器可读提交主线/判据/触达/时效,落 org_mailbox(frames_declare: 前缀)。

    声明不直写 registry 文件:git 单主干纪律+生产工作树 clean(部署纪律铁律 2),
    由平台/loop 值守审核合并(git 通道),审核=公共品面(框卡是组织公共面,防漂移)。
    鉴权沿 judge/writeback 宽限门同款(X-Writeback-Key,未设 key=宽限放行+warn)。
    """
    if not req.frame:
        return _err("frame required", status=400)
    _wb_key = os.environ.get("WRITEBACK_KEY")
    if _wb_key:
        import hmac as _hmac
        if not _hmac.compare_digest(request.headers.get("X-Writeback-Key", ""), _wb_key):
            return _err("writeback key required", status=401)
    else:
        import logging as _log
        _log.getLogger("org.frames_declare").warning("frames_declare grace mode: WRITEBACK_KEY unset")
    denied = _auth_check(db, request, str(req.frame))  # 2026-10-11 收口③(frame 白名单保留于下方 _known 校验)
    if denied:
        return denied
    _known = {f["frame"] for f in _load_frames_registry()["frames"]}
    if req.frame not in _known:
        return _err(f"unknown frame: {req.frame} (in-registry frames only)", status=400)
    for _k in ("mainline", "criteria", "reach", "cadence"):
        _v = str(getattr(req, _k) or "").strip()
        if not _v:
            return _err(f"field required: {_k}", status=400)
        if len(_v) > 300:
            return _err(f"field too long: {_k} (max 300)", status=400)
    db.add(OrgMailbox(
        from_agent=req.frame,
        to_agent="platform",
        trace_id=f"frames_declare:{req.frame}:{int(datetime.now().timestamp())}",
        title=f"[框卡声明] {req.frame} 主线/判据/触达/时效·待平台审核合并 registry",
        body=json.dumps(req.model_dump(), ensure_ascii=False),
        deadline=datetime.now() + timedelta(hours=48),
    ))
    db.commit()
    return {"success": True, "data": {"frame": req.frame, "status": "queued_for_review"}}


class _SkillRepReq(BaseModel):
    slug: str
    total_hires: int
    avg_rating: float
    success_rate: float


@router.post("/skills/reputation")
async def skill_reputation_writeback(req: _SkillRepReq, request: Request, db=Depends(get_db)):
    """技能信誉回写(2026-10-04 · 信誉飞轮配套,v5 #2626 请):交付数据回写 agent_skills
    三字段,全量快照式幂等。行不存在 404(上架走平台审核通道,不自动建行)。
    鉴权沿 writeback 宽限门同款。
    """
    from sqlalchemy import text as _t4
    _wb_key = os.environ.get("WRITEBACK_KEY")
    if _wb_key:
        import hmac as _hmac
        if not _hmac.compare_digest(request.headers.get("X-Writeback-Key", ""), _wb_key):
            return _err("writeback key required", status=401)
    denied = _auth_check(db, request, "v5")  # 2026-10-11 收口④(任意赋值堵死;v5 #10874 拍 B 案:限 org-auth:v5)
    if denied:
        return denied
    if not req.slug or req.total_hires < 0 or not (0 <= req.avg_rating <= 5) or not (0 <= req.success_rate <= 1):
        return _err("invalid values (total_hires>=0, 0<=avg_rating<=5, 0<=success_rate<=1)", status=400)
    n = db.execute(_t4(
        "UPDATE agent_skills SET total_hires=:h, avg_rating=:r, success_rate=:s, updated_at=now() "
        "WHERE slug=:slug"
    ), {"h": req.total_hires, "r": req.avg_rating, "s": req.success_rate, "slug": req.slug}).rowcount
    if not n:
        db.rollback()
        return _err(f"unknown skill slug: {req.slug}", status=404)
    db.commit()
    return {"success": True, "data": {"slug": req.slug, "total_hires": req.total_hires,
                                       "avg_rating": req.avg_rating, "success_rate": req.success_rate}}


_HEX16 = re.compile(r"[0-9a-f]{16}")  # 入册闸(2026-10-04 用户批):live 件 sha16 必须 16 位 hex


def _sediment_effective(row: dict, today: date) -> dict:
    """活性读数态(v2 2026-10-05 用户批·组合制):不改正本字段,只附 effective_status/liveness_note。
    v1(2026-10-04):入册闸(live 件 sha16 必须 16 位 hex)+expires(verified_at+expires_days<today 待复验)。
    v2 增:live = 复验通过 AND ≥1 注册消费方(consumers,硬条件);复验通过但无消费方 →
    unclaimed(待认领,不降级不摘牌)。permanent_type(protocol/criteria/casebook)=永久件例外,
    豁免程序性死亡(60 天无复验无消费方摘牌),expires 复验义务不豁免。访问量/跨框引用=软信号
    不参与生死(三框一致)。摘牌仅两路径:锚失配/程序性死亡(ops/sinks_review_scan.py)。"""
    if row.get("status") != "live":
        return row
    sha = row.get("sha16")
    bad_sha = not (sha and _HEX16.fullmatch(str(sha)))
    expired = False
    v_at, exp_days = row.get("verified_at"), row.get("expires_days")
    if v_at and exp_days:
        try:
            y, m, d = (int(x) for x in str(v_at).split("-"))
            expired = date(y, m, d) + timedelta(days=int(exp_days)) < today
        except Exception:  # noqa: BLE001  日期坏=无法证明新鲜,视同过期
            expired = True
    if bad_sha or expired:
        note = ("sha16 格式违规,入册闸拦截" if bad_sha
                else f"verified_at {v_at}+{exp_days}d 已过期,回执新 sha 续验")
        return {**row, "effective_status": "planned", "liveness_note": note}
    if not row.get("consumers"):  # v2 组合制:硬门过、无注册消费方 → 待认领
        return {**row, "effective_status": "unclaimed",
                "liveness_note": "复验通过但无注册消费方(v2 组合制:待认领,不降级)"}
    return row


def _load_json_registry(name: str) -> dict:
    """registry JSON 通用载入(trainings/benchmarks 沉淀台账,SEDDIMENT_SURFACE_FOUNDATION_V1)。
    文件缺失抛 FileNotFoundError(由端点 fail-soft 兜底)。"""
    import json as _json
    from pathlib import Path as _Path
    _f = _Path(__file__).resolve().parents[1] / "registry" / f"{name}.json"
    return _json.loads(_f.read_text(encoding="utf-8"))


def _sediment_endpoint(name: str, limit: int = 50):
    async def _impl():
        try:
            reg = _load_json_registry(name)
            rows = reg.get(name, [])[-limit:]
            rows = [_sediment_effective(r, date.today()) for r in rows]
        except FileNotFoundError:
            rows = []  # 台账未建=预期态(提案定稿前),fail-soft 非病
        except Exception:  # noqa: BLE001  已建但读坏=病,必须亮灯(posts 静默吞教训
            import logging as _log
            _log.getLogger(f"org.{name}").warning(f"{name} registry 读取异常", exc_info=True)
            rows = []
        return {"success": True, "data": rows, "meta": {"count": len(rows), "schema": reg.get("schema", f"{name}.v1")}}
    _impl.__name__ = f"org_{name}"
    _impl.__doc__ = f"{name} 沉淀台账(org_state 扩展,registry JSON,提案定稿后填充)。"
    return _impl


org_trainings = router.get("/trainings")(_sediment_endpoint("trainings"))
org_benchmarks = router.get("/benchmarks")(_sediment_endpoint("benchmarks"))
org_sinks = router.get("/sinks")(_sediment_endpoint("sinks"))  # 沉淀物注册表(2026-10-04 提前开工·compass #2797 三件占位+v5 TSI 锚定)
org_judging_pipelines = router.get("/judging-pipelines")(_sediment_endpoint("judging_pipelines"))  # 判读管线台账(compass #2871 方式②代合并)
org_memory_io = router.get("/memory-io")(_sediment_endpoint("memory_io"))  # 记忆IO台账(compass #2871 方式②代合并)


class _BenchBackfillReq(BaseModel):
    """判据回填请求(_custodian 自助,L1 闭环固化件)。"""
    benchmark_id: str
    criteria_version: str
    preregistered_hash: str
    evidence_repo: str      # 例 chunxiaoxx/nautilus-compass
    evidence_path: str      # 例 docs/metering/L1_CRITERIA_FREEZE_NOTES_20261005.md
    evidence_sha16: str     # 冻结档 sha256 前 16 位
    reporter: str           # 提交框(须=该行 custodian,判据主权)
    trace_id: str
    note: str = ""


@router.post("/benchmarks/backfill")
async def benchmarks_backfill(req: _BenchBackfillReq, request: Request, db=Depends(get_db)):
    """判据回填自助通道(2026-10-05 · 北极星 L1 闭环固化沉淀,用户批"先推动实现")。

    机制化此前平台 session 手工流程(compass 交付→平台 curl 复验→人工代写→回执):
    custodian 提交判据值+冻结档坐标,服务端对 GitHub raw 正本独立复验 sha256——
    一致=APPROVED 入值守合并队列(复验证据随函留痕,值守合并零复验);
    不可寻址/sha 不符=REJECTED 挡闸留痕。双函自动落 mailbox(平台留痕+回执提交方)。
    幂等=trace_id;判据主权=仅该行 custodian 可回填;不直写 registry 文件
    (git 单主干+生产工作树 clean,沿 frames_declare 先例,值守经 git 通道合并)。
    鉴权沿 writeback 宽限门同款(WRITEBACK_KEY)。
    """
    import hashlib as _hashlib
    import urllib.request as _ureq
    _wb_key = os.environ.get("WRITEBACK_KEY")
    if _wb_key:
        import hmac as _hmac
        if not _hmac.compare_digest(request.headers.get("X-Writeback-Key", ""), _wb_key):
            return _err("writeback key required", status=401)
    else:
        import logging as _log
        _log.getLogger("org.bench_backfill").warning("benchmarks_backfill grace mode: WRITEBACK_KEY unset")
    denied = _auth_check(db, request, str(req.reporter))  # 2026-10-11 收口⑤(from=custodian 绑定)
    if denied:
        return denied
    _bad = [k for k in ("benchmark_id", "criteria_version", "preregistered_hash",
                        "evidence_repo", "evidence_path", "evidence_sha16", "reporter", "trace_id")
            if not str(getattr(req, k) or "").strip()]
    if _bad:
        return _err(f"field required: {','.join(_bad)}", status=400)
    if (len(req.criteria_version) > 300 or len(req.preregistered_hash) > 300
            or len(req.evidence_repo) > 200 or len(req.evidence_path) > 300 or len(req.note) > 500):
        return _err("field too long (criteria_version/preregistered_hash<=300, repo<=200, path<=300, note<=500)", status=400)
    if not _HEX16.fullmatch(req.evidence_sha16):
        return _err("evidence_sha16 must be 16 hex (入册闸)", status=400)
    try:
        reg = _load_json_registry("benchmarks")
    except Exception:  # noqa: BLE001
        return _err("benchmarks registry unavailable", status=503)
    row = next((b for b in reg.get("benchmarks", []) if b.get("benchmark_id") == req.benchmark_id), None)
    if not row:
        return _err(f"unknown benchmark_id: {req.benchmark_id}", status=404)
    custodian = str(row.get("custodian") or "")
    if custodian and req.reporter != custodian:
        return _err(f"criteria sovereignty: only custodian={custodian} may backfill this row", status=403)
    dup = db.execute(_text("SELECT 1 FROM org_mailbox WHERE trace_id=:t AND to_agent='platform' LIMIT 1"),
                     {"t": f"bench_backfill:{req.trace_id}"}).scalar()
    if dup:
        return {"success": True, "data": {"verdict": "DUPLICATE_SKIPPED", "trace_id": req.trace_id}}
    # SSRF 收口(2026-10-11 收口⑤附项):repo 段锁 github owner/repo 形态,path 禁 ..
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", req.evidence_repo) or ".." in req.evidence_path:
        return _err("evidence_repo/path violates allowlist (github raw only)", status=400)
    raw_url = f"https://raw.githubusercontent.com/{req.evidence_repo}/main/{req.evidence_path}"
    try:
        with _ureq.urlopen(raw_url, timeout=25) as _resp:
            _bytes = _resp.read()
    except Exception as _exc:  # noqa: BLE001
        _verdict, _detail = "REJECTED", f"evidence unreachable: {raw_url} ({type(_exc).__name__})"
    else:
        _actual = _hashlib.sha256(_bytes).hexdigest()[:16]
        if _actual == req.evidence_sha16:
            _verdict = "APPROVED"
            _detail = f"raw {len(_bytes)}B sha16={_actual} 复验一致"
        else:
            _verdict = "REJECTED"
            _detail = f"sha mismatch: claimed={req.evidence_sha16} actual={_actual} ({len(_bytes)}B)"
    _merge = {"benchmark_id": req.benchmark_id,
              "set": {"criteria_version": req.criteria_version,
                      "preregistered_hash": req.preregistered_hash,
                      "status": "live"},
              "note": req.note}
    db.add(OrgMailbox(
        from_agent=req.reporter, to_agent="platform",
        trace_id=f"bench_backfill:{req.trace_id}",
        title=f"[判据回填·{_verdict}] {req.benchmark_id} ← {req.reporter}",
        body=json.dumps({"verdict": _verdict, "detail": _detail, "merge": _merge,
                         "evidence": {"repo": req.evidence_repo, "path": req.evidence_path,
                                      "sha16": req.evidence_sha16}, "note": req.note},
                        ensure_ascii=False),
        deadline=datetime.now() + timedelta(hours=48),
    ))
    _next_step = ("已入值守合并队列(合并值=criteria_version/preregistered_hash 如提交,status=live),平台合并后端点即生效"
                  if _verdict == "APPROVED"
                  else "未入合并队列(挡闸留痕),请核坐标或 sha 后重新提交")
    db.add(OrgMailbox(
        from_agent="platform", to_agent=req.reporter,
        trace_id=f"bench_backfill_receipt:{req.trace_id}",
        title=f"[回填回执·{_verdict}] {req.benchmark_id}",
        body=f"{_detail}\n\n{_next_step}\ntrace_id={req.trace_id}",
        deadline=datetime.now() + timedelta(hours=2),
    ))
    db.commit()
    return {"success": True, "data": {"verdict": _verdict, "detail": _detail,
                                      "benchmark_id": req.benchmark_id, "trace_id": req.trace_id}}


@router.get("/dispatch/public")
async def dispatch_public(status: str = "open", task_type: str | None = None, db=Depends(get_db)):
    """市场单公开浏览(2026-09-29 · V2可达性堵点根修,承compass 1609实测)。

    只读+脱敏:任何人(agent/外部人)可见在挂单,无须key——先能"看到单"。
    claim 仍需走鉴权端点(押金+结算不公开)。
    task_type 过滤(2026-10-04 · prime 分流①配合件):?task_type=fuel 按类拉单。
    """
    from sqlalchemy import text as _t2
    _where = "status = :s"
    _params = {"s": status}
    if task_type:
        _where += " AND task_type = :tt"
        _params["tt"] = task_type
    rows = db.execute(_t2(
        "SELECT bounty_id, title, reward_nau, difficulty, task_type, status, "
        f"posted_at::date FROM platform_bounties WHERE {_where} "
        "ORDER BY posted_at DESC LIMIT 50"
    ), _params).mappings().all()
    return _ok([{k: str(v) for k, v in r.items()} for r in rows])


@router.post("/assay/meter")
async def assay_meter(body: dict, db=Depends(get_db)):
    """Assay 计量单 v0:一次验证=一条不可变计量记录(凭证哈希锚定)。"""
    agent, target, jver, rhash = (body.get("agent", ""), body.get("target_object", ""),
                                   body.get("judge_version", ""), body.get("reading_hash", ""))
    if not all([agent, target, jver, rhash]):
        return JSONResponse({"success": False, "error": "agent/target_object/judge_version/reading_hash required"}, 400)
    _ensure_tables(db)
    db.execute(_text(
        "INSERT INTO assay_meter_records (agent, target_object, judge_version, reading_hash, category, note) "
        "VALUES (:a, :t, :j, :r, :c, :n)"
    ), {"a": agent[:64], "t": target[:200], "j": jver[:64], "r": rhash[:128],
        "c": body.get("category", "assay_certificate")[:32], "n": (body.get("note") or "")[:1000]})
    db.commit()
    row = db.execute(_text("SELECT max(id) FROM assay_meter_records")).scalar()
    return _ok({"meter_id": row, "category": body.get("category", "assay_certificate")})


@router.get("/assay/receipt/{rid}")
async def assay_receipt(rid: int, db=Depends(get_db)):
    """签名回执=发票附件:客户可回读凭证(独立验证铁律对外版)。"""
    _ensure_tables(db)
    row = db.execute(_text(
        "SELECT id, agent, target_object, judge_version, reading_hash, category, created_at "
        "FROM assay_meter_records WHERE id = :i"
    ), {"i": rid}).mappings().first()
    if row is None:
        return JSONResponse({"success": False, "error": "not found"}, 404)
    return _ok({k: str(v) for k, v in row.items()})


@router.get("/capability-ledger")
def capability_ledger(
    q: str = Query(default=None, description="关键词过滤(名称/描述)"),
    plane: str = Query(default=None, description="prod/lab/dormant/retired 过滤"),
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db),
):
    """能力账本查询(沉淀复用环·U32 缺口2)——组织的 DNS:查能力→得接口坐标。

    查询即消费:每次调用计数回写(usage_count+1),周报读"账本查询数"=融合度。
    """
    from sqlalchemy import text as _t
    where, params = ["1=1"], {"lim": limit}
    if q:
        where.append("(name ILIKE :q OR description ILIKE :q)")
        params["q"] = f"%{q}%"
    if plane:
        where.append("complexity_level = :pl" if plane == "dormant" else "pattern_type = :pl")
        params["pl"] = plane.upper() if plane != "dormant" else "DORMANT"
    rows = db.execute(_t(
        f"SELECT name, description, pattern_type, complexity_level, created_at "
        f"FROM capability_capsules WHERE {' AND '.join(where)} "
        f"ORDER BY id DESC LIMIT :lim"), params).mappings().all()
    # 消费计数(轻:写 usage_log 一行,不阻塞查询)
    try:
        db.execute(_t(
            "INSERT INTO platform_audit (ts, actor, action, target, outcome) "
            "SELECT now(), 'ledger_query', 'capability_ledger', :f, 'ok'"),
            {"f": f"q={q} plane={plane} n={len(rows)}"})
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
    return {"success": True, "data": [dict(r) for r in rows], "meta": {"count": len(rows)}}


# ── 组织状态标准化面(org_state v1 · 2026-10-04) ──────────────────────
# 用户定调:机制沉淀要系统化工程化标准化,落到平台网站本身。
# 三个只读端点:frames(框卡)/rulings(裁决登记)/verdicts(判读索引)。
# 数据源复用既有件:config/org_frames.json + org_mailbox + feishu_decisions
# + intervention_log.jsonl——零新表。只读+脱敏,无须 key(沿 dispatch/public 先例)。

def _load_frames_registry() -> dict:
    import json as _json
    from pathlib import Path as _Path
    _f = _Path(__file__).resolve().parents[1] / "registry" / "org_frames.json"
    return _json.loads(_f.read_text(encoding="utf-8"))


def _parse_interventions(limit: int = 50) -> list:
    import json as _json
    from pathlib import Path as _Path
    _p = _Path(__file__).resolve().parents[1] / "docs" / "evidence" / "org-os" / "pilot" / "intervention_log.jsonl"
    rows: list = []
    if _p.exists():
        for line in _p.read_text(encoding="utf-8").splitlines()[-500:]:
            try:
                r = _json.loads(line)
                rows.append({"ts": r.get("ts"), "kind": "intervention",
                             "title": r.get("summary"), "by": "user",
                             "ref": f"intervention:{r.get('category', '')}"})
            except Exception:  # noqa: BLE001
                continue
    return rows[-limit:]


@router.get("/frames")
async def org_frames(db=Depends(get_db)):
    """框卡注册表(标准化):每框主线/判据/触达/时效 + 信箱最后来函时间。

    消费方:各框开轮自查定位/平台快照/新会话组织逻辑重建——治"判断半径超视野"。
    """
    try:
        reg = _load_frames_registry()
    except Exception as exc:  # noqa: BLE001
        return _err(f"frames registry unavailable: {exc}", status=503)
    live: dict = {}
    try:
        rows = db.execute(_text(
            "SELECT to_agent, max(created_at) FROM org_mailbox GROUP BY to_agent")).fetchall()
        live = {r[0]: str(r[1]) for r in rows}
    except Exception:  # noqa: BLE001  # 注册表仍可读,活性缺省
        pass
    frames = [dict(f, last_letter=live.get(f["frame"])) for f in reg.get("frames", [])]
    return {"success": True, "schema": reg.get("schema"),
            "data": frames, "meta": {"count": len(frames)}}


@router.get("/rulings")
async def org_rulings(limit: int = 50, db=Depends(get_db)):
    """裁决登记(标准化):决策卡+硬介入,近限50条。

    协议:任何框转呈/升级前先查本端点——已决勿呈(宪法13条④同题双呈按欠函病处置)。
    """
    items: list = []
    try:
        rows = db.execute(_text(
            "SELECT id, title, decided_by, created_at FROM feishu_decisions "
            "ORDER BY created_at DESC LIMIT :l"), {"l": limit}).fetchall()
        items += [{"ts": str(r[3]), "kind": "decision_card", "title": r[1],
                   "by": r[2], "ref": f"card:{r[0]}"} for r in rows]
    except Exception:  # noqa: BLE001  # 决策卡源失联不阻塞硬介入源
        pass
    items += _parse_interventions(limit=limit)
    items.sort(key=lambda x: x.get("ts") or "", reverse=True)
    data = items[:limit]
    return {"success": True, "data": data,
            "meta": {"count": len(data), "hint": "转呈/升级前先查本端点(宪法13条④)"}}


@router.get("/verdicts")
async def org_verdicts(limit: int = 50, db=Depends(get_db)):
    """判读索引(标准化):judge_writeback 落库的判读正本行(trace 前缀 writeback:)。

    消费方:材料方/判读方/平台取 verdict 不再翻函件正文。
    """
    rows = db.execute(_text(
        "SELECT id, from_agent, title, trace_id, created_at FROM org_mailbox "
        "WHERE trace_id LIKE 'writeback:%' ORDER BY id DESC LIMIT :l"), {"l": limit}).fetchall()
    data = [{"id": r[0], "from_agent": r[1], "title": r[2],
             "trace_id": r[3], "created_at": str(r[4])} for r in rows]
    return {"success": True, "data": data, "meta": {"count": len(data)}}

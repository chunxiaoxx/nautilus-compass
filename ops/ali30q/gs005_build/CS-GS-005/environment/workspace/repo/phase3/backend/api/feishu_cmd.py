"""贾维斯 v0 · 飞书指令入口(2026-09-15 · 用户两度提出,V5 248 同意接线)。

POST /api/platform/feishu/cmd
V5 callback_app(8092) 把 im.message.receive_v1 事件原样转发到此(透传
X-Lark-Signature),平台验签后执行固定指令面,回执 push_text 回同一会话。

安全(全 fail-closed):
- url_verification → challenge 回显(事件订阅验证)
- 验签:sha256(ts+nonce+FEISHU_ENCRYPT_KEY+body) base64,坏签名静默丢弃+计数
- **chat 白名单 = chat_id 匹配(FEISHU_CMD_CHAT_ID,缺省 feishu_push.CHAT_ID)
  或 chat_type=="p2p"**——用户是唯一人类,对 app 的私聊即用户本人;非 p2p 且
  非白名单一律丢弃(防注入)。伪造事件被字节级验签挡住,fail-closed 不变。
  (9/15 定谳:首版锁 oc_c9fbb 永假——那是哨兵 app 会话,8092 是 scorer app,
  用户私聊 chat_id 是另一个值;且两 app 会话隔离。)
- event_id 幂等:处理前先落 mailbox 台账(trace=feishu-cmd-<尾8位>),
  重试/并发重入被台账挡住

回执通道(9/15 v0.1):应答放响应体 {"reply": ...},由 8092(scorer app 凭据)
send_text 回原会话——push_text 走哨兵 app 凭据,发不进 scorer 会话。

v0 指令面(固定三条,防幻觉执行;task 投单等 v0 稳定后再开):
- status :组织快照(信箱待处理/M1 链/最新函,只读现成数据源)
- ask <问题> :LLM 答复(agent_engine LLMClient,与 soul 同通道,fail-soft)
- help    :用法
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.feishu_decision import feishu_signature  # 同款验签配方(c715ab62d)
from models.org_mailbox import OrgMailbox
import models.agent_survival  # noqa: F401 — mapper dependency
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/platform/feishu", tags=["Jarvis v0"])

_drops = {"bad_sig": 0, "nosig": 0, "no_key": 0, "wrong_chat": 0, "bad_shape": 0, "dup": 0}


def _cmd_chat_id() -> str:
    from ops.feishu_push import CHAT_ID
    return os.environ.get("FEISHU_CMD_CHAT_ID", CHAT_ID)


def _decrypt_feishu(payload: dict, key: str) -> dict | None:
    """飞书事件加密载荷解密:{"encrypt": b64} → 明文事件 dict。

    官方 SDK 算法(lark-oapi AESCipher 实测 9/15 定谳):AES-256-CBC,
    key=sha256(Encrypt Key),**iv=密文前 16 字节(IV 前置)**,PKCS7。
    注:iv 不是 key[:16]——首版此误致真实事件解密必败(自造密文自测
    又恰好绕过,模拟自证第 N 例)。
    """
    enc = payload.get("encrypt")
    if not isinstance(enc, str) or not enc:
        return None
    try:
        import base64
        import hashlib

        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        aes_key = hashlib.sha256(key.encode()).digest()
        data = base64.b64decode(enc)
        if len(data) < 32 or len(data) % 16 != 0:
            return None
        decryptor = Cipher(algorithms.AES(aes_key), modes.CBC(data[:16])).decryptor()
        padded = decryptor.update(data[16:]) + decryptor.finalize()
        pad = padded[-1]
        if pad < 1 or pad > 16 or padded[-pad:] != bytes([pad]) * pad:
            return None
        out = json.loads(padded[:-pad].decode("utf-8", "replace"))
        return out if isinstance(out, dict) else None
    except Exception as e:  # noqa: BLE001 — 解密失败按不可处理丢弃,fail-closed
        print(f"JARVIS-CMD decrypt-fail: {type(e).__name__}: {e}", flush=True)
        return None


def _extract_command(payload: dict):
    """返回 (event_id, chat_id, chat_type, text) 或 None。兼容新旧双 schema(旧版无 header)。"""
    ev = payload.get("event") if isinstance(payload, dict) else None
    if not isinstance(ev, dict):
        return None
    header = payload.get("header") or {}
    msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
    event_id = str(header.get("event_id") or msg.get("event_id") or msg.get("message_id") or "")
    chat_id = str(msg.get("chat_id") or "")
    chat_type = str(msg.get("chat_type") or "")
    if msg.get("message_type") != "text":
        return None
    try:
        text = str(json.loads(msg.get("content") or "{}").get("text", "")).strip()
    except (ValueError, AttributeError):
        return None
    if not event_id or not chat_id or not text:
        return None
    return event_id, chat_id, chat_type, text[:500]


def _org_status_snapshot(db: Session) -> str:
    """只读快照:信箱待处理/M1 链在途/最新三函。人话,≤400 字。"""
    now = datetime.now()
    pending = (db.query(OrgMailbox)
               .filter(OrgMailbox.to_agent == "platform", OrgMailbox.ack_at.is_(None))
               .order_by(OrgMailbox.id.desc()).limit(20).all())
    n_pending = len(pending)
    m1 = (db.query(OrgMailbox)
          .filter(OrgMailbox.trace_id.like("m1-%")).order_by(OrgMailbox.id.desc())
          .first())
    lines = [f"📮 平台待处理函 {n_pending} 封"]
    if m1 is not None:
        lines.append(f"🔗 M1 链在途:{m1.title[:40]}")
    for r in pending[:3]:
        lines.append(f"  · [{r.from_agent}] {(r.title or '')[:36]}")
    latest = (db.query(OrgMailbox).order_by(OrgMailbox.id.desc()).limit(3).all())
    lines.append("🗂 最新动态:")
    for r in latest:
        lines.append(f"  · {r.from_agent}→{r.to_agent}:{(r.title or '')[:30]}")
    # 记分牌段(9/17 接口位:v5 周频记分牌函若有则附摘要;数据源=v5 317 承诺)
    sb = (db.query(OrgMailbox)
          .filter(OrgMailbox.from_agent == "v5", OrgMailbox.to_agent == "platform",
                  OrgMailbox.title.like("%记分牌%"))
          .order_by(OrgMailbox.id.desc()).first())
    if sb is not None:
        lines.append(f"📊 记分牌({sb.created_at.strftime('%m-%d') if sb.created_at else '?'}):")
        lines.append("  " + (sb.body or "").strip()[:200])
    return "\n".join(lines)[:800]


def _llm_answer(question: str) -> str:
    from agent_engine.llm.client import get_llm_client
    reply = get_llm_client().chat(
        question,
        system="你是贾维斯,nautilus AI 原生组织(一个人类创始人+platform/v5/"
               "compass/flywheel/soul 五个 agent 框)的飞书值班入口。\n"
               "你的能力:回答用户的自由问题(通用问答/写作/分析/计算),"
               "中文简洁,300 字内,不知道就说不知道,不编造组织内部数据。\n"
               "组织实时状态(信箱/任务链/M1 进展)不在你的知识里——"
               "涉及这些请引导用户发送指令 status 查看组织快照;"
               "指令面还有 help(用法说明)。",
        max_tokens=2048)
    return str(reply)[:1200]


def _find_task(db: Session, ref: str):
    """按引用找任务函:纯数字=mailbox id;否则 trace/title 匹配。"""
    if ref.isdigit():
        return db.get(OrgMailbox, int(ref))
    like = f"%{ref}%"
    return (db.query(OrgMailbox)
            .filter(OrgMailbox.task_meta.isnot(None),
                    (OrgMailbox.trace_id.like(like) | OrgMailbox.title.like(like)))
            .order_by(OrgMailbox.id.desc()).first())


def _start_approval(db: Session, ref: str) -> str:
    row = _find_task(db, ref)
    if row is None:
        recent = (db.query(OrgMailbox).filter(OrgMailbox.task_meta.isnot(None))
                  .order_by(OrgMailbox.id.desc()).limit(3).all())
        tips = "\n".join(f"  · id {r.id} {(r.title or '')[:32]}" for r in recent) or "  (无)"
        return f"未找到任务 {ref}。最近任务:\n{tips}"
    now = datetime.now()
    db.add(OrgMailbox(
        from_agent="platform", to_agent="platform",
        trace_id=f"jarvis-confirm-{row.id}", title=f"[贾维斯·待确认] 批准 id{row.id}",
        body=f"用户发起批准 id {row.id}({(row.title or '')[:60]}),等待'确认'。",
        deadline=now + timedelta(minutes=30), created_at=now,
        task_meta={"jarvis_confirm": str(row.id), "consumer": str((row.task_meta or {}).get("consumer", "v5"))}))
    db.commit()
    return (f"将批准:id {row.id}「{(row.title or '')[:50]}」\n"
            f"回「确认」生效(30 分钟内),回「取消」放弃。")


def _confirm_approval(db: Session) -> str:
    now = datetime.now()
    pending = (db.query(OrgMailbox)
               .filter(OrgMailbox.trace_id.like("jarvis-confirm-%"),
                       OrgMailbox.ack_at.is_(None))
               .order_by(OrgMailbox.id.desc()).first())
    if pending is None:
        return "没有待确认的批准。先用「批准 <任务id>」发起。"
    task_id = (pending.task_meta or {}).get("jarvis_confirm", "?")
    consumer = (pending.task_meta or {}).get("consumer", "v5")
    target = db.get(OrgMailbox, int(task_id)) if str(task_id).isdigit() else None
    title = (target.title or "")[:50] if target else task_id
    db.add(OrgMailbox(
        from_agent="user", to_agent=str(consumer),
        trace_id=f"jarvis-approved-{task_id}-{now.strftime('%H%M%S')}",
        title=f"[用户批准·贾维斯落函] id {task_id}",
        body=(f"用户经贾维斯(白名单会话+验签+二次确认)批准任务 id {task_id}"
              f"「{title}」。\n本函 from=user 为人类拍板记录,不可代发。"),
        deadline=now + timedelta(hours=2), created_at=now))
    pending.ack_at = now
    pending.ack_note = "confirmed by user via jarvis"
    db.commit()
    return f"✅ 已批准 id {task_id}「{title}」,已落函通知 {consumer}。"


def _cancel_approval(db: Session) -> str:
    now = datetime.now()
    rows = (db.query(OrgMailbox)
            .filter(OrgMailbox.trace_id.like("jarvis-confirm-%"),
                    OrgMailbox.ack_at.is_(None)).all())
    for r in rows:
        r.ack_at = now
        r.ack_note = "cancelled by user"
    db.commit()
    return f"已取消 {len(rows)} 条待确认。" if rows else "没有待确认的批准。"


def _dispatch_command(text: str, db: Session) -> str:
    low = text.lower()
    # —— @框直达指令(9/18 接口层收口件):「@flywheel UMI 优先」→ 以
    # from='user'(人类身份)落函直达目标框,用户单入口指挥全组织 ——
    m_at = re.match(r"^@(flywheel|v5|compass|soul|platform)\s+(.+)", text.strip(), re.I)
    if m_at:
        to, msg = m_at.group(1).lower(), m_at.group(2).strip()[:400]
        now = datetime.now()
        trace = f"jarvis-direct-{to}-{now.strftime('%H%M%S')}"
        db.add(OrgMailbox(from_agent="user", to_agent=to, trace_id=trace,
                          title=f"[用户直达指令] {msg[:40]}",
                          body=f"用户经贾维斯(@转发)下达指令:\n{msg}\n"
                               f"(from=user,白名单会话+验签,2h SLA)",
                          deadline=now + timedelta(hours=2), created_at=now,
                          task_meta={"task_type": "jarvis_direct", "consumer": to}))
        db.commit()
        return f"📨 已转达 {to}:「{msg[:60]}」(2h SLA 已挂,回函哨兵会推你)"
    if low in ("help", "帮助", "?"):
        return ("贾维斯 v0.3 指令面:\n"
                "· status —— 组织快照(信箱/链/动态/记分牌)\n"
                "· @框名 指令 —— 直达指定框(如「@flywheel UMI 并行优先」),以你的名义落函\n"
                "· 批准 <任务id> —— 发起任务批准(回「确认」生效,「取消」放弃)\n"
                "· ask <问题>(或直接发任意文本)—— 提问;自由文本走 v5 脑\n"
                "· help —— 本说明")
    if low == "status" or text.startswith("状态"):
        return _org_status_snapshot(db)
    # —— 裁决指令(9/17 壳脑分工接线):批准 T-xxx / 确认 / 取消 ——
    m = re.match(r"^(?:批准|approve)\s*(?:T-?|#)?(\w{1,24})", text.strip(), re.I)
    if m:
        return _start_approval(db, m.group(1))
    if text.strip() in ("确认", "confirm", "ok"):
        return _confirm_approval(db)
    if text.strip() in ("取消", "cancel"):
        return _cancel_approval(db)
    q = text
    if low.startswith("ask ") or low.startswith("ask:") or text.startswith("问 "):
        q = text[4:].strip() if not text.startswith("问 ") else text[2:].strip()
        if not q:
            return "用法:ask <问题>"
    # v0.2(9/17 壳脑分工,300 确认):非指令文本路由 v5 脑(respond_via_v5,
    # 带会话记忆);显式 ask 仍走平台 LLM。路由由 cmd 主流程解释此哨兵。
    if not (low.startswith("ask ") or low.startswith("ask:") or text.startswith("问 ")):
        return f"__ROUTE_V5__{text}"
    try:
        return _llm_answer(q)
    except Exception as e:  # noqa: BLE001 — LLM fail-soft,明确报错不吞
        logger.error("feishu cmd ask llm failed: %s", e)
        return f"ask 执行失败({type(e).__name__}),稍后再试或走对话框。"


@router.post("/cmd")
async def feishu_cmd(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        print(f"JARVIS-CMD badjson: {type(e).__name__}", flush=True)
        return {"code": 0, "note": "bad json; dropped"}
    if payload.get("type") == "url_verification":
        return {"challenge": str(payload.get("challenge", ""))}
    key = os.environ.get("FEISHU_ENCRYPT_KEY")
    if not key:
        _drops["no_key"] += 1
        print("JARVIS-CMD nokey: FEISHU_ENCRYPT_KEY missing", flush=True)
        return {"code": 0, "note": "channel not configured; dropped"}
    sig = request.headers.get("X-Lark-Signature", "")
    # 飞书真实事件的 ts/nonce 在请求头(X-Lark-Request-*),不在 body;
    # payload/query 仅为测试兼容兜底(9/15 定谳:首版只读 payload,真实事件必挂)
    ts = (request.headers.get("X-Lark-Request-Timestamp")
          or str(payload.get("ts") or request.query_params.get("ts", "")))
    nonce = (request.headers.get("X-Lark-Request-Nonce")
             or str(payload.get("nonce") or request.query_params.get("nonce", "")))
    if not sig:
        _drops["nosig"] += 1
        print("JARVIS-CMD nosig: event arrived without X-Lark-Signature"
              " (app 未配 Encrypt Key?)", flush=True)
        return {"code": 0, "note": "no signature; dropped"}
    if sig != feishu_signature(ts, nonce, key, raw):
        _drops["bad_sig"] += 1
        print(f"JARVIS-CMD badsig: ts={ts} nonce={nonce} sig={sig[:20]}..."
              f" expect={feishu_signature(ts, nonce, key, raw)[:20]}...", flush=True)
        return {"code": 0, "note": "signature mismatch; dropped"}
    parsed = _extract_command(payload)
    if parsed is None and isinstance(payload.get("encrypt"), str):
        # 加密事件:验签对密文 raw 成立(飞书签密文),解密后重新解析
        plain = _decrypt_feishu(payload, key)
        if plain is not None:
            vt = os.environ.get("FEISHU_VERIFICATION_TOKEN")
            tok = str(((plain.get("header") or {}).get("token")) or "")
            if vt and tok and tok != vt:
                _drops["bad_sig"] += 1
                print("JARVIS-CMD badtoken: decrypted token mismatch", flush=True)
                return {"code": 0, "note": "token mismatch; dropped"}
            parsed = _extract_command(plain)
            payload = plain
    if parsed is None:
        _drops["bad_shape"] += 1
        _dbg_ev = payload.get("event") if isinstance(payload.get("event"), dict) else {}
        _dbg_msg = _dbg_ev.get("message") if isinstance(_dbg_ev.get("message"), dict) else {}
        print(f"JARVIS-CMD badshape: payload_keys={sorted(payload.keys())[:8]} "
              f"msg_keys={sorted(_dbg_msg.keys())[:10]} "
              f"msg_type={_dbg_msg.get('message_type')!r} "
              f"content={str(_dbg_msg.get('content'))[:120]}",
              flush=True)
        return {"code": 0, "note": "no actionable text message; dropped"}
    event_id, chat_id, chat_type, text = parsed
    if chat_id != _cmd_chat_id() and chat_type != "p2p":
        _drops["wrong_chat"] += 1
        print(f"JARVIS-CMD wrongchat: chat={chat_id[:12]} type={chat_type}", flush=True)
        return {"code": 0, "note": "chat not whitelisted; dropped"}
    trace = f"feishu-cmd-{event_id[-8:]}"
    if db.query(OrgMailbox).filter_by(trace_id=trace).first() is not None:
        _drops["dup"] += 1
        return {"code": 0, "note": "duplicate event; dropped"}
    # 先落台账(幂等占位,重试被挡)→执行→回执
    now = datetime.now()
    db.add(OrgMailbox(from_agent="platform", to_agent="platform", trace_id=trace,
                      title=f"[贾维斯指令] {text[:60]}",
                      body=f"feishu im.message 指令(event_id={event_id[:24]},chat={chat_id[:10]},"
                           f"type={chat_type or '?'}):\n{text}",
                      deadline=now + timedelta(hours=2), created_at=now))
    db.commit()
    reply = _dispatch_command(text, db)
    note = "handled; reply in body (caller sends receipt)"
    if reply.startswith("__ROUTE_V5__"):
        # 壳脑分工(300 确认):自由文本 → v5 脑。明文随响应体回 8092(壳已
        # 验签+解密+落台账,脑只管回答;respond_via_v5 带 chat_id 会话记忆)。
        row = db.query(OrgMailbox).filter_by(trace_id=trace).first()
        if row is not None:
            row.ack_at = datetime.now()
            row.ack_note = "routed to v5 brain (respond_via_v5)"
            db.commit()
        return {"code": 0, "note": "routed to v5 brain; 8092 calls respond_via_v5",
                "route": "v5", "text": reply[len("__ROUTE_V5__"):], "chat_id": chat_id}
    row = db.query(OrgMailbox).filter_by(trace_id=trace).first()
    if row is not None:
        row.ack_at = datetime.now()
        row.ack_note = note
        db.commit()
    # chat_id 随响应体回传——加密事件下 8092 拿不到明文字段,send_text 目标以此为准
    return {"code": 0, "note": note, "reply": f"🤖 {reply}", "chat_id": chat_id}

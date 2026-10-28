"""飞书决策卡通道(V5 设计稿 · platform 实施 · 2026-08-29)。

- POST /api/platform/feishu/decision          发起待拍板事项(幂等 trace_id;2-4 选项)
- POST /api/platform/feishu/card/callback     飞书事件订阅回调(challenge 回显/验签 fail-closed/按钮落库)
- GET  /api/platform/feishu/decision/{trace}  各框读结果(到期未决记 default)

红线(设计稿照单):卡片内容不带 PII/甲方名/密钥;验签失败静默丢弃+计数;
FEISHU_ENCRYPT_KEY 未配置 = 通道不上线(卡片不发送,回调静默丢弃)。
v0 边界:卡片实际发送待用户完成飞书应用配置(机器人+IM 权限+事件订阅)后启用。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from models.feishu_decision import FeishuDecision
from utils.database import get_db

router = APIRouter(prefix="/api/platform/feishu", tags=["Org OS"])

_callback_drops = {"bad_sig": 0, "no_key": 0, "unknown": 0}  # 计数告警用(进程内)


def _ok(data, status=200):
    if status == 200:
        return {"success": True, "data": data, "error": None}
    return JSONResponse(status_code=status,
                        content={"success": True, "data": data, "error": None})


def _err(msg, status=400):
    return JSONResponse(status_code=status,
                        content={"success": False, "data": None, "error": msg})


def _parse_deadline(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def feishu_signature(ts: str, nonce: str, key: str, body: bytes) -> str:
    """飞书事件订阅签名:sha256(ts + nonce + encrypt_key + body) 的 hexdigest。

    9/15 官方 SDK 定谳(lark-oapi _verify_sign):hexdigest,非 base64——
    首版 base64 编码致真实事件验签必败(自签自验同错自洽,模拟自证;
    8/30 决策卡转发疑被静默丢弃的另一半根因或即此)。
    """
    return hashlib.sha256(
        ts.encode() + nonce.encode() + key.encode() + body).hexdigest()


@router.post("/decision")
def create_decision(body: dict, db=Depends(get_db)):
    required = ("trace_id", "title", "options", "default", "deadline")
    missing = [k for k in required if body.get(k) in (None, "", [])]
    if missing:
        return _err(f"missing required field(s): {', '.join(missing)}")
    options = [str(o) for o in body["options"]]
    if not (2 <= len(options) <= 4):
        return _err("options must contain 2-4 choices")
    default = str(body["default"])
    if default not in options:
        return _err("default must be one of options")
    deadline = _parse_deadline(body["deadline"])
    if deadline is None:
        return _err("deadline must be ISO8601")
    trace = str(body["trace_id"])
    existing = db.query(FeishuDecision).filter_by(trace_id=trace).first()
    if existing is not None:
        if not existing.card_sent:  # 幂等重入=重试发卡的机会
            code, note = _try_send_card(existing, json.loads(existing.options_json))
            if code == 0:
                existing.card_sent = True
            existing.card_note = note
            db.commit()
        data = existing.to_dict()
        data["idempotent"] = True
        return _ok(data)
    row = FeishuDecision(
        trace_id=trace, title=str(body["title"])[:256], options_json=json.dumps(options),
        default_choice=default, deadline=deadline,
        context=str(body.get("context", ""))[:512],
        card_sent=False,
        card_note="pending")
    db.add(row)
    db.commit()
    db.refresh(row)
    code, note = _try_send_card(row, options)
    if code == 0:
        row.card_sent = True
    row.card_note = note
    db.commit()
    db.refresh(row)
    return _ok(row.to_dict())


@router.get("/decision/vote")
def vote_url(trace: str, choice: str, exp: str, sig: str, db=Depends(get_db)):
    """URL-token 投票(0b 备用通道):卡片回调总线不可用时,点链接落票。
    sig = HMAC-SHA256(key=FEISHU_ENCRYPT_KEY, msg=f"{trace}|{choice}|{exp}")。
    注意:必须声明在 /decision/{trace_id} 之前,否则 vote 被路径参数吞掉。"""
    key = os.environ.get("FEISHU_ENCRYPT_KEY")
    if not key:
        return JSONResponse(status_code=503, content={"success": False,
                                                      "error": "channel not configured"})
    if int(exp) < datetime.now(timezone.utc).timestamp():
        return JSONResponse(status_code=410, content={"success": False,
                                                      "error": "vote link expired"})
    if not hmac.compare_digest(sig, _vote_sig(trace, choice, exp, key)):
        return JSONResponse(status_code=403, content={"success": False,
                                                      "error": "bad signature"})
    row = db.query(FeishuDecision).filter_by(trace_id=trace).first()
    if row is None or choice not in json.loads(row.options_json):
        return JSONResponse(status_code=400, content={"success": False,
                                                      "error": "unknown trace / invalid choice"})
    if row.choice is None:
        row.choice = choice
        row.decided_at = datetime.utcnow()
        row.decided_by = "url-vote"
        db.commit()
    note = "recorded" if row.choice == choice else f"already decided: {row.choice}"
    return JSONResponse(content={"success": True, "note": note})


@router.get("/decision/{trace_id}")
def get_decision(trace_id: str, db=Depends(get_db)):
    row = db.query(FeishuDecision).filter_by(trace_id=trace_id).first()
    if row is None:
        return _err("decision not found", status=404)
    data = row.to_dict()
    # 到期未决 → 记 default(幂等:已决不覆盖)
    if row.choice is None and datetime.utcnow() >= row.deadline:
        row.choice = row.default_choice
        row.decided_at = datetime.utcnow()
        row.decided_by = "default"
        db.commit()
        db.refresh(row)
        data = row.to_dict()
        data["default_applied"] = True
    return _ok(data)


def _extract_action(payload: dict) -> tuple[str, str] | None:
    """从回调体提取 (trace_id, choice);v2.0 与旧版卡片形状都试。"""
    ev = payload.get("event") if isinstance(payload, dict) else None
    if not isinstance(ev, dict):
        return None
    action = ev.get("action") if isinstance(ev.get("action"), dict) else {}
    value = action.get("value")
    if isinstance(value, dict) and value.get("trace_id") and value.get("choice"):
        return str(value["trace_id"]), str(value["choice"])
    return None


@router.post("/card/callback")
async def card_callback(request: Request, db=Depends(get_db)):
    raw = await request.body()
    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001
        return {"challenge": "", "note": "bad json"}
    # ① 事件订阅 URL 验证
    if payload.get("type") == "url_verification":
        return {"challenge": str(payload.get("challenge", ""))}
    # ② 验签 fail-closed:无密钥=通道未上线,静默丢弃
    key = os.environ.get("FEISHU_ENCRYPT_KEY")
    if not key:
        _callback_drops["no_key"] += 1
        return {"code": 0, "note": "channel not configured; dropped"}
    # 飞书官方规范:ts/nonce 在 body 顶层;兼容 query 传参(内部转发器路径)
    sig = request.headers.get("X-Lark-Signature", "")
    ts = str(payload.get("ts") or request.query_params.get("ts", ""))
    nonce = str(payload.get("nonce") or request.query_params.get("nonce", ""))
    if not sig or sig != feishu_signature(ts, nonce, key, raw):
        _callback_drops["bad_sig"] += 1
        return {"code": 0, "note": "signature mismatch; dropped"}  # 静默丢弃(200 防重试风暴)
    # ③ 落库(幂等:已决不覆盖)
    action = _extract_action(payload)
    if action is None:
        _callback_drops["unknown"] += 1
        return {"code": 0, "note": "no actionable value; dropped"}
    trace_id, choice = action
    row = db.query(FeishuDecision).filter_by(trace_id=trace_id).first()
    if row is None or row.choice is not None or choice not in json.loads(row.options_json):
        _callback_drops["unknown"] += 1
        return {"code": 0, "note": "unknown trace / already decided / invalid choice"}
    row.choice = choice
    row.decided_at = datetime.utcnow()
    row.decided_by = "feishu-card"
    db.commit()
    return {"code": 0, "note": "recorded"}


def _vote_sig(trace: str, choice: str, exp: str, key: str) -> str:
    msg = f"{trace}|{choice}|{exp}".encode()
    return hmac.new(key.encode(), msg, hashlib.sha256).hexdigest()


# ---- 卡片发送侧(2026-09-15 Q3 接线:决策落库后实际发卡到用户 p2p) ----

PUBLIC_BASE = os.environ.get("FEISHU_PUBLIC_BASE", "https://www.nautilus.social")


def _vote_link(trace: str, choice: str, deadline: datetime, key: str) -> str:
    from urllib.parse import quote
    exp = str(int(deadline.replace(tzinfo=timezone.utc).timestamp()))
    sig = _vote_sig(trace, choice, exp, key)
    return (f"{PUBLIC_BASE}/api/platform/feishu/decision/vote"
            f"?trace={quote(trace)}&choice={quote(choice)}&exp={exp}&sig={sig}")


def _build_card(row, options: list, key: str) -> dict:
    md = [f"**{row.title}**"]
    if row.context:
        md.append(str(row.context))
    md.append(f"截止(UTC):{row.deadline.isoformat()}Z · 到期未决记 default:**{row.default_choice}**")
    actions = []
    for i, opt in enumerate(options):
        actions.append({"tag": "button",
                        "text": {"tag": "plain_text", "content": str(opt)[:20]},
                        "type": "primary" if i == 0 else "default",
                        "url": _vote_link(row.trace_id, str(opt), row.deadline, key)})
    return {"config": {"wide_screen_mode": True},
            "header": {"template": "blue",
                       "title": {"tag": "plain_text", "content": "🗳️ 待拍板"}},
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(md)}},
                {"tag": "hr"},
                {"tag": "action", "actions": actions},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"trace: {row.trace_id} · 点击按钮即落票"}]},
            ]}


def _try_send_card(row, options: list) -> tuple:
    """fail-soft:决策本体已落库,发卡是增强。返回 (feishu_code|None, note)。"""
    key = os.environ.get("FEISHU_ENCRYPT_KEY")
    if not key:
        return None, "channel not configured (FEISHU_ENCRYPT_KEY unset)"
    try:
        from ops.feishu_push import push_card
        code = push_card(_build_card(row, options, key))
        return code, ("card sent (code 0)" if code == 0 else f"feishu code {code}")
    except Exception as e:  # noqa: BLE001
        return -1, f"send error: {type(e).__name__}: {e}"




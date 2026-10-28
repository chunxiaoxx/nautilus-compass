# -*- coding: utf-8 -*-
"""飞书指令入口(轮询版 · 9/4 用户拍"开工第 1 步:飞书指令入口")。

用户 p2p 文本消息 → im:listMessages 增量水位 → LLM(k3·自有中转站)判读 →
  answer:  用组织状态直答(≤300 字人话)
  forward: 落 mailbox(to=platform)转平台处理,回执"已受理"
安全边界:仅 LARK_P0_CHAT_ID 单聊、仅文本、跳 bot 自身消息(防回环)、
LLM 只产出"直答文本"或"转发摘要"两种结果,不生成任何执行动作;
高危类(对外/花钱)一律 forward 由平台框会话处理。
LLM 挂→fail-soft 全部 forward+模板回执,消息永不丟。

云端手动跑: python3 ops/feishu_cmd_poll.py [--once]
验证通过后挂 systemd timer 5min(oneshot)。
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request as u
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
STATE = BASE / "feishu_cmd_state.json"
API = "https://open.feishu.cn/open-apis"

SYSTEM = """你是"智涌Nautilus"组织平台的飞书入口助手,用户是组织所有者(懂业务不懂代码)。
输入=用户消息+组织实时状态。只输出一行 JSON,两种取值:
{"type":"answer","text":"..."}  ——用户在问组织状态/进展/函件等,用快照信息人话直答(≤300字,禁代码/术语)
{"type":"forward","summary":"..."} ——用户在下指令(发函/催办/派单/记录/涉钱涉外),你不执行,summary≤80字供平台处置
拿不准一律 forward。禁止在 text 里承诺任何你无法验证的事。"""


def load_env() -> None:
    for p in ("/opt/ecc-shared/.env", BASE / ".env"):
        if Path(p).exists():
            for line in open(p, encoding="utf-8"):
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v.strip().strip('"'))


def api(path: str, token: str | None = None, payload: dict | None = None,
        params: str = "") -> dict:
    req = u.Request(API + path + params,
                    data=json.dumps(payload).encode() if payload else None,
                    headers={"Content-Type": "application/json",
                             **({"Authorization": "Bearer " + token} if token else {})},
                    method="POST" if payload else "GET")
    return json.loads(u.urlopen(req, timeout=20).read())


def bot_open_id(token: str) -> str:
    return (api("/bot/v3/info", token).get("bot") or {}).get("open_id", "")


def fetch_new(token: str, since_ms: int) -> list[dict]:
    end = int(time.time() * 1000)
    q = (f"/im/v1/messages?container_id_type=chat&container_id={os.environ['LARK_P0_CHAT_ID']}"
         f"&start_time={since_ms}&end_time={end}&sort_type=ByCreateTimeAsc&page_size=50")
    items = (api(q, token).get("data") or {}).get("items") or []
    out = []
    for it in items:
        if it.get("msg_type") != "text" or it.get("sender", {}).get("sender_type") == "app":
            continue
        try:
            text = json.loads(it["body"]["content"]).get("text", "").strip()
        except Exception:
            continue
        text = text.replace("@_user_1", "").strip()
        if text:
            out.append({"ts": int(it["create_time"]), "sender": it["sender"]["id"], "text": text})
    return out


def send_text(token: str, text: str) -> None:
    api("/im/v1/messages?receive_id_type=chat_id", token, payload={
        "receive_id": os.environ["LARK_P0_CHAT_ID"], "msg_type": "text",
        "content": json.dumps({"text": text})})


def org_context() -> str:
    ctx = ""
    for p in ("/tmp/snap_human.txt", "/tmp/snap.txt"):
        try:
            ctx += open(p, encoding="utf-8").read()[:3000]
            break
        except OSError:
            continue
    try:
        sys.path.insert(0, str(BASE.parent))
        import models.agent_survival  # noqa: F401
        from utils.database import SessionLocal
        from sqlalchemy import text
        s = SessionLocal()
        un = s.execute(text("SELECT to_agent,COUNT(*) FROM org_mailbox WHERE ack_at IS NULL GROUP BY to_agent")).fetchall()
        led = s.execute(text("SELECT trace_id FROM feishu_decisions WHERE trace_id LIKE 'decision-%' ORDER BY id DESC LIMIT 3")).fetchall()
        s.close()
        ctx += f"\n[实时]未ack={un} 登记处最新={[x[0] for x in led]}"
    except Exception as e:  # noqa: BLE001
        ctx += f"\n[实时查询失败:{str(e)[:60]}]"
    return ctx


def llm_route(text: str, ctx: str) -> dict | None:
    ck = os.environ.get("CHUNXIAO_API_KEY")
    if not ck:
        return None
    try:
        req = u.Request(os.environ.get("CHUNXIAO_BASE_URL", "https://api.chunxiao.wang/v1")
                        + "/chat/completions",
                        data=json.dumps({"model": "k3", "max_tokens": 1500,
                            "messages": [{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": f"[组织状态]\n{ctx}\n\n[用户消息]\n{text}"}]}).encode(),
                        headers={"Authorization": "Bearer " + ck,
                                 "Content-Type": "application/json"}, method="POST")
        d = json.loads(u.urlopen(req, timeout=170).read())
        raw = (d.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        raw = raw[raw.index("{"):raw.rindex("}") + 1] if "{" in raw and "}" in raw else raw
        r = json.loads(raw)
        return r if r.get("type") in ("answer", "forward") else None
    except Exception:
        return None


def forward_to_platform(token: str, text: str, summary: str, msg: dict) -> None:
    payload = {"from_agent": "user-prime", "to_agent": "platform",
               "trace_id": f"cmd-{msg['ts']}",
               "deadline": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
               "title": f"[用户飞书指令] {summary[:60]}",
               "body": f"来源=飞书指令入口(轮询版)\n原文:{text}\n判读摘要:{summary}"}
    req = u.Request("http://127.0.0.1:8000/api/platform/org/mailbox",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"}, method="POST")
    ok = json.loads(u.urlopen(req, timeout=15).read()).get("success")
    send_text(token, "已受理,转平台处理。" if ok else "指令已记录,但落库失败——请到 platform 对话框补发。")


def process(token: str, msg: dict, state: dict) -> None:
    r = llm_route(msg["text"], org_context())
    if r and r["type"] == "answer" and r.get("text"):
        send_text(token, r["text"][:900])
    elif r and r.get("summary"):
        forward_to_platform(token, msg["text"], r["summary"], msg)
    else:  # LLM 挂/解析失败:fail-soft 全转发
        forward_to_platform(token, msg["text"], "LLM判读不可用,原样转平台", msg)
    state["last_ms"] = msg["ts"]


def main() -> None:
    load_env()
    state = json.loads(STATE.read_text()) if STATE.exists() else {"last_ms": int(time.time() * 1000) - 3600_000}
    tok = api("/auth/v3/tenant_access_token/internal",
              payload={"app_id": os.environ["LARK_APP_ID"],
                       "app_secret": os.environ["LARK_APP_SECRET"]})["tenant_access_token"]
    me = bot_open_id(tok)
    msgs = [m for m in fetch_new(tok, state["last_ms"]) if m["sender"] != me]
    for m in msgs:
        print(f"handle: {m['ts']} {m['text'][:40]}")
        process(tok, m, state)
        STATE.write_text(json.dumps(state))  # 逐条落盘,中断不重发
    print(f"done: {len(msgs)} handled, last_ms={state['last_ms']}")


if __name__ == "__main__":
    main()
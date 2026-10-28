# -*- coding: utf-8 -*-
"""决策卡批量补发(9/2)——修"待接卡片发送调用"断点:卡入库从未发送。
- 3 张在库 v2 卡(一页纸/招募/Orbbec)延期防 default 覆盖
- 3 张新卡入库(kairos/¥7重测/seed3,经 POST /decision 幂等)
- 全部 6 张按一卡一消息发飞书 p2p(URL-token 投票,48h 有效)
云端跑: cd backend && python3 docs/evidence/org-os/pilot/send_decision_cards_20260902.py
"""
import os, sys, json, hmac, hashlib, time
from datetime import datetime
import urllib.request as urlreq
import urllib.parse as uparse

sys.path.insert(0, ".")
for _p in (".env", "/home/ubuntu/nautilus-v5/.env.systemd", "/home/ubuntu/nautilus-v5/.env"):
    if os.path.exists(_p):
        for ln in open(_p, encoding="utf-8"):
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.strip().split("=", 1)
                os.environ.setdefault(k, v.strip().strip('"'))

import models.agent_survival  # noqa: F401 mapper chain
from models.feishu_decision import FeishuDecision
from utils.database import SessionLocal

API = "http://127.0.0.1:8000/api/platform/feishu"
PUB = "https://www.nautilus.social/api/platform/feishu/decision/vote"
CHAT_ID = "oc_c9fbb71be60e8d64fb0c854078b05847"
KEY = os.environ["FEISHU_ENCRYPT_KEY"]
EXP = str(int(time.time()) + 48 * 3600)
NEW_DL = "2026-09-03 18:00:00"

NEW = [
    dict(trace_id="kairos-disposal-20260902",
         title="kairos 处置(V5提案:最老agent 4/21注册,身份/a2a/经济三断60天零消费)",
         options=["A·救助(修完没活派)", "B·安乐死", "C·封存(V5荐:stop+disable可逆+解冻条件)"],
         default="C·封存(V5荐:stop+disable可逆+解冻条件)"),
    dict(trace_id="d6-k8-retest-20260902",
         title="¥7 k=8 重测(d6 adapter随盘丢失;pass@k单调,k=3翻不到PROVEN线)",
         options=["a·重训三臂再k=8(数百元)", "b·base单臂k=8(¥1-2)", "c·不重测k=3定案(V5荐)"],
         default="c·不重测k=3定案(V5荐)"),
    dict(trace_id="seed3-b-track-20260902",
         title="seed3 B轨补测(全量90G大磁盘;飞轮评估对京沪对接零加成)",
         options=["A·挂起等n=3口径需求(飞轮荐)", "B·补测租大磁盘实例"],
         default="A·挂起等n=3口径需求(飞轮荐)"),
]

for c in NEW:
    body = dict(c, deadline=NEW_DL, context="platform 9/2 积压决策清单")
    req = urlreq.Request(API + "/decision", data=json.dumps(body).encode(),
                         headers={"Content-Type": "application/json"}, method="POST")
    with urlreq.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
        print("new:", c["trace_id"][:30], "idempotent" if d["data"].get("idempotent") else "created")

s = SessionLocal()
cards = s.query(FeishuDecision).filter_by(card_sent=False).filter(
    FeishuDecision.choice.is_(None)).filter(
    ~FeishuDecision.trace_id.like("deploy-smoke%")).order_by(FeishuDecision.id).all()
print("待发卡:", [(c.id, c.trace_id) for c in cards])


def vote_url(trace, choice):
    sig = hmac.new(KEY.encode(), f"{trace}|{choice}|{EXP}".encode(), hashlib.sha256).hexdigest()
    return (f"{PUB}?trace={uparse.quote(trace)}&choice={uparse.quote(choice)}"
            f"&exp={EXP}&sig={sig}")


def fs_send(text):
    body = {"app_id": os.environ["FEISHU_APP_ID"],
            "app_secret": os.environ["FEISHU_APP_SECRET"]}
    req = urlreq.Request("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                         data=json.dumps(body).encode(),
                         headers={"Content-Type": "application/json"}, method="POST")
    with urlreq.urlopen(req, timeout=30) as r:
        tok = json.loads(r.read())["tenant_access_token"]
    req = urlreq.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=json.dumps({"receive_id": CHAT_ID, "msg_type": "text",
                         "content": json.dumps({"text": text})}).encode(),
        headers={"Authorization": "Bearer " + tok,
                 "Content-Type": "application/json"}, method="POST")
    with urlreq.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


fs_send("📋 决策卡通道修复:此前 8 张卡入库未发送(断点在'待接卡片发送调用'),现在补发 "
        f"{len(cards)} 张未决卡。点选项链接即落票(48h 有效);到期未决按各卡 default 记。")
for c in cards:
    c.deadline = datetime(2026, 9, 3, 18, 0, 0)
    opts = json.loads(c.options_json)
    lines = [f"【决策卡 #{c.id}】{c.title}", f"deadline 09-03 18:00 UTC+8 · trace {c.trace_id}", ""]
    for o in opts:
        lines.append(f"▶ {o}")
        lines.append(vote_url(c.trace_id, o))
        lines.append("")
    resp = fs_send("\n".join(lines))
    if resp.get("code") == 0:
        c.card_sent = True
        c.card_note = "sent via url-token p2p 9/2"
        print("sent:", c.id, c.trace_id[:34], "code", resp.get("code"))
    else:
        print("FAIL:", c.id, resp.get("code"), str(resp.get("msg"))[:60])
s.commit()
for c in s.query(FeishuDecision).all():
    print(c.id, c.trace_id[:32], "sent" if c.card_sent else "-", c.choice or "-")
s.close()

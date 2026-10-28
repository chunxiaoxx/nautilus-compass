# -*- coding: utf-8 -*-
"""飞书文本推送正本(2026-09-12 自 send_snapshot_push.py 抽出)。

凭据加载:云 backend/.env + v5 .env.systemd(与 send_snapshot_push 同配方);
chat_id = 平台 p2p 会话(8/30 首发验证 code 0)。
"""
from __future__ import annotations

import json
import os
import urllib.request as u

CHAT_ID = "oc_c9fbb71be60e8d64fb0c854078b05847"
BASE = "https://open.feishu.cn/open-apis"


def _load_env() -> None:
    for p in ("/home/ubuntu/nautilus-mvp/phase3/backend/.env",
              "/home/ubuntu/nautilus-v5/.env.systemd"):
        try:
            for line in open(p, encoding="utf-8"):
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v.strip('"'))
        except FileNotFoundError:
            continue


def push_text(text: str) -> int:
    """发文本到平台 p2p 会话,返回飞书 code(0=成功)。"""
    return _send_message("text", json.dumps({"text": text}))


def push_card(card: dict) -> int:
    """发 interactive 卡片到平台 p2p 会话,返回飞书 code(0=成功)。
    2026-09-15:决策卡发送侧接线(Q3)——与 push_text 同凭据同会话。"""
    return _send_message("interactive", json.dumps(card))


def _send_message(msg_type: str, content_json: str) -> int:
    import logging
    import urllib.error
    _load_env()
    try:
        tok_req = u.Request(
            BASE + "/auth/v3/tenant_access_token/internal",
            data=json.dumps({"app_id": os.environ["FEISHU_APP_ID"],
                             "app_secret": os.environ["FEISHU_APP_SECRET"]}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        tok = json.loads(u.urlopen(tok_req, timeout=30).read())["tenant_access_token"]
        msg = u.Request(
            BASE + "/im/v1/messages?receive_id_type=chat_id",
            data=json.dumps({"receive_id": CHAT_ID, "msg_type": msg_type,
                             "content": content_json}).encode(),
            headers={"Authorization": "Bearer " + tok,
                     "Content-Type": "application/json"}, method="POST")
        return json.loads(u.urlopen(msg, timeout=30).read()).get("code", -1)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        logging.getLogger(__name__).warning("feishu push failed: %s", e)
        return -1
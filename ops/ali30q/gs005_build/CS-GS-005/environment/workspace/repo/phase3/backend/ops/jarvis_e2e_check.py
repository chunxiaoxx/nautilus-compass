#!/usr/bin/env python3
"""贾维斯 v0 E2E 自测:模拟 V5 转发一条真签名 help 指令(2026-09-15)。
期望:code=0 + handled + receipt code=0(用户飞书收到回执)。"""
import base64
import hashlib
import json
import os
import sys
import urllib.request as u
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ops.feishu_push import _load_env, CHAT_ID  # noqa: E402 — 云端同配方加载凭据

_load_env()
key = os.environ["FEISHU_ENCRYPT_KEY"]
body = {
    "header": {"event_id": "evt-e2e-jarvis-20260915-01",
               "event_type": "im.message.receive_v1"},
    "event": {"message": {
        "chat_id": os.environ.get("FEISHU_CMD_CHAT_ID", CHAT_ID),
        "message_type": "text", "content": json.dumps({"text": "help"})}},
    "ts": "1757900000", "nonce": "n-e2e-1",
}
raw = json.dumps(body).encode()
sig = base64.b64encode(hashlib.sha256(
    body["ts"].encode() + body["nonce"].encode() + key.encode() + raw).digest()).decode()
req = u.Request("http://localhost:8000/api/platform/feishu/cmd", data=raw, method="POST",
                headers={"Content-Type": "application/json",
                         "X-Lark-Signature": sig})
try:
    print(u.urlopen(req, timeout=90).read().decode())
except u.HTTPError as e:
    err = e.read(4096).decode(errors="replace")
    print(f"code={e.code} err={err}")
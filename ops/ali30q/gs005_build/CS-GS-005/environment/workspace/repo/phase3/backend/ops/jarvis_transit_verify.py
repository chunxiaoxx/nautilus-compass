#!/usr/bin/env python3
"""贾维斯透传全链终验:真签名 im.message(status)→8092 callback→透传→平台 cmd。
期望:8092 返回 jarvis forwarded + 平台台账落行 + 用户飞书收到 status 快照。"""
import base64
import hashlib
import json
import os
import sys
import urllib.request as u
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ops.feishu_push import _load_env, CHAT_ID  # noqa: E402

_load_env()
key = os.environ["FEISHU_ENCRYPT_KEY"]
body = {
    "header": {"event_id": "evt-e2e-transit-915-02",
               "event_type": "im.message.receive_v1"},
    "event": {"message": {
        "chat_id": os.environ.get("FEISHU_CMD_CHAT_ID", CHAT_ID),
        "message_type": "text", "content": json.dumps({"text": "status"})}},
    "ts": "1757909999", "nonce": "n-transit-1",
}
raw = json.dumps(body).encode()
sig = base64.b64encode(hashlib.sha256(
    body["ts"].encode() + body["nonce"].encode() + key.encode() + raw).digest()).decode()
req = u.Request("http://127.0.0.1:8092/api/feishu/callback", data=raw, method="POST",
                headers={"Content-Type": "application/json",
                         "X-Lark-Signature": sig})
print("8092 resp:", u.urlopen(req, timeout=120).read().decode())

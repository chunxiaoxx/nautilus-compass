#!/usr/bin/env python3
"""贾维斯全链自测 v2(8092 全链 · 2026-09-15):模拟飞书带签名头事件打 8092。

与 v1 的区别:v1 直连平台端点且 ts/nonce 塞 payload(盲区来源);v2 走 8092
+ 三个 X-Lark 头,复刻真实飞书请求形状。仅验管道:真实 chat_id 仍需用户终验
(send_text 对自造会话会失败,预期 fail-soft warning,不崩)。
"""
import base64
import hashlib
import json
import os
import urllib.request

import sys
sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")

# 从云环境读 encrypt key(平台与 8092 同 key)
key = None
for line in open("/home/ubuntu/nautilus-mvp/phase3/backend/.env", encoding="utf-8"):
    if line.startswith("FEISHU_ENCRYPT_KEY="):
        key = line.split("=", 1)[1].strip()
        break
assert key, "FEISHU_ENCRYPT_KEY not found"

ts, nonce = "1757958900", "sc-nonce-v2"
event = {
    "header": {"event_id": "evt_selfcheckv20001", "event_type": "im.message.receive_v1"},
    "event": {"message": {
        "chat_id": "oc_selfcheck_fake_p2p", "chat_type": "p2p",
        "message_type": "text", "content": json.dumps({"text": "help"})}},
}
raw = json.dumps(event).encode()
sig = base64.b64encode(
    hashlib.sha256(ts.encode() + nonce.encode() + key.encode() + raw).digest()).decode()

req = urllib.request.Request(
    "http://127.0.0.1:8092/api/feishu/callback", data=raw, method="POST",
    headers={"Content-Type": "application/json", "X-Lark-Signature": sig,
             "X-Lark-Request-Timestamp": ts, "X-Lark-Request-Nonce": nonce})
with urllib.request.urlopen(req, timeout=120) as r:
    print("8092 resp:", r.status, r.read().decode()[:200])

# 查平台台账
import sqlite3
# 平台库位置从 env 或默认
db_path = "/home/ubuntu/nautilus-mvp/phase3/backend/nautilus_production.db"
if not os.path.exists(db_path):
    db_path = "/home/ubuntu/nautilus-mvp/phase3/backend/nautilus.db"
conn = sqlite3.connect(db_path)
rows = conn.execute(
    "SELECT trace_id, ack_note FROM org_mailbox WHERE trace_id LIKE 'feishu-cmd-%'"
    " ORDER BY id DESC LIMIT 3").fetchall()
print("ledger:", rows)
conn.close()

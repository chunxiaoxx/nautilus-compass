#!/usr/bin/env python3
"""贾维斯全链自测 v3(加密事件 · 2026-09-15):自加密 p2p 事件打 8092。

复刻 9/15 21:08 真实事件形状:body={"encrypt":...} + 三个 X-Lark 头。
验证:透传→平台验签(对密文 raw)→AES 解密→白名单→台账→响应体 reply+chat_id。
"""
import base64
import hashlib
import json
import sys
import urllib.request

sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")

key = None
for line in open("/home/ubuntu/nautilus-mvp/phase3/backend/.env", encoding="utf-8"):
    if line.startswith("FEISHU_ENCRYPT_KEY="):
        key = line.split("=", 1)[1].strip()
        break
assert key, "FEISHU_ENCRYPT_KEY not found"

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

inner = {
    "header": {"event_id": "evt_selfcheckv30001", "event_type": "im.message.receive_v1"},
    "event": {"message": {
        "chat_id": "oc_selfcheck_enc_p2p", "chat_type": "p2p",
        "message_type": "text", "content": json.dumps({"text": "help"})}},
}
aes_key = hashlib.sha256(key.encode()).digest()
plain = json.dumps(inner).encode()
pad_n = 16 - (len(plain) % 16)
padded = plain + bytes([pad_n]) * pad_n
enc = Cipher(algorithms.AES(aes_key), modes.CBC(aes_key[:16])).encryptor()
cipher_b64 = base64.b64encode(enc.update(padded) + enc.finalize()).decode()
raw = json.dumps({"encrypt": cipher_b64}).encode()

ts, nonce = "1757966000", "sc-nonce-v3"
sig = base64.b64encode(
    hashlib.sha256(ts.encode() + nonce.encode() + key.encode() + raw).digest()).decode()

req = urllib.request.Request(
    "http://127.0.0.1:8092/api/feishu/callback", data=raw, method="POST",
    headers={"Content-Type": "application/json", "X-Lark-Signature": sig,
             "X-Lark-Request-Timestamp": ts, "X-Lark-Request-Nonce": nonce})
with urllib.request.urlopen(req, timeout=120) as r:
    print("8092 resp:", r.status, r.read().decode()[:120])

import sqlite3  # noqa: E402
print("(台账以 psql 为准,此处略)")

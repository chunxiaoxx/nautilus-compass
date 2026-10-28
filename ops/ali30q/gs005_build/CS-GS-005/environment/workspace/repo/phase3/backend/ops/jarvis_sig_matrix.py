#!/usr/bin/env python3
"""签名算法矩阵:用 23:24:35 真实事件的实际值离线复算,找出与飞书 sig 匹配的串。"""
import ast
import base64
import hashlib
import json
import subprocess

# 从 journal 取 23:24 的 RAW 行
out = subprocess.run(
    ["sudo", "journalctl", "-u", "feishu-callback", "--since", "23:24",
     "--until", "23:25", "--no-pager"], capture_output=True, text=True).stdout
line = [l for l in out.splitlines() if "JARVIS-RAW" in l][0]
raw = ast.literal_eval(line.split("JARVIS-RAW ", 1)[1].strip())
payload = json.loads(raw.decode())
EK = "SbKwDDUcLE2bxuvMArRnJemrbSJoWr4o"
VT = "EQZkDmCLnvPvmfOtrJXPQblIdpjIQiVZ"
ts, nonce = "1789485873", "749987784"
target = "d10fc5dc89ce7ea0319e"

b64str = payload["encrypt"].encode()
combos = {
    "ts+nonce+EK+raw": ts + nonce + EK,
    "ts+nonce+VT+raw": ts + nonce + VT,
    "EK+ts+nonce+raw": EK + ts + nonce,
    "nonce+ts+EK+raw": nonce + ts + EK,
}
results = {}
for name, prefix in combos.items():
    data = prefix.encode() + raw
    if name == "ts+nonce+EK+b64":
        continue
    sig = base64.b64encode(hashlib.sha256(data).digest()).decode()
    results[name] = sig
    if sig.startswith(target[:8]):
        print(f"*** MATCH: {name} -> {sig}")

data = (ts + nonce + EK).encode() + b64str
sig = base64.b64encode(hashlib.sha256(data).digest()).decode()
results["ts+nonce+EK+b64"] = sig
if sig.startswith(target[:8]):
    print(f"*** MATCH: ts+nonce+EK+b64 -> {sig}")
data = raw + (ts + nonce + EK).encode()
sig = base64.b64encode(hashlib.sha256(data).digest()).decode()
results["raw+ts+nonce+EK"] = sig
if sig.startswith(target[:8]):
    print(f"*** MATCH: raw+ts+nonce+EK -> {sig}")
    sig = base64.b64encode(hashlib.sha256(data).digest()).decode()
    results[name] = sig
    if sig.startswith(target[:8]):
        print(f"*** MATCH: {name} -> {sig}")

print("target prefix:", target)
for k, v in results.items():
    print(f"{k}: {v[:24]}")
# 顺带:解密看看这条事件的 chat_id(确认是否 oc_e3db8f)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
aes_key = hashlib.sha256(EK.encode()).digest()
ct = base64.b64decode(payload["encrypt"])
dec = Cipher(algorithms.AES(aes_key), modes.CBC(ct[:16])).decryptor()
padded = dec.update(ct[16:]) + dec.finalize()
plain = json.loads(padded[:-padded[-1]])
msg = plain.get("event", {}).get("message", {})
print("chat_id:", msg.get("chat_id"), "chat_type:", msg.get("chat_type"),
      "text:", msg.get("content"), "event_id:", plain.get("header", {}).get("event_id"))

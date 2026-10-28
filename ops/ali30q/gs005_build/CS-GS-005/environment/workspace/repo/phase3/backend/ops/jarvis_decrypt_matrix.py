#!/usr/bin/env python3
"""对 22:49 真实密文跑解密算法矩阵(key×iv 变体)——定位飞书实际算法。"""
import ast
import base64
import hashlib
import json

line = open("/tmp/enc_body.txt").read().strip()
raw = ast.literal_eval(line)
if isinstance(raw, str):
    raw = raw.encode()
payload = json.loads(raw.decode())
ct = base64.b64decode(payload["encrypt"])
EK = "SbKwDDUcLE2bxuvMArRnJemrbSJoWr4o"
VT = "EQZkDmCLnvPvmfOtrJXPQblIdpjIQiVZ"

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

keys = {
    "sha256(EK)": hashlib.sha256(EK.encode()).digest(),
    "EK.pad32": EK.encode().ljust(32, b"\x00")[:32],
    "EK.pad32sp": EK.encode().ljust(32, b" ")[:32],
    "sha256(VT)": hashlib.sha256(VT.encode()).digest(),
    "VT.pad32": VT.encode().ljust(32, b"\x00")[:32],
    "md5x2(EK)": hashlib.md5(EK.encode()).digest() * 2,
    "sha256(EK.hex)": hashlib.sha256(
        hashlib.sha256(EK.encode()).hexdigest().encode()).digest(),
}
hits = []
for kn, k in keys.items():
    ivs = {"k[:16]": k[:16], "zero": b"\x00" * 16,
           "sha16": hashlib.sha256(k).digest()[:16]}
    for ivn, iv in ivs.items():
        try:
            dec = Cipher(algorithms.AES(k), modes.CBC(iv)).decryptor()
            padded = dec.update(ct) + dec.finalize()
            s = padded[:-padded[-1]].decode("utf-8", "replace")
            if s.lstrip()[:1] in "{[":
                hits.append((kn, ivn, s[:400]))
        except Exception:
            pass
print("HITS:", len(hits))
for kn, ivn, s in hits:
    print(f"[{kn} + {ivn}] -> {s}")

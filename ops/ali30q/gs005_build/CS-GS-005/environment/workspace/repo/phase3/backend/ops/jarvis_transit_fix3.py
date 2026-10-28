#!/usr/bin/env python3
"""贾维斯透传补充修复(8092 侧 · fix3):透传带全签名三元组。

飞书事件订阅签名 = base64(sha256(ts + nonce + key + body)),其中 ts/nonce 在
请求头 X-Lark-Request-Timestamp / X-Lark-Request-Nonce——首版透传只带了
X-Lark-Signature,缺 ts/nonce,真实事件到平台必挂验签(bad_sig)。
"""
P = "/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py"
src = open(P, encoding="utf-8").read()

old = '''                    headers={"Content-Type": "application/json",
                             "X-Lark-Signature": req.headers.get("x-lark-signature") or ""})'''
new = '''                    headers={"Content-Type": "application/json",
                             "X-Lark-Signature": req.headers.get("x-lark-signature") or "",
                             "X-Lark-Request-Timestamp": req.headers.get("x-lark-request-timestamp") or "",
                             "X-Lark-Request-Nonce": req.headers.get("x-lark-request-nonce") or ""})'''
assert old in src, "anchor missing"
src = src.replace(old, new, 1)
open(P, "w", encoding="utf-8", newline="\n").write(src)
import py_compile
py_compile.compile(P, doraise=True)
print("PATCHED+SYNTAX OK")

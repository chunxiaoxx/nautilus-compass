#!/usr/bin/env python3
"""贾维斯透传(8092 侧 · fix5):debug 行补签名头指示。

核验发现:8092 从不验签,v5 .env 无 ENCRYPT_KEY——飞书是否带 X-Lark-Signature
取决于后台 per-app Encrypt Key 配置,本地不可见。print 加 sig/ts 头指示,
用户实发一条即揭示真实签名状态(不猜,拿数据)。"""
P = "/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py"
src = open(P, encoding="utf-8").read()

old = '''        print("JARVIS-DEBUG et=%s chat_id=%s chat_type=%s msg_type=%s" % (
            _j_et, _j_msg.get("chat_id"), _j_msg.get("chat_type"),
            _j_msg.get("message_type")), flush=True)'''
new = '''        print("JARVIS-DEBUG et=%s chat_id=%s chat_type=%s msg_type=%s sig=%s ts=%s nonce=%s" % (
            _j_et, _j_msg.get("chat_id"), _j_msg.get("chat_type"),
            _j_msg.get("message_type"),
            "Y" if req.headers.get("x-lark-signature") else "N",
            "Y" if req.headers.get("x-lark-request-timestamp") else "N",
            "Y" if req.headers.get("x-lark-request-nonce") else "N"), flush=True)'''
assert old in src, "anchor missing"
src = src.replace(old, new, 1)
open(P, "w", encoding="utf-8", newline="\n").write(src)
import py_compile
py_compile.compile(P, doraise=True)
print("PATCHED OK")

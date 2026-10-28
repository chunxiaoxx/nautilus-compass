#!/usr/bin/env python3
"""贾维斯透传(8092 侧 · fix8):终验通过,清理逐事件 debug 打印。

保留 _j_et/_j_msg 变量(透传条件仍用),删 JARVIS-DEBUG/JARVIS-RAW 两处 print。
"""
P = "/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py"
src = open(P, encoding="utf-8").read()

old_block = '''        print("JARVIS-DEBUG et=%s chat_id=%s chat_type=%s msg_type=%s sig=%s ts=%s nonce=%s" % (
            _j_et, _j_msg.get("chat_id"), _j_msg.get("chat_type"),
            _j_msg.get("message_type"),
            "Y" if req.headers.get("x-lark-signature") else "N",
            "Y" if req.headers.get("x-lark-request-timestamp") else "N",
            "Y" if req.headers.get("x-lark-request-nonce") else "N"), flush=True)
        print("JARVIS-RAW %s" % raw, flush=True)'''
assert old_block in src, "debug block missing"
src = src.replace(old_block + "\n", "", 1)
open(P, "w", encoding="utf-8", newline="\n").write(src)
import py_compile
py_compile.compile(P, doraise=True)
print("CLEANED OK")

#!/usr/bin/env python3
"""贾维斯透传(8092 侧 · fix6):加密事件透传+raw 诊断+send_text 用响应 chat_id。

真实事件实测(9/15 21:08 journal):sig=Y ts=Y nonce=Y(签名头在,app 配了
Encrypt Key),但 et= chat_id=None——事件体疑似加密密文({"encrypt":...}),
8092 明文解析拿不到字段。本补丁:
A. debug 行后加 raw[:300] 打印(下次真实事件直接看形状,一锤定音)
B. 透传条件加 "encrypt" in body——密文事件也透传(白名单判定移平台,
   平台解密后统一判;验签对密文 raw 依然成立)
C. send_text 目标改用平台响应体回传的 chat_id(加密事件下本地无明文字段)
"""
P = "/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py"
src = open(P, encoding="utf-8").read()

# --- A: raw 诊断 ---
old_a = '''            "Y" if req.headers.get("x-lark-request-nonce") else "N"), flush=True)'''
new_a = '''            "Y" if req.headers.get("x-lark-request-nonce") else "N"), flush=True)
        print("JARVIS-RAW %s" % raw[:300], flush=True)'''
assert old_a in src, "A anchor missing"
src = src.replace(old_a, new_a, 1)

# --- B: 透传条件加密文事件 ---
old_b = '''        if (isinstance(body, dict) and isinstance(_j_msg, dict)
                and _j_msg.get("chat_type") == "p2p"
                and ("im.message.receive" in _j_et or not _j_et)):'''
new_b = '''        if (isinstance(body, dict)
                and (("encrypt" in body)  # 加密事件:平台解密后统一判白名单
                     or (isinstance(_j_msg, dict)
                         and _j_msg.get("chat_type") == "p2p"
                         and ("im.message.receive" in _j_et or not _j_et)))):'''
assert old_b in src, "B anchor missing"
src = src.replace(old_b, new_b, 1)

# --- C: send_text 用响应体 chat_id ---
old_c = '''                if isinstance(_rj, dict) and _rj.get("reply"):
                    try:
                        _, fpost2 = make_feishu_http()
                        send_text(_feishu_token(), str(_j_msg.get("chat_id")),
                                  str(_rj["reply"])[:4000], post=fpost2)'''
new_c = '''                if isinstance(_rj, dict) and _rj.get("reply"):
                    try:
                        _, fpost2 = make_feishu_http()
                        # 加密事件下本地无明文 chat_id,以平台响应体回传为准
                        _cid = str(_rj.get("chat_id") or _j_msg.get("chat_id") or "")
                        if _cid:
                            send_text(_feishu_token(), _cid,
                                      str(_rj["reply"])[:4000], post=fpost2)'''
assert old_c in src, "C anchor missing"
src = src.replace(old_c, new_c, 1)

open(P, "w", encoding="utf-8", newline="\n").write(src)
import py_compile
py_compile.compile(P, doraise=True)
print("PATCHED OK")

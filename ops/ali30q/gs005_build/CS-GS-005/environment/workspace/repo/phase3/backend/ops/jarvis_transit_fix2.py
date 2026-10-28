#!/usr/bin/env python3
"""贾维斯透传 v0.1 定谳修复(8092 侧 · 2026-09-15)。

诊断(用户实发消息 POST 200 但零透传):
- 首版条件锁 oc_c9fbb(哨兵 app 会话)永假——8092 是 scorer app,
  用户私聊 chat_id 是另一个值
- logger.info 从未进 journal(root logger 默认 WARNING,uvicorn 独立 logger)
  ——debug 行静默,叠加盲区

修:
A. debug 行换 print(绕过 logger 级别)+ 提取 _j_et/_j_msg 供条件复用
B. 条件改双 schema(新 header.event_type 或旧无 header)+ chat_type=="p2p"
C. 读平台响应体 reply,scorer 凭据 send_text 回原会话(哨兵凭据发不进 scorer 会话)
"""
import sys

P = "/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py"
src = open(P, encoding="utf-8").read()

# --- A: debug 行换 print + 变量提取(放 json.loads 后,challenge 前) ---
old_a = '        logger.info("jarvis-debug raw[:300]=%s", raw[:300])'
new_a = '''        _j_ev = body.get("event") if isinstance(body, dict) else None
        _j_msg = (_j_ev.get("message") if isinstance(_j_ev, dict) else None) or {}
        _j_et = ((body.get("header") or {}).get("event_type") or "") if isinstance(body, dict) else ""
        print("JARVIS-DEBUG et=%s chat_id=%s chat_type=%s msg_type=%s" % (
            _j_et, _j_msg.get("chat_id"), _j_msg.get("chat_type"),
            _j_msg.get("message_type")), flush=True)'''
assert old_a in src, "A anchor missing"
src = src.replace(old_a, new_a, 1)

# --- B: 透传条件改双 schema + p2p ---
old_b = '''        if (isinstance(body, dict)
                and (body.get("header") or {}).get("event_type") == "im.message.receive_v1"
                and (((body.get("event") or {}).get("message")) or {}).get("chat_id")
                == "oc_c9fbb71be60e8d64fb0c854078b05847"):'''
new_b = '''        if (isinstance(body, dict) and isinstance(_j_msg, dict)
                and _j_msg.get("chat_type") == "p2p"
                and ("im.message.receive" in _j_et or not _j_et)):'''
assert old_b in src, "B anchor missing"
src = src.replace(old_b, new_b, 1)

# --- C: 响应体回执(send_text 回原会话) ---
old_c = '''                with _rq.urlopen(_req, timeout=90) as _resp:
                    logger.info("jarvis transit resp=%s", _resp.status)
                return {"code": 0, "note": "jarvis forwarded"}'''
new_c = '''                with _rq.urlopen(_req, timeout=120) as _resp:
                    _rbody = _resp.read().decode("utf-8", "replace")
                try:
                    _rj = _json.loads(_rbody)
                except Exception:
                    _rj = {}
                if isinstance(_rj, dict) and _rj.get("reply"):
                    try:
                        _, fpost2 = make_feishu_http()
                        send_text(_feishu_token(), str(_j_msg.get("chat_id")),
                                  str(_rj["reply"])[:4000], post=fpost2)
                    except Exception as e:  # noqa: BLE001 — 回执失败不抹透传结果
                        logger.warning("jarvis reply send err: %s", e)
                return {"code": 0, "note": "jarvis forwarded"}'''
assert old_c in src, "C anchor missing"
src = src.replace(old_c, new_c, 1)

open(P, "w", encoding="utf-8", newline="\n").write(src)
print("PATCHED OK")
# 自检:语法+关键标记
import py_compile
py_compile.compile(P, doraise=True)
for mark in ('chat_type") == "p2p"', "JARVIS-DEBUG", "_rj.get(\"reply\")"):
    assert mark in open(P, encoding="utf-8").read(), f"mark missing: {mark}"
print("SYNTAX+MARKS OK")

#!/usr/bin/env python3
"""贾维斯透传修复(8092 侧 · fix4):变量提取块挪到 body 赋值后。

fix2 的锚点在 json.loads 之前(debug 行原位),UnboundLocalError——
全链自测 jarvis_e2e_check2 抓出。"""
P = "/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py"
src = open(P, encoding="utf-8").read()

bad_block = '''        _j_ev = body.get("event") if isinstance(body, dict) else None
        _j_msg = (_j_ev.get("message") if isinstance(_j_ev, dict) else None) or {}
        _j_et = ((body.get("header") or {}).get("event_type") or "") if isinstance(body, dict) else ""
        print("JARVIS-DEBUG et=%s chat_id=%s chat_type=%s msg_type=%s" % (
            _j_et, _j_msg.get("chat_id"), _j_msg.get("chat_type"),
            _j_msg.get("message_type")), flush=True)'''
assert bad_block in src, "bad block missing (already fixed?)"

# 1) 删错位块(回滚到无 debug 状态)
src = src.replace(bad_block + "\n", "", 1)
# 2) 插到 body 赋值之后
anchor = "        intent = parse_event(body)\n"
assert anchor in src, "anchor missing"
src = src.replace(anchor, bad_block + "\n" + anchor, 1)
open(P, "w", encoding="utf-8", newline="\n").write(src)
import py_compile
py_compile.compile(P, doraise=True)
# 3) 顺序自检:print 行必须在 body 赋值之后
lines = open(P, encoding="utf-8").read().splitlines()
i_body = next(i for i, l in enumerate(lines) if "body = _json.loads(raw)" in l)
i_print = next(i for i, l in enumerate(lines) if "JARVIS-DEBUG" in l)
assert i_print > i_body, f"order wrong: print@{i_print} <= body@{i_body}"
print(f"PATCHED OK (body@{i_body} < print@{i_print})")

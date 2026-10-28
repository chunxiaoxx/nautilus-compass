#!/usr/bin/env python3
"""贾维斯透传(8092 侧 · fix7):JARVIS-RAW 打全量密文([:300]曾截断,无法离线解密复盘)。"""
P = "/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py"
src = open(P, encoding="utf-8").read()
old = '        print("JARVIS-RAW %s" % raw[:300], flush=True)'
new = '        print("JARVIS-RAW %s" % raw, flush=True)'
assert old in src, "anchor missing"
src = src.replace(old, new, 1)
open(P, "w", encoding="utf-8", newline="\n").write(src)
import py_compile
py_compile.compile(P, doraise=True)
print("PATCHED OK")

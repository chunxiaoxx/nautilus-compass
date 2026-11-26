#!/usr/bin/env python3
"""mcp_server.py:默认项目判定(resolve_project 的兜底扫描)加 60 秒缓存。

为什么(2026-11-27 云上实测):不指定 project 的每次 recall,服务端都遍历全部项目目录并 stat
每个记忆文件找"最近修改"——12,167 个目录 / 61,518 次 stat / 2.76 秒。这是 MCP 召回
"3 秒左右"的主因(嵌入挪回本地后仍在)。

对目标文件做三处锚定插入,每个锚点必须恰好出现一次;先备份;保留原行尾。
用法:python ops/mcp_default_project_cache_patch.py <mcp_server.py 路径> [--check-only]
"""
import hashlib
import json
import os
import sys

TARGET = sys.argv[1]
CHECK_ONLY = "--check-only" in sys.argv
raw = open(TARGET, "rb").read()
text = raw.decode("utf-8")
crlf = "\r\n" in text
text = text.replace("\r\n", "\n")

HELPERS = '''# 2026-11-27 · 默认项目判定的短时缓存。原实现每次调用都遍历全部项目目录并 stat 每个记忆文件
# 找"最近修改"(云上实测 12,167 个目录 / 61,518 次 stat / 2.76 秒)——不指定 project 的每次
# recall 都先付这 2.76 秒。默认项目一分钟内变不变没有业务后果,缓存 TTL 内复用上一次结果。
# 缓存键带项目根目录路径:换根目录(测试 / 多实例)不串台。
_DEFAULT_PROJECT_TTL_S = 60.0
_DEFAULT_PROJECT_CACHE = ("", 0.0, None)


def _default_project_cached(now: float, root) -> str | None:
    key, stamp, name = _DEFAULT_PROJECT_CACHE
    return name if (name and key == str(root) and now - stamp < _DEFAULT_PROJECT_TTL_S) else None


def _default_project_remember(now: float, root, name) -> None:
    global _DEFAULT_PROJECT_CACHE
    _DEFAULT_PROJECT_CACHE = (str(root), now, name)


'''

A_DEF = 'def resolve_project(explicit: str | None) -> str | None:\n'
A_EXISTS = '    if not PROJECTS_DIR.exists():\n        return None\n'
A_RETURN = '        if mtime > best_mtime:\n            best, best_mtime = d.name, mtime\n    return best\n'


def once(needle, label):
    count = text.count(needle)
    if count != 1:
        print(json.dumps({"ok": False, "anchor": label, "count": count}, ensure_ascii=False))
        sys.exit(2)


once(A_DEF, "def")
once(A_EXISTS, "exists-check")
once(A_RETURN, "return-best")
if "_DEFAULT_PROJECT_TTL_S" in text:
    print(json.dumps({"ok": True, "already_applied": True}))
    sys.exit(0)

text = text.replace(A_DEF, HELPERS + A_DEF)
text = text.replace(A_EXISTS, A_EXISTS
                    + "    cached = _default_project_cached(time.time(), PROJECTS_DIR)\n"
                    + "    if cached is not None:\n        return cached\n")
text = text.replace(A_RETURN, '        if mtime > best_mtime:\n            best, best_mtime = d.name, mtime\n'
                              "    _default_project_remember(time.time(), PROJECTS_DIR, best)\n    return best\n")
compile(text, TARGET, "exec")
if CHECK_ONLY:
    print(json.dumps({"ok": True, "check_only": True}))
    sys.exit(0)

backup = TARGET + ".bak-20261127-defaultproj"
with open(backup, "wb") as handle:
    handle.write(raw)
out = text.replace("\n", "\r\n") if crlf else text
tmp = TARGET + ".tmp"
with open(tmp, "wb") as handle:
    handle.write(out.encode("utf-8"))
os.replace(tmp, TARGET)
print(json.dumps({"ok": True, "backup": os.path.basename(backup),
                  "sha_before": hashlib.sha256(raw).hexdigest()[:12],
                  "sha_after": hashlib.sha256(open(TARGET, "rb").read()).hexdigest()[:12]}))

#!/usr/bin/env python3
"""V7 daemon 3 patches · 2026-05-19 · compass-dialog ship.

F4 body_fallback · v7tool_compass_ingest_obs body 空 / <10 → auto-fallback
F5 tool_name_alias · v7tool_mcp_exec compass_ingest → compass_ingest_obs
F6 verbatim_error · LLM prompt 加 "verbatim 引 server error 再归因" 规则
"""
import shutil
import sys
import time

PATH = "/usr/local/bin/v7-telegram-daemon.py"

with open(PATH) as f:
    src = f.read()

ts = time.strftime("%Y%m%d_%H%M%S")
backup = f"{PATH}.bak.{ts}"
shutil.copy(PATH, backup)
print(f"backup: {backup}")

# ── Patch F4: body fallback in v7tool_compass_ingest_obs ──
old1 = (
    'def v7tool_compass_ingest_obs(name: str, body: str, drift: str = "green", type_: str = "discovery") -> dict:\n'
    '    """V7 真写 compass · 留自己的记忆"""\n'
    '    try:\n'
    '        payload = json.dumps({'
)
new1 = (
    'def v7tool_compass_ingest_obs(name: str, body: str, drift: str = "green", type_: str = "discovery") -> dict:\n'
    '    """V7 真写 compass · 留自己的记忆"""\n'
    '    # _PATCH_V7_F4_BODY_FALLBACK_2026_05_19 · server min 10 chars · LLM 偶漏 body · fallback 防 ingest 全废\n'
    '    if not body or len(body.strip()) < 10:\n'
    '        body = f"V7 cron tick · body missing/short · auto-fallback · name={name[:80]} · ts={int(time.time())}"\n'
    '    try:\n'
    '        payload = json.dumps({'
)
if old1 not in src:
    print("ERR · F4 pattern not found · abort")
    sys.exit(1)
src = src.replace(old1, new1, 1)
assert "_PATCH_V7_F4_BODY_FALLBACK_2026_05_19" in src, "F4 apply failed"
print("F4 body_fallback · applied")

# ── Patch F5: tool name alias in v7tool_mcp_exec ──
old2 = (
    'def v7tool_mcp_exec(tool_name, args=None):\n'
    '    # _PATCH_V7_F3_MCP_INIT_AUTHZ_2026_05_19 mcp_server 要求 initialize + authToken handshake\n'
    '    try:\n'
    '        import socket as _sock\n'
    '        args = args or {}'
)
new2 = (
    'def v7tool_mcp_exec(tool_name, args=None):\n'
    '    # _PATCH_V7_F3_MCP_INIT_AUTHZ_2026_05_19 mcp_server 要求 initialize + authToken handshake\n'
    '    # _PATCH_V7_F5_TOOL_NAME_ALIAS_2026_05_19 · LLM 偶拼错 compass_ingest · 真名 compass_ingest_obs\n'
    '    _MCP_TOOL_ALIAS = {\n'
    '        "compass_ingest": "compass_ingest_obs",\n'
    '        "ingest_obs": "compass_ingest_obs",\n'
    '    }\n'
    '    if tool_name in _MCP_TOOL_ALIAS:\n'
    '        tool_name = _MCP_TOOL_ALIAS[tool_name]\n'
    '    try:\n'
    '        import socket as _sock\n'
    '        args = args or {}'
)
if old2 not in src:
    print("ERR · F5 pattern not found · abort")
    sys.exit(1)
src = src.replace(old2, new2, 1)
assert "_PATCH_V7_F5_TOOL_NAME_ALIAS_2026_05_19" in src, "F5 apply failed"
print("F5 tool_name_alias · applied")

# ── Patch F6: LLM prompt · verbatim 引 server error 再归因 ──
old3 = '  · 真做事 · 调 tool · 最多 15 轮.'
new3 = (
    '  · 真做事 · 调 tool · 最多 15 轮.\n'
    '  · _PATCH_V7_F6_VERBATIM_ERROR_2026_05_19 · tool 返回 error/ok:false 时 · 必先 verbatim 引证 server error message · 再归因·不准脑补 "session_id 格式错"/"token 错"/"unauthorized" · INNER 5 天误读真案'
)
if old3 not in src:
    print("ERR · F6 pattern not found · abort")
    sys.exit(1)
src = src.replace(old3, new3, 1)
assert "_PATCH_V7_F6_VERBATIM_ERROR_2026_05_19" in src, "F6 apply failed"
print("F6 verbatim_error · applied")

with open(PATH, "w") as f:
    f.write(src)

print(f"\nall 3 patches applied · {PATH} · backup {backup}")

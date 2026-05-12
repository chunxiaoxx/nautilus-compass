#!/usr/bin/env python3
"""Idempotent patch · add `Connection: close` header to /v1/v14/* responses.

Why: V5/V6 call recall+ingest_obs every 10-15 min · gap far > any reasonable
keep-alive (75s shipped earlier). Server-side closes idle conn · client httpx
pool still thinks it's reusable · next call hits closed conn → RemoteProtocolError.

Fix: tell client to close after each /v1/v14/* response · V5 httpx honors
HTTP/1.1 Connection: close · drops pool entry · next call fresh TCP.

drift_check (high-freq) unchanged · keeps keep-alive pooling for perf.

This complements --timeout-keep-alive 75 · doesn't replace it. Combined:
- /v1/drift_check  : high-freq · pool reuse OK · keep-alive 75s safety net
- /v1/v14/recall   : low-freq · forced new TCP each call · 0 race
- /v1/v14/ingest_obs: low-freq · forced new TCP each call · 0 race
"""
import pathlib
import sys

UNIT = pathlib.Path("/home/ubuntu/compass/compass_http_v09.py")
NEEDLE = '    response = await call_next(request)\n    response.headers["X-Request-Id"] = rid'
PATCH = '''    response = await call_next(request)
    # v15 · Connection: close for low-freq /v1/v14/* paths · prevents
    # 10-15min idle race between V5 httpx pool and uvicorn keep-alive
    if path.startswith("/v1/v14/"):
        response.headers["Connection"] = "close"
    response.headers["X-Request-Id"] = rid'''

t = UNIT.read_text()
if 'response.headers["Connection"] = "close"' in t:
    print("already-patched · no-op")
    sys.exit(0)
if NEEDLE not in t:
    print("ERR: needle not found · manual patch required", file=sys.stderr)
    sys.exit(1)
new = t.replace(NEEDLE, PATCH, 1)
UNIT.write_text(new)
print("patched · /v1/v14/* now sends Connection: close")

# AST validate
import ast
try:
    ast.parse(new)
    print("ast.parse OK")
except SyntaxError as e:
    print(f"AST FAIL · rollback advised: {e}", file=sys.stderr)
    sys.exit(2)

#!/usr/bin/env python3
"""Idempotent patch · add --timeout-keep-alive 75 to compass.service ExecStart.

Why: V5/V6 httpx (via httpcore process-level pool) reuse TCP idle > 5s
uvicorn default `--timeout-keep-alive 5` closes idle conn · client next req
hits closed conn mid-send → RemoteProtocolError: Server disconnected.

drift_check is high-freq so idle never crosses 5s · recall/ingest_obs are
low-freq so cross 5s · symptomatic at low-freq endpoints.

Fix: server-side --timeout-keep-alive 75 (nginx/ELB industry default).
"""
import pathlib
import sys

UNIT = pathlib.Path("/etc/systemd/system/compass.service")
NEEDLE = "--workers 4 \\"
INSERT = "--workers 4 \\\n    --timeout-keep-alive 75 \\"

t = UNIT.read_text()
if "--timeout-keep-alive" in t:
    print("already-patched · no-op")
    sys.exit(0)
if NEEDLE not in t:
    print("ERR: needle not found · manual patch required", file=sys.stderr)
    sys.exit(1)
new = t.replace(NEEDLE, INSERT, 1)
UNIT.write_text(new)
print("patched")

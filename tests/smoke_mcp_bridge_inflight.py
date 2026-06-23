#!/usr/bin/env python3
"""v1.9 end-to-end smoke (real localhost sockets · zero外网).

Proves: a tools/call sent to cloud over conn1 that the cloud receives but never
replies to (dropped mid-flight) IS re-sent over conn2 after the initialize
replay. This is the gap v1.8 left open (it only replayed initialize, lost the
in-flight request). Run: python tests/smoke_mcp_bridge_inflight.py
"""
from __future__ import annotations

import importlib
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
os.environ.setdefault("COMPASS_CLOUD_TOKEN", "smoke-token")
bridge = importlib.import_module("ops.mcp_stdio_to_cloud")

HOST = "127.0.0.1"
received = {"conn1": [], "conn2": []}

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind((HOST, 0))
srv.listen(2)
PORT = srv.getsockname()[1]


def _reply(msg_id):
    return (json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": {"ok": True}}) + "\n").encode()


def server():
    # conn1 · real initialize + a tools/call that we deliberately never answer
    c1, _ = srv.accept()
    f1 = c1.makefile("rb")
    received["conn1"].append(f1.readline())          # initialize
    c1.sendall(_reply(1))                             # answer initialize
    received["conn1"].append(f1.readline())           # tools/call (id=2)
    c1.close()                                         # DROP before replying → in-flight lost

    # conn2 · reconnect: replayed initialize, then the re-sent tools/call
    c2, _ = srv.accept()
    f2 = c2.makefile("rb")
    received["conn2"].append(f2.readline())           # replayed initialize
    c2.sendall(_reply(1))                              # swallowed by _recv_one_line
    received["conn2"].append(f2.readline())           # re-sent tools/call (id=2)
    c2.sendall(_reply(2))
    c2.close()


t = threading.Thread(target=server, daemon=True)
t.start()


def opener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.settimeout(None)
    return s


link = bridge._CloudLink(opener=opener)
init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
link.note_outgoing(init)
link.connect(replay=False)
link.send(bridge._inject_auth(init))                  # real initialize over conn1

call = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"recall"}}'
out = bridge._inject_auth(call)
link.send(out)
link.note_request(out)                                # track in-flight
time.sleep(0.3)                                        # let server read conn1 + drop

link.mark_down()                                       # detect drop
link.connect(replay=True)                              # reconnect → replay init + re-send pending
time.sleep(0.3)

t.join(timeout=2)


def _has_id2(frames):
    for r in frames:
        try:
            m = json.loads(r.decode().strip())
        except Exception:
            continue
        if m.get("id") == 2 and m.get("method") == "tools/call":
            return True
    return False


assert _has_id2(received["conn1"]), f"conn1 should have received the tools/call: {received['conn1']}"
assert _has_id2(received["conn2"]), f"FAIL · in-flight tools/call NOT re-sent on reconnect: {received['conn2']}"

# Drive the reply-clearing path (what _pump_cloud_to_out does live): read the
# re-sent call's reply off conn2 and note it → pending clears (full round-trip).
sock = link.current()
sock.settimeout(2.0)
buf = b""
while b"\n" not in buf:
    chunk = sock.recv(65536)
    if not chunk:
        break
    buf += chunk
for cl in buf.split(b"\n"):
    if cl.strip():
        link.note_reply(cl.decode("utf-8", errors="replace"))

assert not link.pending_lines(), f"pending should clear after the re-sent call is acked: {link.pending_lines()}"
print("SMOKE PASS · v1.9 · 在途 tools/call 在 conn1 丢失 → conn2 重连后重发 + reply 销账成功")

"""recall_with_fallback — query the T4 GPU daemon first, fall back to the CPU
server on connection failure (Phase 0 Task 4 of the cloud-substrate plan).

The cloud topology runs a spot T4 GPU daemon (fast reranked recall) plus a
persistent CPU server (cold standby). When the spot T4 is preempted or
unreachable, the client must transparently fall back to the CPU server so recall
never hard-fails. A daemon that is reachable but returns ok=False (a query-level
error) is NOT a connection failure and does not trigger fallback.

Protocol mirrors recall.try_daemon_recall: newline-delimited JSON over TCP to
the daemon's (host, 9876).
"""
from __future__ import annotations

import json
import os
import socket

# exceptions that mean "this endpoint is down / unreachable" -> try the next one
_CONN_ERRORS = (ConnectionError, socket.timeout, TimeoutError, OSError)


def call_endpoint(host, port, query, project, top_k=8, action="recall", timeout=60.0):
    """One round-trip to a compass daemon. Raises on connection failure."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        req = {"action": action, "query": query[:2000], "project": project, "top_k": top_k}
        if action != "ping":  # v3.0.10 · daemon 9876 token auth (ping exempt)
            try:
                with open(os.path.expanduser("~/.claude/.cache/compass_daemon_token"),
                          encoding="utf-8") as _tf:
                    req["token"] = _tf.read().strip()
            except OSError:
                pass
        s.sendall(json.dumps(req, ensure_ascii=False).encode("utf-8") + b"\n")
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    line, _, _ = buf.partition(b"\n")
    return json.loads(line.decode("utf-8"))


def recall_with_fallback(query, project, primary, fallback, top_k=8,
                         action="recall", caller=call_endpoint):
    """Try `primary` (host, port); on connection failure try `fallback`.

    Returns the daemon response dict annotated with `served_by` in
    {"primary", "fallback", None}. Never raises on connection failure — returns
    {"ok": False, "served_by": None, "error": ...} when every endpoint is down.
    """
    endpoints = [("primary", primary)]
    if fallback:
        endpoints.append(("fallback", fallback))

    last_err = None
    for label, ep in endpoints:
        host, port = ep
        try:
            res = caller(host, port, query=query, project=project, top_k=top_k, action=action)
        except _CONN_ERRORS as e:
            last_err = f"{label} {host}:{port} unreachable: {type(e).__name__}: {e}"
            continue
        res = dict(res)
        res["served_by"] = label
        return res

    return {"ok": False, "served_by": None, "error": last_err or "no endpoint reachable"}

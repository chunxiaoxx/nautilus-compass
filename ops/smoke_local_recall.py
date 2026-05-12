#!/usr/bin/env python3
"""Smoke recall latency · local GPU daemon · cold + warm."""
import json
import socket
import sys
import time


def call_recall(query, top_k=3, timeout=180):
    t0 = time.time()
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9876))
    req = {"action": "recall", "query": query, "project": "C--Users-chunx", "top_k": top_k}
    s.sendall((json.dumps(req) + "\n").encode("utf-8"))
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c:
            break
        buf += c
    s.close()
    d = json.loads(buf.decode("utf-8"))
    dt_ms = (time.time() - t0) * 1000
    hits = len(d.get("recall", []))
    return dt_ms, hits


def main():
    print("cold (indexes 762 files) ...", flush=True)
    dt, n = call_recall("compass MCP fix today")
    print(f"cold = {dt/1000:.1f}s · hits={n}")
    for q in ["V5 stake age", "BGE GPU local", "session search"]:
        dt, n = call_recall(q, timeout=30)
        print(f"warm = {dt:.0f}ms · hits={n} · {q}")


if __name__ == "__main__":
    sys.exit(main())

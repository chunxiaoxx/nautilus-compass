#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9876 索引暖机循环:逐批烧 _EMBED_BUDGET 直至 coverage 全量(重启后 J4 前置件)。"""
import json
import socket
import sys
import time
from pathlib import Path

TOKEN = (Path.home() / ".claude" / ".cache" / "compass_daemon_token").read_text(encoding="utf-8").strip()
PROJ = "C--Users-chunx-Projects-nautilus-compass"


def req(p, timeout=600.0):
    p["token"] = TOKEN
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(("127.0.0.1", 9876))
        s.sendall(json.dumps(p, ensure_ascii=False).encode("utf-8") + b"\n")
        buf = b""
        while b"\n" not in buf:
            c = s.recv(65536)
            if not c:
                break
            buf += c
    return json.loads(buf.decode("utf-8"))


def main():
    deadline = time.time() + 40 * 60
    i = 0
    while time.time() < deadline:
        i += 1
        try:
            r = req({"action": "dedup_check", "project": PROJ,
                     "text": f"warmup pass {i} · index coverage driver"})
        except Exception as e:
            print(f"[{i}] conn fail: {e}", flush=True)
            time.sleep(10)
            continue
        cov = r.get("coverage") or {}
        emb, tot = cov.get("embedded", -1), cov.get("total", -1)
        print(f"[{i}] coverage {emb}/{tot}", flush=True)
        if 0 <= emb == tot:
            print("WARM: FULL", flush=True)
            return 0
    print("WARM: TIMEOUT", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A100 rerank 隧道(R452): 本机 127.0.0.1:19879 → A100 127.0.0.1:9879。

paramiko direct-tcpip 双向 pump,凭据走 a100_env(不落仓),断线自动重建 transport。
daemon 侧接法: COMPASS_RERANK_REMOTE=127.0.0.1:19879。
用法: python tools/a100_rerank_tunnel.py   (前台;watchdog 化候 systemd/nssm)
"""
from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paramiko  # noqa: E402


def load_env() -> dict:
    env = {}
    f = Path.home() / ".claude" / ".cache" / "a100_env"
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env

LOCAL_PORT = 19879
REMOTE_ADDR = ("127.0.0.1", 9879)


def connect_transport() -> paramiko.Transport:
    env = load_env()
    last = None
    for attempt in range(3):
        try:
            t = paramiko.Transport((env["A100_HOST"], int(env["A100_PORT"])))
            t.connect(username=env["A100_USER"], password=env["A100_PW"])
            print(f"[tunnel] transport up ({attempt + 1} tries)", flush=True)
            return t
        except Exception as e:
            last = e
            time.sleep(2 ** attempt)
    raise last


def pump(a: socket.socket, b: socket.channel):
    try:
        while True:
            data = a.recv(16384)
            if not data:
                break
            b.sendall(data)
    except Exception:
        pass
    finally:
        try:
            a.close()
        except Exception:
            pass
        try:
            b.close()
        except Exception:
            pass


def handle_client(sock: socket.socket, transport_box: list):
    transport = transport_box[0]
    try:
        chan = transport.open_channel("direct-tcpip", REMOTE_ADDR, sock.getpeername())
    except Exception as e:
        print(f"[tunnel] open_channel fail: {e} · reconnecting", flush=True)
        transport_box[0] = connect_transport()
        try:
            chan = transport_box[0].open_channel("direct-tcpip", REMOTE_ADDR, sock.getpeername())
        except Exception as e2:
            print(f"[tunnel] retry fail: {e2}", flush=True)
            sock.close()
            return
    t1 = threading.Thread(target=pump, args=(sock, chan), daemon=True)
    t2 = threading.Thread(target=pump, args=(chan, sock), daemon=True)
    t1.start()
    t2.start()
    t1.join()


def main():
    box = [connect_transport()]
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", LOCAL_PORT))
    srv.listen(8)
    print(f"[tunnel] listening 127.0.0.1:{LOCAL_PORT} -> A100:{REMOTE_ADDR[1]}", flush=True)
    while True:
        try:
            sock, _ = srv.accept()
            threading.Thread(target=handle_client, args=(sock, box), daemon=True).start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[tunnel] accept loop: {e}", flush=True)
            time.sleep(2)
            if not box[0].is_active():
                box[0] = connect_transport()


if __name__ == "__main__":
    main()

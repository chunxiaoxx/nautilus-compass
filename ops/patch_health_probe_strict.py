#!/usr/bin/env python3
"""v1.5.7 · /compass/health probe must require real response bytes.

Bug: sshd reverse tunnel binds port even if local-end dead.
TCP connect succeeds. send goes through. recv returns 0 bytes (EOF).
Old probe returned reachable=True · false positive.

Fix: require recv > 0 bytes to call it reachable.
"""
import pathlib
import sys


TARGET = pathlib.Path("/home/ubuntu/compass/compass_http_v09.py")

OLD = '''    def _probe_daemon(host, port, timeout=2.0):
        s = _sk.socket()
        s.settimeout(timeout)
        t0 = _t.time()
        try:
            s.connect((host, port))
            # send no-op recall · zero result is OK · we only check TCP alive
            s.sendall(b\'{"action":"healthcheck"}\\n\')
            try:
                _ = s.recv(4096)
            except Exception:
                pass
            return {"reachable": True, "latency_ms": int((_t.time()-t0)*1000)}'''

NEW = '''    def _probe_daemon(host, port, timeout=2.0):
        s = _sk.socket()
        s.settimeout(timeout)
        t0 = _t.time()
        try:
            s.connect((host, port))
            s.sendall(b\'{"action":"healthcheck"}\\n\')
            try:
                r = s.recv(4096)
            except Exception:
                r = b""
            # v1.5.7 · require >=1 byte response · sshd reverse tunnel
            # accepts connect but local-end-dead returns recv=0 · this
            # distinguishes "TCP reachable" from "daemon actually answering"
            if not r:
                return {"reachable": False,
                        "latency_ms": int((_t.time()-t0)*1000),
                        "error": "connected but no response (local end down?)"}
            return {"reachable": True,
                    "latency_ms": int((_t.time()-t0)*1000),
                    "resp_bytes": len(r)}'''


def main() -> int:
    t = TARGET.read_text()
    if 'v1.5.7' in t and 'resp_bytes' in t:
        print("already-patched · no-op")
        return 0
    if OLD not in t:
        print("ERR · _probe_daemon shape changed · cannot find marker", file=sys.stderr)
        return 1
    t = t.replace(OLD, NEW, 1)
    TARGET.write_text(t)
    print("patched · probe now requires real response")

    import ast
    try:
        ast.parse(t)
        print("AST OK")
    except SyntaxError as e:
        print(f"AST FAIL · {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Cloud-side patch · 3-tier BGE fallback architecture.

Architecture after this patch:
    Local Windows GTX 1060 (BGE GPU) · listens on local 127.0.0.1:9876
        |
        +-- ssh -fN -R 9876:127.0.0.1:9876 cloud   (reverse tunnel · auto-keepalive)
        |
    cloud 127.0.0.1:9876   ← reverse tunnel endpoint · cloud sees local daemon here
    cloud 127.0.0.1:9886   ← cloud CPU BGE daemon · fallback when local PC off

mcp_server.daemon_call + http_v09._call_v14_daemon retry ladder:
    1. try 9876  (local GPU · 30-80ms · preferred)
    2. try 9886  (cloud CPU · 1-3s · fallback)
    3. raise / return None  (final fallback: jaccard already exists in http_v09)

Idempotent · safe to re-run.
"""
import pathlib
import sys


MCP_SERVER = pathlib.Path("/home/ubuntu/nautilus-compass/mcp_server.py")
HTTP_V09   = pathlib.Path("/home/ubuntu/compass/compass_http_v09.py")
SYSTEMD_BGE = pathlib.Path("/etc/systemd/system/compass-bge-daemon.service")


def patch_mcp_server() -> str:
    """Change DAEMON_PORT = 9876 (single) to DAEMON_PORTS = [9876, 9886] with retry."""
    t = MCP_SERVER.read_text()
    if "DAEMON_PORTS" in t:
        return "mcp_server.py · already-patched"

    # Add DAEMON_PORTS constant
    t = t.replace(
        "DAEMON_PORT = 9876",
        "DAEMON_PORT = 9876\n# v1.5.3 · 3-tier fallback ladder\nDAEMON_PORTS = [9876, 9886]"
    )

    # Replace daemon_call body to iterate over ports
    old_call = """def daemon_call(req: dict, timeout: float = DAEMON_TIMEOUT) -> dict:
    \"\"\"Send JSON request to BGE daemon · return parsed reply.

    Raises socket.error / json.JSONDecodeError on transport failure.

    v1.3 · forwards COMPASS_AGENT_TYPE env to daemon for per-agent L2
    evidence in verification_log.jsonl (#104).
    \"\"\"
    if "agent_type" not in req:
        env_agent = os.environ.get("COMPASS_AGENT_TYPE")
        if env_agent:
            req = {**req, "agent_type": env_agent}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((DAEMON_HOST, DAEMON_PORT))
        s.sendall((json.dumps(req) + "\\n").encode("utf-8"))
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\\n"):
                break
        return json.loads(buf.decode("utf-8"))
    finally:
        s.close()"""

    new_call = """def daemon_call(req: dict, timeout: float = DAEMON_TIMEOUT) -> dict:
    \"\"\"Send JSON request to BGE daemon · return parsed reply.

    v1.5.3 · iterate DAEMON_PORTS [9876, 9886] · local GPU first, cloud CPU
    fallback. Returns first successful response. Raises last error if all fail.

    v1.3 · forwards COMPASS_AGENT_TYPE env to daemon (#104).
    \"\"\"
    if "agent_type" not in req:
        env_agent = os.environ.get("COMPASS_AGENT_TYPE")
        if env_agent:
            req = {**req, "agent_type": env_agent}
    last_err = None
    for port in DAEMON_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((DAEMON_HOST, port))
            s.sendall((json.dumps(req) + "\\n").encode("utf-8"))
            buf = b""
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
                if buf.endswith(b"\\n"):
                    break
            return json.loads(buf.decode("utf-8"))
        except (ConnectionRefusedError, OSError) as e:
            last_err = e
            continue
        finally:
            s.close()
    raise last_err if last_err else OSError("no daemon reachable")"""

    if old_call not in t:
        return "mcp_server.py · daemon_call shape changed · manual review needed"

    t = t.replace(old_call, new_call)
    MCP_SERVER.write_text(t)
    return "mcp_server.py · patched"


def patch_http_v09() -> str:
    """Change _call_v14_daemon to iterate ports."""
    t = HTTP_V09.read_text()
    if "_V14_PORTS" in t:
        return "compass_http_v09.py · already-patched"

    # Add ports list right after _V14_PORT
    t = t.replace(
        '_V14_PORT = int(_v14_os.environ.get("COMPASS_BGE_PORT", "9876"))',
        '_V14_PORT = int(_v14_os.environ.get("COMPASS_BGE_PORT", "9876"))\n'
        '# v1.5.3 · 3-tier fallback · local GPU 9876 first · cloud CPU 9886 fallback\n'
        '_V14_PORTS = [_V14_PORT, 9886] if _V14_PORT == 9876 else [_V14_PORT]'
    )

    # Replace _call_v14_daemon body
    old = """def _call_v14_daemon(req, timeout=None):
    \"\"\"Forward request to v1.4 BGE daemon (TCP localhost:9876). Returns None on failure.\"\"\"
    t = timeout if timeout is not None else _V14_TIMEOUT_S
    try:
        s = _v14_socket.socket()
        s.settimeout(t)
        s.connect((_V14_HOST, _V14_PORT))
        s.sendall((_v14_json.dumps(req) + "\\n").encode("utf-8"))
        buf = b""
        while True:
            c = s.recv(65536)
            if not c: break
            buf += c
            if buf.endswith(b"\\n"): break
        s.close()
        d = _v14_json.loads(buf.decode("utf-8", errors="replace").strip())
        return d if d.get("ok") else None
    except Exception:
        return None"""

    new = """def _call_v14_daemon(req, timeout=None):
    \"\"\"Forward request to v1.4 BGE daemon · 3-tier fallback ladder.
    Try 9876 (local GPU via reverse tunnel) then 9886 (cloud CPU). Returns None if all fail.\"\"\"
    t = timeout if timeout is not None else _V14_TIMEOUT_S
    for port in _V14_PORTS:
        try:
            s = _v14_socket.socket()
            s.settimeout(t)
            s.connect((_V14_HOST, port))
            s.sendall((_v14_json.dumps(req) + "\\n").encode("utf-8"))
            buf = b""
            while True:
                c = s.recv(65536)
                if not c: break
                buf += c
                if buf.endswith(b"\\n"): break
            s.close()
            d = _v14_json.loads(buf.decode("utf-8", errors="replace").strip())
            if d.get("ok"):
                return d
            # daemon answered but ok=false · try next port
        except Exception:
            continue
    return None"""

    if old not in t:
        return "compass_http_v09.py · _call_v14_daemon shape changed · manual review needed"

    t = t.replace(old, new)
    HTTP_V09.write_text(t)
    return "compass_http_v09.py · patched"


def move_cloud_daemon_to_9886() -> str:
    """Patch systemd unit so cloud BGE daemon binds 9886 instead of 9876.
    Reverse tunnel from local PC will own 9876."""
    t = SYSTEMD_BGE.read_text()
    if "ZMM_DAEMON_PORT=9886" in t:
        return "systemd unit · already-patched"

    # Insert Environment override before ExecStart
    if "Environment=ZMM_DAEMON_PORT=9886" not in t:
        t = t.replace(
            "[Service]\n",
            "[Service]\nEnvironment=ZMM_DAEMON_PORT=9886\n",
            1,
        )
        SYSTEMD_BGE.write_text(t)

    return "systemd unit · ZMM_DAEMON_PORT=9886 inserted"


def main() -> int:
    r1 = patch_mcp_server()
    print(r1)
    r2 = patch_http_v09()
    print(r2)
    r3 = move_cloud_daemon_to_9886()
    print(r3)

    # AST validate the python files
    import ast
    for p in [MCP_SERVER, HTTP_V09]:
        try:
            ast.parse(p.read_text())
            print(f"AST OK · {p.name}")
        except SyntaxError as e:
            print(f"AST FAIL · {p.name} · {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

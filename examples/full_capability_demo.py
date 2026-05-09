#!/usr/bin/env python3
"""compass full-capability demo · runs in <30s on a fresh laptop, daemon optional.
Records cleanly for video/asciinema/Show HN. No setup beyond `pip install nautilus-compass`.

Demos: Merkle integrity · Drift history · Session search · BGE liveness · MCP round-trip.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# Windows GBK consoles choke on ✓ ⚠ ✗ glyphs · force UTF-8 (mirrors compass_verify.py).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

GREEN, YELLOW, RED, DIM, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[0m"
OK = f"{GREEN}✓{RESET}"
WARN = f"{YELLOW}⚠{RESET}"
FAIL = f"{RED}✗{RESET}"


def banner(n: int, title: str) -> None:
    print(f"\n{DIM}─── Demo {n}/5 · {title} ───{RESET}")


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, env=env, cwd=str(ROOT))
    return p.returncode, (p.stdout or "")


def head(text: str, n: int = 20) -> str:
    lines = text.splitlines()
    out = "\n".join(lines[:n])
    if len(lines) > n:
        out += f"\n{DIM}  … ({len(lines) - n} more lines){RESET}"
    return out


def demo_1_merkle() -> tuple[str, str]:
    banner(1, "Merkle integrity (compass_verify --all)")
    script = ROOT / "compass_verify.py"
    if not script.is_file():
        raise FileNotFoundError(f"compass_verify.py missing at {script}")
    _, out = run([PY, str(script), "--all"], timeout=20)
    print(head(out, 12))
    ok_lines = sum(1 for ln in out.splitlines() if "[OK]" in ln)
    tampered = sum(1 for ln in out.splitlines() if "[TAMPERED]" in ln)
    if tampered:
        return FAIL, f"merkle · {tampered} TAMPERED files detected"
    if ok_lines >= 1:
        return OK, f"merkle · {ok_lines} chains verified · 0 tampered"
    return WARN, "merkle · no chains found"


def demo_2_drift() -> tuple[str, str]:
    banner(2, "Drift history (last 7 days)")
    script = ROOT / "drift_history.py"
    if not script.is_file():
        return WARN, "drift · drift_history.py not found"
    rc, out = run([PY, str(script), "7"], timeout=15)
    print(head(out, 20))
    if rc == 0 and "Drift History" in out:
        return OK, "drift · 7d summary rendered"
    return WARN, f"drift · rc={rc} · banner missing"


def demo_3_search() -> tuple[str, str]:
    banner(3, "Session search ('merkle chain', top 3)")
    script = ROOT / "session_search.py"
    if not script.is_file():
        return WARN, "search · session_search.py not found"
    rc, out = run([PY, str(script), "merkle chain", "--top", "3"], timeout=15)
    print(head(out, 20))
    if rc != 0:
        return WARN, f"search · rc={rc}"
    hits = sum(1 for ln in out.splitlines() if ln.lstrip().startswith("["))
    return OK, f"search · {hits} hits returned"


def demo_4_bge() -> tuple[str, str]:
    banner(4, "BGE daemon liveness (127.0.0.1:9876)")
    payload = (json.dumps({"action": "ping"}) + "\n").encode("utf-8")
    try:
        with socket.create_connection(("127.0.0.1", 9876), timeout=2) as s:
            s.sendall(payload)
            s.settimeout(2.0)
            chunks = []
            while True:
                try:
                    buf = s.recv(4096)
                except socket.timeout:
                    break
                if not buf:
                    break
                chunks.append(buf)
                if b"\n" in buf:
                    break
            reply = b"".join(chunks).decode("utf-8", errors="replace").strip()
    except ConnectionRefusedError:
        print(f"  {DIM}connection refused · daemon not running (expected){RESET}")
        return WARN, "bge · daemon down (probe ok)"
    except (socket.timeout, OSError) as e:
        print(f"  {DIM}socket error · {e}{RESET}")
        return WARN, f"bge · daemon unresponsive ({e})"
    print(f"  reply: {reply[:120]}")
    if "pong" in reply:
        return OK, "bge · daemon alive · pong received"
    return WARN, "bge · unexpected reply"


def demo_5_mcp() -> tuple[str, str]:
    banner(5, "MCP round-trip (initialize → tools/list → drift_check)")
    server = ROOT / "mcp_server.py"
    if not server.is_file():
        return WARN, f"mcp · server missing at {server}"
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.Popen([PY, str(server)], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", env=env, cwd=str(ROOT))

    def send(payload: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()

    def recv() -> dict:
        assert proc.stdout is not None
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError("server closed stdout")
            line = line.strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" not in frame and frame.get("method", "").startswith("notifications/"):
                continue
            return frame
        raise RuntimeError("recv timeout")

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05",
                         "clientInfo": {"name": "compass-demo", "version": "0.1"}}})
        init = recv()
        if "error" in init:
            return FAIL, f"mcp · initialize error · {init['error']}"
        info = init.get("result", {}).get("serverInfo", {})
        print(f"  initialize · {info.get('name')} {info.get('version')}")
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools_reply = recv()
        if "error" in tools_reply:
            return FAIL, f"mcp · tools/list error · {tools_reply['error']}"
        tools = [t["name"] for t in tools_reply.get("result", {}).get("tools", [])]
        print(f"  tools/list · {len(tools)} tools · {', '.join(sorted(tools)[:6])}")

        send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
              "params": {"name": "drift_check", "arguments": {"prompt": "hi"}}})
        call_reply = recv()
        if "error" in call_reply:
            return FAIL, f"mcp · drift_check error · {call_reply['error']}"
        content = call_reply.get("result", {}).get("content", [])
        print(f"  drift_check · {len(content)} content items")

        assert proc.stdin is not None
        proc.stdin.close()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
        return OK, f"mcp · round-trip clean · {len(tools)} tools exposed"
    except Exception as e:
        return FAIL, f"mcp · {type(e).__name__} · {e}"
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> int:
    print(f"{DIM}compass full-capability demo · 5 demos · daemon optional{RESET}")
    demos = [("merkle", demo_1_merkle), ("drift", demo_2_drift),
             ("search", demo_3_search), ("bge", demo_4_bge), ("mcp", demo_5_mcp)]
    results: list[tuple[str, str, str]] = []
    for name, fn in demos:
        try:
            mark, line = fn()
        except Exception as e:
            mark, line = FAIL, f"{name} · crashed · {type(e).__name__}: {e}"
        results.append((name, mark, line))
        print(f"  {mark} {line}")

    print(f"\n{DIM}─── Summary ───{RESET}")
    ok_count = sum(1 for _, m, _ in results if m == OK)
    fail_count = sum(1 for _, m, _ in results if m == FAIL)
    notes = []
    for name, mark, _ in results:
        if mark == WARN:
            notes.append("daemon down" if name == "bge" else f"{name} warn")
        elif mark == FAIL:
            notes.append(f"{name} fail")
    summary = f"{ok_count}/5 ok"
    if notes:
        summary += " · " + " · ".join(notes)
    print(summary)
    # Soft warns (daemon down) still exit 0 · only crash on total failure.
    return 1 if fail_count and ok_count == 0 else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)

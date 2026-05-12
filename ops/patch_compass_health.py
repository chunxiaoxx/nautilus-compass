#!/usr/bin/env python3
"""Idempotent patch · add /compass/health observability endpoint to compass_http_v09.py.

Probes:
  - local_gpu_9876 (reverse tunnel · primary)
  - cloud_cpu_9886 (fallback)
  - mcp_tcp_9877 (Claude Code MCP transport)
  - load avg + memory free
  - agent_tool_calls compass_* in last hour (PG)
  - recent journal errors (last 5 min)
  - degraded_reasons (computed)

Pair with: ops/compass_health_cron.sh (Telegram alert when degraded).
"""
import pathlib
import sys


TARGET = pathlib.Path("/home/ubuntu/compass/compass_http_v09.py")
MARKER = '@app.get("/compass/health")'
INSERT_AFTER = '@app.get("/healthz")\ndef healthz():'

ENDPOINT = '''

@app.get("/compass/health")
def compass_health():
    """v1.5.6 · observability endpoint · daemon + load + recent errors + agent calls.
    Probes each tier of the BGE daemon fallback ladder + cloud resource state.
    Cron consumer: ops/compass_health_cron.sh · Telegram alert on degraded."""
    import socket as _sk
    import time as _t
    import subprocess as _sp
    import psycopg2 as _pg

    def _probe_daemon(host, port, timeout=2.0):
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
            return {"reachable": True, "latency_ms": int((_t.time()-t0)*1000)}
        except Exception as e:
            return {"reachable": False, "error": repr(e)[:120]}
        finally:
            try: s.close()
            except Exception: pass

    components = {
        "local_gpu_9876":   _probe_daemon("127.0.0.1", 9876),
        "cloud_cpu_9886":   _probe_daemon("127.0.0.1", 9886),
        "mcp_tcp_9877":     _probe_daemon("127.0.0.1", 9877),
        "http_gateway":     {"reachable": True, "self": True},
    }

    # load + memory
    load_avg = list(os.getloadavg())
    try:
        with open("/proc/meminfo") as f:
            mi = {ln.split(":")[0]: int(ln.split()[1]) for ln in f if ":" in ln}
        mem_avail_mb = mi.get("MemAvailable", 0) // 1024
    except Exception:
        mem_avail_mb = -1

    # agent_tool_calls last hour
    agent_calls = {}
    try:
        with _pg.connect(
            host="localhost", user="nautilus_user",
            password="nautilus2024", dbname="nautilus_production"
        ) as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT tool_name, count(*)
                FROM agent_tool_calls
                WHERE ts > NOW() - INTERVAL '1 hour'
                  AND tool_name LIKE 'compass%'
                GROUP BY 1 ORDER BY 2 DESC
            """)
            for tool, n in cur.fetchall():
                agent_calls[tool] = n
    except Exception as e:
        agent_calls = {"error": repr(e)[:120]}

    # recent errors from compass.service journal · last 5min
    recent_errors = []
    try:
        r = _sp.run(
            ["journalctl", "-u", "compass.service",
             "--since", "5 min ago", "--no-pager", "-p", "warning"],
            capture_output=True, text=True, timeout=3,
        )
        if r.stdout:
            lines = [ln for ln in r.stdout.splitlines() if ln.strip()][-10:]
            recent_errors = lines
    except Exception:
        pass

    # degraded reasons
    degraded = []
    if not components["local_gpu_9876"]["reachable"] and not components["cloud_cpu_9886"]["reachable"]:
        degraded.append("both BGE daemons down · only jaccard fallback remains")
    elif not components["local_gpu_9876"]["reachable"]:
        degraded.append("local GPU unreachable · fallback to cloud CPU (slower)")
    if not components["mcp_tcp_9877"]["reachable"]:
        degraded.append("MCP TCP server down · Claude Code dialogs cannot connect")
    if load_avg[0] > 8.0:
        degraded.append(f"load avg high: {load_avg[0]:.2f}")
    if 0 <= mem_avail_mb < 500:
        degraded.append(f"memory low: {mem_avail_mb} MB available")

    tier = "primary"
    if not components["local_gpu_9876"]["reachable"]:
        tier = "fallback" if components["cloud_cpu_9886"]["reachable"] else "jaccard-only"
    if not components["mcp_tcp_9877"]["reachable"]:
        tier = "down"

    return {
        "ok": len(degraded) == 0,
        "tier": tier,
        "ts": int(_t.time()),
        "components": components,
        "load_avg": load_avg,
        "memory_available_mb": mem_avail_mb,
        "agent_calls_last_hour": agent_calls,
        "recent_errors": recent_errors,
        "degraded_reasons": degraded,
    }
'''


def main() -> int:
    t = TARGET.read_text()
    if MARKER in t:
        print("compass_http_v09.py · already-patched · no-op")
        return 0
    if INSERT_AFTER not in t:
        print(f"ERR · cannot find insert marker · manual review needed", file=sys.stderr)
        return 1

    # Locate end of healthz function · then insert ENDPOINT
    # Naive: find the closing brace pattern of healthz then insert after
    needle = 'return {\n        "status": "ok",\n        "service": "compass-gateway",\n        "version": SERVER_VERSION,\n        "region": REGION,\n        "users": users,\n        "observations": obs,\n    }'
    if needle not in t:
        print("ERR · healthz body shape changed · check manually", file=sys.stderr)
        return 1
    t = t.replace(needle, needle + ENDPOINT, 1)
    TARGET.write_text(t)
    print("patched · /compass/health endpoint added")

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

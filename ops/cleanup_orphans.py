#!/usr/bin/env python3
"""compass daemon + MCP orphan cleanup (2026-08-09 · mem_audit fix)

Usage:
    python3 cleanup_orphans.py              # dry-run · show what would be killed
    python3 cleanup_orphans.py --execute    # actually kill

Targets:
    1. Duplicate nautilus-compass daemon.py processes (keep youngest)
    2. Orphaned MCP servers older than --hours N (default 6)
    3. Optionally: DtsApo4Service restart hint

Design: precise PID targeting · never taskkill //IM · dry-run default.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    print("ERROR: pip install psutil", file=sys.stderr)
    sys.exit(1)


def find_daemon_procs() -> list[psutil.Process]:
    """Find all nautilus-compass daemon.py processes."""
    results = []
    for p in psutil.process_iter(["pid", "cmdline", "create_time", "name"]):
        try:
            cmdline = " ".join(p.info["cmdline"] or [])
            if "daemon.py" in cmdline and "nautilus-compass" in cmdline:
                results.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(results, key=lambda p: p.info["create_time"], reverse=True)


def find_orphan_mcps(max_age_h: float) -> list[psutil.Process]:
    """Find MCP server processes older than max_age_h hours."""
    cutoff = time.time() - max_age_h * 3600
    mcp_patterns = [
        "mcp-servers",
        "mcp/server.cjs",
        "mcp_server.py",
        "mcp_stdio_to_cloud.py",
    ]
    results = []
    for p in psutil.process_iter(["pid", "cmdline", "create_time", "name"]):
        try:
            cmdline = " ".join(p.info["cmdline"] or [])
            age_ok = p.info["create_time"] < cutoff
            if age_ok and any(pat in cmdline for pat in mcp_patterns):
                results.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return results


def fmt_proc(p: psutil.Process) -> str:
    try:
        mem = p.memory_info().rss / 1024 / 1024
        age_h = (time.time() - p.info["create_time"]) / 3600
        cmdline = " ".join(p.info["cmdline"] or [])[:80]
        return f"  PID={p.pid:6d}  RSS={mem:7.0f}MB  age={age_h:.1f}h  {cmdline}"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return f"  PID={p.pid:6d}  (access denied)"


def main():
    parser = argparse.ArgumentParser(description="Clean up leaked daemon + MCP processes")
    parser.add_argument("--execute", action="store_true", help="Actually kill (default: dry-run)")
    parser.add_argument("--hours", type=float, default=6, help="MCP orphan age threshold (default: 6h)")
    args = parser.parse_args()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"=== compass cleanup ({mode}) ===\n")

    # 1. Duplicate daemons
    daemons = find_daemon_procs()
    print(f"[daemon] found {len(daemons)} nautilus-compass daemon.py process(es):")
    for d in daemons:
        print(fmt_proc(d))

    if len(daemons) > 1:
        # Keep the youngest (most recent start), kill the rest
        keep = daemons[0]
        to_kill = daemons[1:]
        print(f"\n  → keep youngest PID={keep.pid}, kill {len(to_kill)} duplicate(s):")
        for p in to_kill:
            print(fmt_proc(p))
            if args.execute:
                try:
                    p.terminate()
                    print(f"    terminated PID={p.pid}")
                except psutil.NoSuchProcess:
                    pass
    else:
        print("  → no duplicates, nothing to do")

    # 2. Orphan MCP servers
    orphans = find_orphan_mcps(args.hours)
    print(f"\n[mcp] found {len(orphans)} orphaned MCP server(s) older than {args.hours}h:")
    for p in orphans:
        print(fmt_proc(p))

    if orphans:
        total_mem = sum(p.memory_info().rss for p in orphans if p.is_running()) / 1024 / 1024
        print(f"\n  → total orphan memory: {total_mem:.0f} MB")
        if args.execute:
            for p in orphans:
                try:
                    p.terminate()
                    print(f"    terminated PID={p.pid}")
                except psutil.NoSuchProcess:
                    pass
    else:
        print("  → no orphans")

    # 3. DtsApo4Service hint
    print("\n[dts] DtsApo4Service (audio driver leak, ~3.3 GB):")
    print("  → fix: Restart-Service -Name DtsApo4Service -Force  (requires admin)")
    print("  → long-term: disable DTS audio enhancement in Device Manager")

    print(f"\n=== {'done' if args.execute else 'dry-run complete (use --execute to act)'} ===")


if __name__ == "__main__":
    main()

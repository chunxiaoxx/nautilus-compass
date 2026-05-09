"""Auto-detect installed agents and offer to wire compass MCP into each.

Detects Claude Code, Claude Desktop (Mac/Win), Cursor, Cline, Continue.dev,
Zed Editor. For each found, prints the diff that would be applied and asks
yes/no per-agent. Always backs up the target config to <path>.bak.<ts>
before writing.

Run from anywhere:
    python -m nautilus_compass.install_to_agent       (after pip install)
    python scripts/install_to_agent.py                (from repo root)

Or in dry-run mode to just report what would happen:
    python scripts/install_to_agent.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

# Windows console default codepage (GBK on zh-CN) cannot render ✓ — force UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = PLUGIN_ROOT / "mcp_server.py"
DAEMON_START = PLUGIN_ROOT / "daemon_start.sh"

SERVER_NAME = "nautilus-compass"
COMMAND_PYTHON = "python3" if platform.system() != "Windows" else "python"


def candidate_targets() -> list[dict]:
    """Locations to probe for known agents.

    Returns a list of {agent, config_path, format, key_path}.
    format: "claude" (mcpServers under root) | "continue" (yaml) | "zed".
    key_path: list of dict keys leading to the mcpServers map.
    """
    home = Path.home()
    targets = []

    # Claude Code (CLI) -- ~/.claude.json
    targets.append({
        "agent": "Claude Code",
        "config_path": home / ".claude.json",
        "format": "claude",
        "key_path": ["mcpServers"],
    })

    # Claude Desktop -- per OS
    sysname = platform.system()
    if sysname == "Darwin":
        cd_path = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sysname == "Windows":
        cd_path = Path(os.environ.get("APPDATA", str(home))) / "Claude" / "claude_desktop_config.json"
    else:
        cd_path = home / ".config" / "Claude" / "claude_desktop_config.json"
    targets.append({
        "agent": "Claude Desktop",
        "config_path": cd_path,
        "format": "claude",
        "key_path": ["mcpServers"],
    })

    # Cursor -- ~/.cursor/mcp.json
    targets.append({
        "agent": "Cursor",
        "config_path": home / ".cursor" / "mcp.json",
        "format": "claude",
        "key_path": ["mcpServers"],
    })

    # Cline (VSCode) -- platform-specific globalStorage path
    if sysname == "Darwin":
        cline_base = home / "Library" / "Application Support" / "Code" / "User" / "globalStorage"
    elif sysname == "Windows":
        cline_base = Path(os.environ.get("APPDATA", str(home))) / "Code" / "User" / "globalStorage"
    else:
        cline_base = home / ".config" / "Code" / "User" / "globalStorage"
    cline_path = cline_base / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    targets.append({
        "agent": "Cline (VSCode)",
        "config_path": cline_path,
        "format": "claude",
        "key_path": ["mcpServers"],
    })

    # Continue.dev -- ~/.continue/config.yaml (we still write JSON to a sidecar
    # because YAML editing is fragile; user can paste the snippet from docs).
    targets.append({
        "agent": "Continue.dev",
        "config_path": home / ".continue" / "config.yaml",
        "format": "continue-yaml",
        "key_path": [],
    })

    return targets


def server_block() -> dict:
    """The mcpServers entry to write."""
    return {
        SERVER_NAME: {
            "command": COMMAND_PYTHON,
            "args": [str(MCP_SERVER)],
            "env": {
                "PYTHONIOENCODING": "utf-8",
            },
        }
    }


def backup(path: Path) -> Path:
    ts = int(time.time())
    bak = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, bak)
    return bak


def patch_claude_format(target: dict, dry_run: bool) -> tuple[bool, str]:
    path = target["config_path"]
    if not path.parent.exists():
        return False, f"skip · {path.parent} does not exist (agent not installed)"
    if not path.exists():
        existing = {}
    else:
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False, f"skip · cannot parse existing JSON at {path}"

    cur = existing.setdefault("mcpServers", {})
    if SERVER_NAME in cur and cur[SERVER_NAME].get("args") and str(MCP_SERVER) in cur[SERVER_NAME]["args"]:
        return False, f"already configured at {path}"

    cur.update(server_block())

    if dry_run:
        return True, f"would patch {path} (key path: mcpServers.{SERVER_NAME})"

    if path.exists():
        bak = backup(path)
        bak_note = f" (backup → {bak.name})"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        bak_note = " (created)"

    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return True, f"patched {path}{bak_note}"


def patch_continue_yaml(target: dict, dry_run: bool) -> tuple[bool, str]:
    """For Continue we don't auto-edit YAML (too fragile). Print the snippet."""
    path = target["config_path"]
    snippet = (
        "  - name: nautilus-compass\n"
        "    command: " + COMMAND_PYTHON + "\n"
        "    args:\n"
        f"      - {MCP_SERVER}\n"
        "    env:\n"
        "      PYTHONIOENCODING: utf-8\n"
    )
    if not path.parent.exists():
        return False, "skip · ~/.continue not present"
    return False, (
        f"manual step required for Continue.dev · paste under `mcpServers:` in {path}\n"
        + snippet
    )


def daemon_running() -> bool:
    """Quick TCP probe for the BGE-m3 daemon."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", 9876))
        s.close()
        return True
    except OSError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print plan, do not modify any file")
    ap.add_argument("--yes", "-y", action="store_true", help="apply to every detected target without prompting")
    args = ap.parse_args()

    print(f"plugin root: {PLUGIN_ROOT}")
    print(f"mcp_server:  {MCP_SERVER}  ({'ok' if MCP_SERVER.exists() else 'MISSING'})")
    print(f"daemon @ 127.0.0.1:9876: {'running' if daemon_running() else 'NOT running -- start with daemon_start.sh'}")
    print()

    if not MCP_SERVER.exists():
        print("error: mcp_server.py not found · run from inside the plugin clone", file=sys.stderr)
        return 1

    targets = candidate_targets()
    plans: list[tuple[dict, str]] = []
    print("=== detection ===")
    for t in targets:
        present = t["config_path"].exists() or t["config_path"].parent.exists()
        marker = "✓ found " if present else "  not found"
        print(f"  {marker}  {t['agent']:<22} {t['config_path']}")
        if present:
            plans.append((t, ""))
    print()

    if not plans:
        print("no agents detected · nothing to do.")
        return 0

    print("=== plan ===")
    for t, _ in plans:
        if t["format"] == "continue-yaml":
            ok, msg = patch_continue_yaml(t, dry_run=True)
        else:
            ok, msg = patch_claude_format(t, dry_run=True)
        verb = "PATCH" if ok else "SKIP"
        print(f"  [{verb}] {t['agent']:<22} {msg}")
    print()

    if args.dry_run:
        print("dry-run · no changes written")
        return 0

    if not args.yes:
        ans = input("apply patches? [y/N] ").strip().lower()
        if ans != "y":
            print("aborted by user")
            return 0

    print("=== applying ===")
    n_ok = 0
    for t, _ in plans:
        if t["format"] == "continue-yaml":
            ok, msg = patch_continue_yaml(t, dry_run=False)
        else:
            ok, msg = patch_claude_format(t, dry_run=False)
        verb = "ok  " if ok else "skip"
        print(f"  [{verb}] {t['agent']:<22} {msg}")
        if ok:
            n_ok += 1
    print()
    print(f"{n_ok} agent(s) patched · restart each agent to load the new MCP server.")
    if not daemon_running():
        print("reminder: start the BGE-m3 daemon for recall + drift to work:")
        print(f"  bash {DAEMON_START}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

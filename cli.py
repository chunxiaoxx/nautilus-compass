"""nautilus-compass · umbrella CLI dispatcher.

`nautilus-compass <subcommand> [args...]` routes to the compass-*
subcommand modules. Each subcommand exposes main()/serve() and parses
sys.argv[1:] itself, so the dispatcher rewrites sys.argv before
delegating, then restores it.

Backs the pyproject console-script
`nautilus-compass = nautilus_compass.cli:main`. The 5 subcommand modules
(drift_history, session_search, session_writer, mcp_server,
sdk.a2a_adapter) predate this as standalone compass-* commands; this
umbrella was missing, so the installed `nautilus-compass` crashed at
import. Lightweight on purpose — heavy subcommand imports happen only
on dispatch.
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

__all__ = ["main"]

# subcommand name → (module suffix, callable name)
_SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "doctor": ("doctor", "main"),
    "loop": ("loop_cli", "main"),
    "drift-history": ("drift_history", "main"),
    "session-search": ("session_search", "main"),
    "session-writer": ("session_writer", "main"),
    "mcp": ("mcp_server", "main"),
    "a2a": ("sdk.a2a_adapter", "serve"),
}

_DESCRIPTIONS = {
    "doctor": "verify the installed package, daemon, dependencies, and recall",
    "loop": "run or replay deterministic local learning-loop evidence",
    "drift-history": "persona-drift trend across all projects",
    "session-search": "semantic search over session memory",
    "session-writer": "distill + write a session memory file",
    "mcp": "run the MCP stdio server (Claude Code/Desktop)",
    "a2a": "serve the A2A HTTP adapter",
}


def _read_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("nautilus-compass")
        except PackageNotFoundError:
            pass
    except Exception:
        pass
    # repo-root fallback · parse sibling __init__.py without importing it
    init = Path(__file__).resolve().parent / "__init__.py"
    try:
        m = re.search(r'__version__\s*=\s*["\']([^"\']+)', init.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    except Exception:
        pass
    return "unknown"


def _print_usage(stream=None) -> None:
    stream = stream or sys.stdout
    width = max(len(s) for s in _SUBCOMMANDS)
    lines = [
        f"nautilus-compass {_read_version()} · black-box agent memory with drift detection",
        "",
        "usage: nautilus-compass <subcommand> [args...]",
        "",
        "subcommands:",
    ]
    for sub in _SUBCOMMANDS:
        lines.append(f"  {sub.ljust(width)}  {_DESCRIPTIONS.get(sub, '')}")
    lines += [
        "",
        "  --version, -V   print version",
        "  --help, -h      show this help",
        "",
        "each subcommand is also a standalone command: compass-<subcommand>",
        "run `nautilus-compass <subcommand> --help` for subcommand options.",
    ]
    stream.write("\n".join(lines) + "\n")


def _import_subcommand(module_suffix: str):
    last_err: Exception | None = None
    for prefix in ("nautilus_compass.", ""):
        try:
            return importlib.import_module(prefix + module_suffix)
        except ImportError as e:
            last_err = e
    raise last_err if last_err else ImportError(module_suffix)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in ("-h", "--help", "help"):
        _print_usage()
        return 0
    if argv[0] in ("-V", "--version", "version"):
        sys.stdout.write(f"nautilus-compass {_read_version()}\n")
        return 0

    sub = argv[0]
    if sub not in _SUBCOMMANDS:
        sys.stderr.write(f"nautilus-compass: unknown subcommand '{sub}'\n\n")
        _print_usage(sys.stderr)
        return 2

    module_suffix, fn_name = _SUBCOMMANDS[sub]
    module = _import_subcommand(module_suffix)
    fn = getattr(module, fn_name)

    saved_argv = sys.argv
    sys.argv = [f"nautilus-compass {sub}", *argv[1:]]
    try:
        result = fn()
    finally:
        sys.argv = saved_argv
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main())

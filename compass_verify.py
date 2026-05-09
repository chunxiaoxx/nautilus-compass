#!/usr/bin/env python3
"""compass verify · v1.0 tamper-evidence CLI.

Walks ~/.claude/projects/<encoded>/memory/ directories, verifies the Merkle
hash chain recorded in .chain.json, reports tampered / missing files.

Exit code:
  0 · all verified chains are valid
  1 · any tampered or missing file detected, or chain file missing

Usage:
  python compass_verify.py              # verify memory for current cwd
  python compass_verify.py --project <encoded>   # one specific project
  python compass_verify.py --all        # walk every project
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 2026-05-07: Windows GBK consoles choke on ✓ ✗ glyphs. Force UTF-8 on
# stdout/stderr so the slash command never surfaces a UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

PLUGIN_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PLUGIN_DIR))
from merkle_chain import verify_chain  # noqa: E402

PROJECTS_DIR = Path.home() / ".claude" / "projects"


def encode_cwd(cwd: Path) -> str:
    """Mirror Claude Code's project-encoding scheme.

    Drops the drive colon on Windows, replaces path separators with "-".
    Must stay in sync with daemon.py / session_writer.py.
    """
    s = str(cwd.resolve())
    # Strip leading drive letter colon: "C:\foo" -> "C\foo"
    if len(s) >= 2 and s[1] == ":":
        s = s[0] + s[2:]
    return s.replace("\\", "-").replace("/", "-")


def memory_dir_for(project_key: str) -> Path:
    return PROJECTS_DIR / project_key / "memory"


def _report(project_key: str, memory_dir: Path) -> bool:
    """Print one project's report. Return True if clean, False otherwise."""
    if not memory_dir.is_dir():
        print(f"[SKIP] {project_key} · no memory/ dir")
        return True
    chain_file = memory_dir / ".chain.json"
    if not chain_file.is_file():
        print(f"[SKIP] {project_key} · no .chain.json (never written)")
        return True
    result = verify_chain(memory_dir)
    status = "OK" if result["valid"] else "TAMPERED"
    marker = "✓" if result["valid"] else "✗"
    print(f"[{status}] {marker} {project_key}")
    print(f"    expected head: {result['expected_head'][:16]}...")
    print(f"    actual head:   {result['actual_head'][:16]}...")
    if result["tampered_files"]:
        print(f"    tampered ({len(result['tampered_files'])}):")
        for f in result["tampered_files"]:
            print(f"      - {f}")
    if result["missing_files"]:
        print(f"    missing ({len(result['missing_files'])}):")
        for f in result["missing_files"]:
            print(f"      - {f}")
    return result["valid"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify nautilus-compass memory integrity")
    ap.add_argument("--project", help="Specific encoded project key (e.g. C-Users-chunx-Projects-foo)")
    ap.add_argument("--all", action="store_true", help="Verify every project under ~/.claude/projects")
    args = ap.parse_args()

    if args.all and args.project:
        print("error: --all and --project are mutually exclusive", file=sys.stderr)
        return 2

    if args.all:
        if not PROJECTS_DIR.is_dir():
            print(f"no projects directory at {PROJECTS_DIR}", file=sys.stderr)
            return 1
        keys = sorted(p.name for p in PROJECTS_DIR.iterdir() if p.is_dir())
        if not keys:
            print("no projects found")
            return 0
        all_ok = True
        for k in keys:
            ok = _report(k, memory_dir_for(k))
            all_ok = all_ok and ok
        return 0 if all_ok else 1

    if args.project:
        key = args.project
    else:
        key = encode_cwd(Path.cwd())

    ok = _report(key, memory_dir_for(key))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

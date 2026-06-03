#!/usr/bin/env python3
"""v2.0.0 · #2 · self-evolve CLI · fallback for SessionEnd-hook missed runs.

Triggers L1 collapse + entity link scan for one project or all projects.
Designed for cron / systemd timer · every 1h is a reasonable backstop.

Usage:
  python bin/cli_self_evolve.py --project <slug>     # specific project
  python bin/cli_self_evolve.py --all                # iterate all ~/.claude/projects/*
  python bin/cli_self_evolve.py --dry-run            # report would-do without writing

Exit code 0 if any project was evolved, else 2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root or installed
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def _list_all_projects() -> list:
    """Enumerate ~/.claude/projects/*/memory dirs."""
    proj_root = Path.home() / ".claude" / "projects"
    if not proj_root.exists():
        return []
    out = []
    for d in proj_root.iterdir():
        if d.is_dir():
            mem = d / "memory"
            if mem.exists():
                out.append((d.name, mem))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="self-evolve · trigger L1 collapse + entity scan")
    p.add_argument("--project", help="project slug (encoded cwd) · skipped if --all")
    p.add_argument("--all", action="store_true", help="iterate all projects")
    p.add_argument("--dry-run", action="store_true", help="report only · no writes")
    p.add_argument("--threshold", type=int, default=3,
                   help="ungrouped sessions before L1 trigger fires (default 3)")
    args = p.parse_args()

    if not args.project and not args.all:
        p.error("must pass --project <slug> or --all")

    try:
        from storage.self_evolve import (
            count_ungrouped,
            evolve_at_session_end,
        )
    except ImportError as e:
        sys.stderr.write(f"can't import storage.self_evolve: {e}\n")
        return 1

    targets = []
    if args.all:
        targets = _list_all_projects()
    else:
        mem = Path.home() / ".claude" / "projects" / args.project / "memory"
        if not mem.exists():
            sys.stderr.write(f"no memory dir at {mem}\n")
            return 1
        targets = [(args.project, mem)]

    if not targets:
        print("no targets")
        return 2

    any_evolved = False
    for slug, mem_dir in targets:
        ungrouped = count_ungrouped(mem_dir)
        if args.dry_run:
            print(f"[dry-run] {slug}: ungrouped={ungrouped} threshold={args.threshold}")
            continue
        result = evolve_at_session_end(mem_dir, l1_threshold=args.threshold)
        l1 = result.get("l1_triggered", {})
        if l1.get("triggered"):
            any_evolved = True
            print(f"{slug}: L1 triggered · groups={l1.get('groups', 0)} "
                  f"ungrouped_before={l1.get('ungrouped', 0)}")
        else:
            ent = result.get("entity_scan", {})
            print(f"{slug}: skip · ungrouped={l1.get('ungrouped', ungrouped)} "
                  f"refs={ent.get('refs_total', 0)}")

    return 0 if (any_evolved or args.dry_run) else 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""v1.7.1 · L1 build CLI · manual trigger for L1 overview generation.

Wires l1_grouper + l1_renderer + l1_index modules together.
NO LLM. Uses BGE-m3 only when topic clustering kicks in.

License: MIT (matches nautilus-compass).
Reference: paper/SPEC_LAYER2_L1_REWRITE.md.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.l1_grouper import group_sessions
from storage.l1_renderer import render_all
from storage.l1_index import update_index


def main():
    ap = argparse.ArgumentParser(description="Build L1 overview tier for a project.")
    ap.add_argument("--project", required=False, default=None,
                    help="Encoded project dir name (defaults to most-recent)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print planned actions without writing")
    ap.add_argument("--build-mode", choices=["full", "incremental"], default="full",
                    help="Full rebuild or only changed sessions (incremental)")
    args = ap.parse_args()

    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        print(f"ERROR: {projects_dir} not found", file=sys.stderr)
        return 1
    if args.project:
        target = projects_dir / args.project
    else:
        candidates = sorted(projects_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        target = next((c for c in candidates if (c / "memory").exists()), None)
    if not target or not (target / "memory").exists():
        print(f"ERROR: no memory dir found in {target}", file=sys.stderr)
        return 1

    sessions = sorted((target / "memory").glob("session_*.md"))
    print(f"compass l1-build · project={target.name} · sessions={len(sessions)} · mode={args.build_mode}")

    groups = group_sessions(sessions)
    if not groups:
        print("no groups formed (need >=3 sessions per thread or >=4 in topic cluster)")
        return 0

    print(f"groups formed: {len(groups)}")
    for gid, members in groups.items():
        print(f"  - {gid}: {len(members)} sessions")

    if args.dry_run:
        print("DRY RUN · no files written")
        return 0

    out_dir = target / "memory" / "_l1"
    written = render_all(groups, out_dir)
    idx = update_index(out_dir, written)
    print(f"wrote {len(written)} L1 files to {out_dir}")
    print(f"index entries: {len(idx)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

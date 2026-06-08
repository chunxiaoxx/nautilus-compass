"""corpus_sync — mirror the compass memory corpus (.md only) between hosts.

Phase 0 Task 2 of the cloud-substrate plan. The cloud T4 daemon needs the memory
corpus but NOT the multi-GB transcript history: we mirror only `.md` files
(measured ~5MB/project vs 1.8GB with transcripts). rsync makes it idempotent —
a re-run with no changes transfers nothing.

  push_corpus(local_memory_dir, remote_host, remote_dir)   # dev/CPU-server -> T4
  pull_corpus(remote_host, remote_dir, local_cache)         # T4 startup pull

CLI:
  python corpus_sync.py push --local ~/.claude/.../memory --host ubuntu@T4 --remote ~/compass-corpus
  python corpus_sync.py pull --host ubuntu@T4 --remote ~/compass-corpus --local ./corpus-cache
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

# rsync filter: recurse dirs, take only .md, drop everything else.
_MD_FILTER = ["--include=*/", "--include=*.md", "--exclude=*"]


def select_corpus_files(root: str) -> list[str]:
    """Return relative paths of corpus files to sync (.md only, no transcripts/caches).

    Pure helper — the source of truth for what counts as 'corpus'. Mirrors the
    rsync filter so tests can assert selection without running rsync.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__" and not d.startswith(".git")]
        for fn in filenames:
            if fn.endswith(".md"):
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                out.append(rel)
    return out


def _default_runner(cmd: list[str]) -> int:
    return subprocess.run(cmd).returncode


def _rsync(src: str, dst: str, dry_run: bool, runner) -> int:
    cmd = ["rsync", "-az", "--delete"] + _MD_FILTER
    if dry_run:
        cmd.append("-n")
    cmd += [src, dst]
    return runner(cmd)


def push_corpus(local_dir, remote_host, remote_dir, dry_run=False, runner=None):
    """Mirror local .md corpus up to remote_host:remote_dir."""
    runner = runner or _default_runner
    src = local_dir.rstrip("/\\") + "/"
    dst = f"{remote_host}:{remote_dir}"
    return _rsync(src, dst, dry_run, runner)


def pull_corpus(remote_host, remote_dir, local_cache, dry_run=False, runner=None):
    """Pull the .md corpus down from remote_host:remote_dir into local_cache."""
    runner = runner or _default_runner
    src = f"{remote_host}:{remote_dir.rstrip('/')}/"
    dst = local_cache.rstrip("/\\") + "/"
    os.makedirs(local_cache, exist_ok=True)
    return _rsync(src, dst, dry_run, runner)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("push")
    p.add_argument("--local", required=True)
    p.add_argument("--host", required=True)
    p.add_argument("--remote", required=True)
    p.add_argument("--dry-run", action="store_true")
    q = sub.add_parser("pull")
    q.add_argument("--host", required=True)
    q.add_argument("--remote", required=True)
    q.add_argument("--local", required=True)
    q.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.cmd == "push":
        n = len(select_corpus_files(args.local))
        print(f"pushing {n} .md files -> {args.host}:{args.remote}")
        rc = push_corpus(args.local, args.host, args.remote, dry_run=args.dry_run)
    else:
        rc = pull_corpus(args.host, args.remote, args.local, dry_run=args.dry_run)
    sys.exit(rc)


if __name__ == "__main__":
    main()

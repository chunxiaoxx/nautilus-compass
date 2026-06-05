"""Single source of truth for PoI memory_key = project/filename.
Used by emission (local + cloud inline copy), reconcile, boost, migration.
Pure · no I/O on the derive path. Reference: docs/plans/2026-06-03-poi-central-ledger-design.md §5.
"""
from __future__ import annotations
from typing import Optional


def _normalize_project(project: str) -> str:
    """Match recall.py encoded_cwd form: C:\\Users\\chunx -> C--Users-chunx."""
    p = (project or "").strip()
    if ":" in p or "\\" in p:
        p = p.replace(":\\", "--").replace(":/", "--").replace("\\", "-").replace("/", "-")
    return p


def _basename(filename: str) -> str:
    name = (filename or "").strip().replace("\\", "/")
    return name.rsplit("/", 1)[-1]


def derive_memory_key(project: str, filename: str) -> str:
    return f"{_normalize_project(project)}/{_basename(filename)}"


def memory_key_from_path(path) -> Optional[str]:
    """Derive key from a memory file path .../<project>/memory/<file>.
    Anchors on the literal 'memory' directory segment: project is the segment
    immediately before it, filename is the last segment. Returns None when the
    layout doesn't match (bare filename, no 'memory' dir, nothing before it, or
    'memory' is the last segment) so callers fall back to frontmatter / env NS —
    never silently mislabel an unrelated path segment as the project."""
    parts = [p for p in str(path).replace("\\", "/").split("/") if p]
    if len(parts) < 3:
        return None  # filename only or too shallow
    try:
        midx = len(parts) - 1 - parts[::-1].index("memory")  # last 'memory' segment
    except ValueError:
        return None  # no 'memory' dir → project undeterminable
    if midx == 0 or midx == len(parts) - 1:
        return None  # nothing before 'memory' (no project) or it IS the last part
    return derive_memory_key(parts[midx - 1], parts[-1])

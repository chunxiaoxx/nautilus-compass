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
    """Derive key from a memory file path .../projects/<project>/memory/<file>.
    Returns None if path is just a filename (project undeterminable)."""
    s = str(path).replace("\\", "/")
    parts = s.split("/")
    if len(parts) < 3:
        return None  # filename only or too shallow
    # <project>/memory/<file>  → project = parts[-3]
    return derive_memory_key(parts[-3], parts[-1])

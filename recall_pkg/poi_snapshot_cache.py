"""Lazy mtime-cached PoI credit snapshot for the long-running daemon boost path.

Reloads only when the snapshot file's mtime changes · keeps last-good dict if a
reload fails (corrupt/half-written) or the file disappears · never raises. The
boost is an enhancement, not a dependency, so any error degrades gracefully to
the last-good (or empty) dict. Reference: design §4.3/§8.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict

try:
    from ..proof.poi_credit_store import load_snapshot
except (ImportError, ValueError):
    from proof.poi_credit_store import load_snapshot  # type: ignore

_CACHE: Dict[str, float] = {}
_MTIME: float = -1.0
_LOADED_PATH: str = ""


def _snapshot_path() -> Path:
    env = os.environ.get("COMPASS_POI_CREDIT_SNAPSHOT")
    if env:
        return Path(env)
    base = os.environ.get(
        "COMPASS_POI_CACHE_DIR",
        str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache"),
    )
    return Path(base) / "poi_credit_cache.json"


def reset_cache() -> None:
    """Test helper · drop the in-memory cache so the next get reloads."""
    global _CACHE, _MTIME, _LOADED_PATH
    _CACHE, _MTIME, _LOADED_PATH = {}, -1.0, ""


def get_credit_snapshot() -> Dict[str, float]:
    """Return the credit dict · reload from disk only on mtime/path change.

    On any error or corrupt reload, keep the last-good dict. When the configured
    path changes (e.g. tests swapping snapshots), the cache resets for the new
    path before attempting a load.
    """
    global _CACHE, _MTIME, _LOADED_PATH
    p = _snapshot_path()
    path_str = str(p)
    try:
        # Path changed → forget the previous snapshot's cache.
        if path_str != _LOADED_PATH:
            _CACHE, _MTIME, _LOADED_PATH = {}, -1.0, path_str

        if not p.exists():
            return _CACHE

        mtime = p.stat().st_mtime
        if mtime == _MTIME:
            return _CACHE  # unchanged since last load

        loaded = load_snapshot(p)
        _MTIME = mtime
        # load_snapshot returns {} on corrupt/unreadable. Only adopt non-empty
        # data so a corrupt reload keeps the last-good dict. An intentionally
        # empty snapshot stays empty because _CACHE is already {} in that case.
        if loaded:
            _CACHE = loaded
        return _CACHE
    except Exception:
        return _CACHE

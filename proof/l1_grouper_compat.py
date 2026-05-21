"""Compat shim · expose parse_session_frontmatter safely from proof/ subpackage.

Tries relative import first (package context · production)
then absolute (tests run with root in sys.path).
"""
from pathlib import Path

_parse = None
try:
    from ..storage.l1_grouper import parse_session_frontmatter as _parse  # type: ignore
except (ImportError, ValueError):
    try:
        from storage.l1_grouper import parse_session_frontmatter as _parse  # type: ignore
    except ImportError:
        _parse = None


def parse_session_frontmatter_safe(path) -> dict:
    if _parse is None:
        return {}
    return _parse(Path(path) if not isinstance(path, Path) else path)

"""Soul PR gate · blacklist + diff LOC cap.

Shared safety gate for Soul's apply/draft-PR path. Draft PR + human review is
the final merge gate; this layer rejects obviously-unsafe changes before a PR is
even opened. NEVER allows auto-merge.
"""
from __future__ import annotations
from typing import List, Tuple

# Paths Soul must never modify via auto-generated PRs
PATH_BLACKLIST = (
    ".env", "alembic/", "migrations/", "contracts/", "secrets",
    "_dead_code_backup", ".soul-",
)
MAX_PR_DIFF_LOC = 500


def check_paths(changed_paths: List[str]) -> Tuple[bool, str]:
    for p in changed_paths:
        for bad in PATH_BLACKLIST:
            if bad in p:
                return False, f"blacklisted path: {p} (matched '{bad}')"
    return True, "ok"


def check_diff_loc(total_loc: int, cap: int = MAX_PR_DIFF_LOC) -> Tuple[bool, str]:
    if total_loc > cap:
        return False, f"diff {total_loc} LOC exceeds cap {cap}"
    return True, "ok"


def gate(changed_paths: List[str], total_loc: int, cap: int = MAX_PR_DIFF_LOC) -> Tuple[bool, str]:
    ok, reason = check_paths(changed_paths)
    if not ok:
        return False, reason
    return check_diff_loc(total_loc, cap)

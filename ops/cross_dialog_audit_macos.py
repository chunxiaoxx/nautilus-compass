#!/usr/bin/env python3
"""Read-only inventory for the four current Nautilus dialog repositories.

This replaces the historical Windows-path audit. It reports repository identity,
dirty state, recent commits, memory files, worktrees, and handoff candidates;
it never edits files, sends messages, or infers business acceptance.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess
from typing import Any


DIALOGS = {
    "compass": pathlib.Path("/Users/chunxiao.wang/Projects/nautilus-compass"),
    "core": pathlib.Path("/Users/chunxiao.wang/Projects/nautilus-core"),
    "v5": pathlib.Path("/Users/chunxiao.wang/Projects/nautilus-v5"),
    "flywheel": pathlib.Path("/Users/chunxiao.wang/Projects/nautilusflywheel"),
}


def run_git(root: pathlib.Path, *args: str) -> tuple[str, int]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        return result.stdout.strip(), result.returncode
    except (OSError, subprocess.SubprocessError) as error:
        return f"{type(error).__name__}: {error}", 1


def audit(name: str, root: pathlib.Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": name,
        "path": str(root),
        "exists": root.exists(),
        "read_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if not root.exists():
        return row

    top_level = root / "AGENTS.md"
    row["agents_md"] = {"exists": top_level.exists(),
                        "sha256": __import__("hashlib").sha256(top_level.read_bytes()).hexdigest()
                        if top_level.exists() else None}
    branch, rc = run_git(root, "branch", "--show-current")
    row["branch"] = branch if rc == 0 else None
    status, rc = run_git(root, "status", "--short")
    dirty_lines = [line for line in status.splitlines() if line.strip()] if rc == 0 else []
    row["dirty_count"] = len(dirty_lines)
    row["dirty_sample"] = dirty_lines[:5]
    commits, rc = run_git(root, "log", "-5", "--date=iso-strict", "--pretty=format:%h %ad %s")
    row["recent_commits"] = commits.splitlines() if rc == 0 else []
    worktrees, rc = run_git(root, "worktree", "list", "--porcelain")
    row["worktree_count"] = sum(1 for line in worktrees.splitlines() if line.startswith("worktree ")) if rc == 0 else None
    memory = root / ".claude" / "memory"
    row["memory_files"] = sorted((item.name for item in memory.glob("*.md")),
                                  key=lambda name: (memory / name).stat().st_mtime,
                                  reverse=True)[:5] if memory.exists() else []
    handoffs = sorted(
        (item.name for item in root.glob("HANDOFF*.md")),
        key=lambda name: (root / name).stat().st_mtime,
        reverse=True,
    )[:5]
    row["handoff_candidates"] = handoffs
    return row


def main() -> int:
    output = pathlib.Path(
        "/Users/chunxiao.wang/Projects/nautilus-compass/runtime/cross-dialog-inventory-20261116.json"
    )
    document = {
        "schema": "cross-dialog-inventory/1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": "Read-only inventory; no business acceptance inferred.",
        "dialogs": [audit(name, root) for name, root in DIALOGS.items()],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(output),
        "dialogs": [(row["name"], row["exists"], row.get("dirty_count"))
                     for row in document["dialogs"]],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

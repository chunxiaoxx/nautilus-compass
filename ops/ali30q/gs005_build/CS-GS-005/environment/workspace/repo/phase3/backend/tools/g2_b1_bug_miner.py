"""G2-B1 bug miner: turn this repo's own git history into repair-task queue rows.

Cheap filter only — the executor's RED precondition is the real gate (it
refuses to spend tokens unless the task actually reproduces as RED).

Output: one JSON object per line (JSONL), schema g2-b1-task-v1:
  {buggy_commit, reference_fix_commit, test_files[], source_files[]}

Selection heuristic (deliberately conservative):
  - fix commit touches at least one tests/** file AND at least one non-test source file
  - diff is small (< 200 changed lines total)
  - commit message is not pure docs/chore
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

MAX_CHANGED_LINES = 200
SKIP_PREFIXES = ("docs", "chore", "test", "style", "revert")


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    out = subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                         timeout=120, check=check)
    return out


def _is_test_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    under_tests = "/tests/" in path or path.startswith("tests/")
    return under_tests and (name.startswith("test_") or name.endswith("_test.py"))


def _parse_log(log: str) -> list[tuple[str, str, int]]:
    """Walk raw log lines: a line with \x00 starts an entry; the next line
    matching 'N files changed' is its stat."""
    entries: list[tuple[str, str, int]] = []
    current: tuple[str, str] | None = None
    for line in log.splitlines():
        if "\x00" in line:
            current = tuple(line.split("\x00", 1))  # type: ignore[assignment]
        elif current is not None and "changed" in line:
            match = re.search(r"(\d+) files? changed", line)
            if match:
                entries.append((*current, int(match.group(1))))
            current = None
    return entries


def mine(repo_root: Path, since: str = "1.year.ago", limit: int = 500) -> list[dict]:
    log = _git(["log", f"--since={since}", f"-{limit}", "--no-merges",
                "--pretty=%H%x00%s", "--shortstat"], repo_root).stdout.decode("utf-8", "replace")
    tasks: list[dict] = []
    for commit_hash, subject, changed in _parse_log(log):
        # Repair tasks only: feature/refactor commits add their own tests —
        # at the buggy parent those tests don't exist (collected-0 false RED,
        # proven 8/23 on three straight queue rows).
        if not subject.lower().startswith(("fix", "bugfix", "hotfix")):
            continue
        if subject.lower().startswith(SKIP_PREFIXES):
            continue
        if changed == 0 or changed > MAX_CHANGED_LINES:
            continue
        files = _git(["show", "--name-only", "--pretty=format:", commit_hash],
                     repo_root).stdout.decode("utf-8", "replace").splitlines()
        test_files = [f for f in files if _is_test_file(f)]
        source_files = [f for f in files if f and f not in test_files
                        and f.endswith((".py", ".ts", ".tsx", ".go"))]
        if not test_files or not source_files:
            continue
        parent = _git(["rev-parse", f"{commit_hash}^"],
                       repo_root).stdout.decode().strip()
        # The test file must already exist at the buggy parent (modified, not added).
        if any(_git(["cat-file", "-e", f"{parent}:{f}"], repo_root,
                    check=False).returncode != 0 for f in test_files):
            continue
        tasks.append({
            "schema_version": "g2-b1-task-v1",
            "buggy_commit": parent,
            "reference_fix_commit": commit_hash,
            "subject": subject[:200],
            "test_files": test_files[:5],
            "source_files": source_files[:5],
        })
    return tasks


def main() -> int:
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("g2b1_task_queue.jsonl")
    tasks = mine(repo_root)
    out_path.write_text(
        "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tasks),
        encoding="utf-8",
    )
    print(f"mined {len(tasks)} candidate tasks -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

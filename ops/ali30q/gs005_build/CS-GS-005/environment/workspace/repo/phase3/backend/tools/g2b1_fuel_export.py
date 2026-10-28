"""G2-B1 fuel exporter: mined repair tasks -> V5 a_class_filter intake format.

Contract (V5 dialog 2026-08-24): three pieces per task —
  task_uid / summary / starter_inline (buggy source) / verifier_inline (the
fix's test, i.e. the spec). Provenance and our run evidence ride along so the
filter can prioritize tasks we have verified solutions for.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _git_show(repo: Path, ref: str, path: str) -> str:
    out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=repo,
                         capture_output=True, timeout=120, check=True)
    return out.stdout.decode("utf-8", "replace")


def export_task(repo_root: Path, task: dict) -> dict | None:
    source = task["source_files"][0]
    test = task["test_files"][0]
    try:
        starter = _git_show(repo_root, task["buggy_commit"], source)
        verifier = _git_show(repo_root, task["reference_fix_commit"], test)
    except subprocess.CalledProcessError:
        return None
    return {
        "task_uid": f"g2b1:{task['reference_fix_commit'][:12]}",
        "summary": task.get("subject", ""),
        "starter_inline": starter,
        "verifier_inline": verifier,
        "provenance": {
            "repo": repo_root.name,
            "buggy_commit": task["buggy_commit"],
            "reference_fix_commit": task["reference_fix_commit"],
            "starter_path": source,
            "verifier_path": test,
        },
    }


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: g2b1_fuel_export.py <repo_root> <queue.jsonl> [out.jsonl]")
        return 2
    repo = Path(sys.argv[1]).resolve()
    queue = Path(sys.argv[2])
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else queue.with_name(
        queue.stem + "_fuel_export.jsonl")
    rows = [json.loads(l) for l in queue.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    exported = []
    for task in rows:
        rec = export_task(repo, task)
        if rec:
            exported.append(rec)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                           for r in exported), encoding="utf-8")
    print(f"exported {len(exported)}/{len(rows)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

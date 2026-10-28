"""Cycle 15 · capture engine output for human inspection.

The previous run (cycle15_self_bootstrap.py) showed the LLM's semantic diff was
exactly the spec'd additions (import re + _inject_file_context). The strict
semantic check fails ANY diff · but we want to verify the OTHER lines were
truly preserved before considering manual apply.

This script:
  1. Re-dispatches the same task via engine.generate (no ship wrapper)
  2. Parses the LLM output blocks
  3. Writes the proposed new ship.py to scripts/cycle15_proposed_ship.py
  4. Runs unified diff vs original
  5. Reports added/removed line counts
"""
from __future__ import annotations

import difflib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "phase3" / "backend"))

from engine.nautilus_engine import NautilusEngine  # noqa: E402

BASE_DIR = REPO_ROOT
TARGET_REL = "phase3/backend/engine/ship.py"


# Re-use exact SPEC from cycle15_self_bootstrap (kept inline · script
# duplication is intentional · this is a one-shot inspection tool).
SPEC = """\
Add file-content context injection to phase3/backend/engine/ship.py.

GOAL: When ship() runs against a task that mentions specific file paths,
automatically read those files from base_dir and prepend their content to the
LLM prompt. This gives the LLM ground truth for MINIMAL CHANGE MODE.

CHANGES (precise · do NOT modify any other line):

1. Add `import re` to the existing import block at the top of the file
   (place it alphabetically: after `import json`, before `import shutil`).

2. Add a new module-level helper function. Place it immediately AFTER the
   existing `_run_semantic_checks` function and BEFORE the `_build_retry_prompt`
   function. The helper must be exactly:

    def _inject_file_context(
        task: str, base_dir: Path, max_chars_per_file: int = 8000
    ) -> str:
        \"\"\"Read every file mentioned in `task` that exists under base_dir and
        prepend its content to the prompt as a CONTEXT block. Returns the task
        unchanged when no matches resolve.

        Karpathy Fix 1 · gives the LLM ground truth so MINIMAL CHANGE MODE
        (cycle 12 P0) has real lines to preserve.
        \"\"\"
        pattern = re.compile(r"[\\w/\\-_.\\\\]+\\.(?:py|js|ts|tsx|md|sql|yaml|yml|json|sh|go|rs)\\b")
        found = sorted(set(pattern.findall(task)))
        blocks: list[str] = []
        for rel in found:
            target = (base_dir / rel).resolve()
            try:
                target.relative_to(base_dir)
            except ValueError:
                continue
            if not target.is_file():
                continue
            try:
                content = target.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(content) > max_chars_per_file:
                continue
            blocks.append(
                f"CONTEXT for {rel} (preserve unless task explicitly says otherwise):\\n"
                f"```\\n{content}\\n```\\n"
            )
        if not blocks:
            return task
        return "\\n".join(blocks) + "\\n" + task

3. Inside the `ship()` function · immediately after the line
   `base = Path(base_dir).resolve()` · add exactly one new line:
       task = _inject_file_context(task, base)

DO NOT modify any other line in ship.py. Keep ALL other code identical · do
not refactor · do not rename · do not change function signatures · do not
reorder existing functions.
"""


def main() -> int:
    target = BASE_DIR / TARGET_REL
    original = target.read_text(encoding="utf-8")
    print(f"[setup] original = {len(original)} chars · {len(original.splitlines())} lines")

    task = (
        f"ORIGINAL FILE CONTENT of {TARGET_REL} (preserve EVERY line below "
        f"byte-for-byte except where the SPEC explicitly says to add):\n\n"
        f"```python\n{original}```\n\n"
        f"SPEC:\n{SPEC}"
    )

    print(f"[dispatch] engine.generate · max_tokens=16000 · temp=0.1")
    engine = NautilusEngine(dry_run=True, base_dir=str(BASE_DIR))
    raw = engine.generate(task, max_tokens=16000, temperature=0.1)
    print(f"[result] raw output = {len(raw)} chars")

    blocks = engine.parse_file_blocks(raw)
    print(f"[result] parsed blocks = {len(blocks)}")
    if not blocks:
        print("[FATAL] no blocks parsed · LLM did not follow output convention")
        out_raw = REPO_ROOT / "scripts" / "cycle15_raw_output.txt"
        out_raw.write_text(raw, encoding="utf-8")
        print(f"[raw saved] {out_raw}")
        return 2

    new_content = blocks[0]["content"]
    out_path = REPO_ROOT / "scripts" / "cycle15_proposed_ship.py"
    out_path.write_text(new_content, encoding="utf-8")
    print(f"[saved] proposed ship.py → {out_path}")
    print(f"[result] new = {len(new_content)} chars · {len(new_content.splitlines())} lines")
    print(f"[delta] +{len(new_content) - len(original)} chars · +{len(new_content.splitlines()) - len(original.splitlines())} lines")

    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{TARGET_REL}",
        tofile=f"b/{TARGET_REL}",
        n=2,
    ))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    print(f"[diff] +{added} lines · -{removed} lines")

    diff_path = REPO_ROOT / "scripts" / "cycle15_proposed_ship.diff"
    diff_path.write_text("".join(diff), encoding="utf-8")
    print(f"[diff saved] {diff_path}")

    if removed == 0:
        print(f"\n[verdict] ZERO line removals · pure addition (Karpathy Fix 1 as spec)")
        print(f"[verdict] safe to apply IF tests pass on proposed file")
    elif removed < 5:
        print(f"\n[verdict] minor removals · review diff manually before apply")
    else:
        print(f"\n[verdict] significant removals · semantic check correctly blocked apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

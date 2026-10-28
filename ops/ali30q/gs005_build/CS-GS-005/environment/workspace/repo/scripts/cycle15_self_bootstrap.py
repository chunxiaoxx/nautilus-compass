"""Cycle 15 · engine self-bootstraps Karpathy Fix 1 (context injection in ship.py).

Recursive self-modification: dispatch the engine via cycle 12 P0+P1 pipeline to
add the missing context-injection helper to its own ship.py · using the
cycle 14b learning (provide ground truth in task) + cycle 12 trigger phrases.

If engine succeeds:
  - Layer 3 compounding validated end-to-end (cycle 12 → cycle 15)
  - Karpathy Fix 1 shipped for free without manual coding

If engine fails:
  - Hard data on where engine breaks for real change tasks
  - Cycle 12 P1 semantic check correctly blocks bad apply (verified safety net)

apply=False first · semantic check + standard checks must pass · then human
review · only THEN consider apply=True (separate manual step).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "phase3" / "backend"))

from engine.nautilus_engine import (  # noqa: E402
    DEFAULT_SYSTEM_PROMPT,
    NautilusEngine,
)
from engine.ship import ship  # noqa: E402

BASE_DIR = str(REPO_ROOT)
TARGET_REL = "phase3/backend/engine/ship.py"


class HighBudgetEngine(NautilusEngine):
    """NautilusEngine with larger output budget · ship.py is ~14k chars · needs ~5k tokens."""

    def generate(self, task: str, context: str = "", max_tokens: int = 16000, temperature: float = 0.1) -> str:
        return super().generate(task, context=context, max_tokens=max_tokens, temperature=temperature)


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
    target = Path(BASE_DIR) / TARGET_REL
    if not target.is_file():
        print(f"[FATAL] target missing: {target}")
        return 2
    original = target.read_text(encoding="utf-8")
    print(f"[setup] base_dir = {BASE_DIR}")
    print(f"[setup] target   = {TARGET_REL}")
    print(f"[setup] original = {len(original)} chars · {len(original.splitlines())} lines")
    print(f"[setup] MINIMAL CHANGE MODE in prompt: {'MINIMAL CHANGE MODE' in DEFAULT_SYSTEM_PROMPT}")
    print(f"[setup] MINIMAX_API_KEY set: {bool(os.environ.get('MINIMAX_API_KEY'))}")
    print()

    task = (
        f"ORIGINAL FILE CONTENT of {TARGET_REL} (preserve EVERY line below "
        f"byte-for-byte except where the SPEC explicitly says to add):\n\n"
        f"```python\n{original}```\n\n"
        f"SPEC:\n{SPEC}"
    )

    print(f"[dispatch] task chars: {len(task)} · apply=False · max_retries=1")
    print()

    engine = HighBudgetEngine(dry_run=True, base_dir=BASE_DIR)
    result = ship(
        engine,
        task,
        base_dir=BASE_DIR,
        apply=False,
        dispatch_audit=False,
        max_retries=1,
    )

    print(f"[result] errors        = {result.errors or '(none)'}")
    print(f"[result] applied       = {result.applied}")
    print(f"[result] attempts      = {len(result.attempts)}")
    for a in result.attempts:
        print(f"           attempt {a['attempt_number']}: "
              f"raw={a['raw_response_chars']} chars · files={len(a['files_planned'])} · "
              f"checks_passed={a['check_result'].get('passed')}")
    print(f"[result] files_planned = {len(result.files_planned)}")
    for f in result.files_planned:
        print(f"           · {f['path']} · {f['size']} chars · {f['lang']}")
    print()
    print(f"[result] check_result.passed = {result.check_result.get('passed')}")
    for c in result.check_result.get("checks", []):
        status = (
            "SKIP" if c.get("skipped")
            else ("PASS" if c.get("passed") else "FAIL")
        )
        msg = (c.get("message") or "").strip().replace("\n", " | ")[:280]
        print(f"           [{status}] {c['name']:14} {msg}")

    sem = [c for c in result.check_result.get("checks", []) if c.get("name") == "semantic"]
    if sem and sem[0]["passed"]:
        print(f"\n[verdict] PASS · engine successfully preserved semantics while adding helper")
        print(f"[verdict] Next: human review of staged content before apply=True")
        # Save staged-equivalent for human review by re-generating in dry-run
        # (we lose access to staging temp dir after ship() cleans it up)
        # Caller can read the changes by separately re-running with the same task.
        return 0
    if sem and not sem[0]["passed"]:
        print(f"\n[verdict] PARTIAL · semantic check correctly caught over-rewrite")
        print(f"[verdict] cycle 12 P1 safety net validated again · engine cannot ship Karpathy Fix 1 unmodified")
        print(f"[verdict] hard data captured for cycle 16+ improvement")
        return 1
    print(f"\n[verdict] semantic check did not fire · investigate trigger phrase detection")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Cycle 12 P2 · real-effect verification on quantum-buddha BUDDHA-A.1 task.

Dispatches engine.ship() with the original failing task spec against the
fix-last-hangul.py script · uses apply=False (dry-run) · observes:
  1. Engine pipeline fires end-to-end
  2. cycle 12 P1 semantic check appended to check_result
  3. cycle 12 P0 MINIMAL CHANGE MODE prompt effect (semantic check passes
     when LLM preserves code · fails when LLM over-rewrites)

NO LLM creds in this file. Reuses MINIMAX_API_KEY from environment.
NO writes to base_dir (apply=False).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `engine.*` importable without installing
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "phase3" / "backend"))

from engine.nautilus_engine import DEFAULT_SYSTEM_PROMPT, NautilusEngine  # noqa: E402
from engine.ship import ship  # noqa: E402

BASE_DIR = "C:/Users/chunx/quantum-buddha-project"
TARGET_REL = "scripts/fix-last-hangul.py"
TASK = (
    f"in {TARGET_REL} · add a brief module docstring at the very top "
    f"describing this script (Google Translate via Vertex AI Gemini for "
    f"zh-source.json paragraphs into Japanese, with OpenCC s2t conversion · "
    f"saves into knowledge-translations.json) · "
    f"keep ALL other code identical · do not refactor"
)


def main() -> int:
    print(f"[setup] base_dir = {BASE_DIR}")
    print(f"[setup] target   = {TARGET_REL}")
    print(f"[setup] MINIMAX_API_KEY set: {bool(os.environ.get('MINIMAX_API_KEY'))}")
    target = Path(BASE_DIR) / TARGET_REL
    if not target.is_file():
        print(f"[FATAL] target file missing: {target}")
        return 2
    original = target.read_text(encoding="utf-8")
    print(
        f"[setup] original: {len(original)} chars · "
        f"{len(original.splitlines())} lines"
    )

    print(f"[verify P0] DEFAULT_SYSTEM_PROMPT has MINIMAL CHANGE MODE: "
          f"{'MINIMAL CHANGE MODE' in DEFAULT_SYSTEM_PROMPT}")
    print()
    print(f"[dispatch] task: {TASK[:120]}...")
    print(f"[dispatch] apply=False · dispatch_audit=False · max_retries=0")
    print()

    # Cycle 15 e2e · use SIMPLE original BUDDHA-A.1 task · no manual context
    # prepend. Karpathy Fix 1 (engine-self-shipped this session) should auto-
    # detect the file path in the task and inject the file content. End-to-end
    # validation that Layer 3 compounding + Karpathy Fix 1 close the loop.
    engine = NautilusEngine(dry_run=True, base_dir=BASE_DIR)
    result = ship(
        engine,
        TASK,
        base_dir=BASE_DIR,
        apply=False,
        dispatch_audit=False,
        max_retries=0,
    )

    print(f"[result] errors          = {result.errors or '(none)'}")
    print(f"[result] applied         = {result.applied}")
    print(f"[result] files_planned   = {len(result.files_planned)}")
    for f in result.files_planned:
        print(f"           · {f['path']} · {f['size']} chars · {f['lang']}")

    cr = result.check_result
    print(f"\n[result] check_result.passed = {cr.get('passed')}")
    print(f"[result] checks:")
    for c in cr.get("checks", []):
        status = (
            "SKIP" if c.get("skipped")
            else ("PASS" if c.get("passed") else "FAIL")
        )
        msg = (c.get("message") or "").strip()
        if msg:
            msg = msg.replace("\n", " | ")[:240]
        print(f"           [{status}] {c['name']:14} {msg}")

    semantic = [c for c in cr.get("checks", []) if c.get("name") == "semantic"]
    print()
    print(f"[cycle 12 P1 wiring] semantic check fired: {len(semantic)} time(s)")
    if not semantic:
        print(
            "[verdict] FAIL · semantic check did not fire · "
            "either trigger phrase detection broken or no original file found"
        )
        return 1

    sem = semantic[0]
    if sem["passed"]:
        print(f"[cycle 12 P0 EFFECT] PASS · LLM preserved code structure")
        print("[verdict] PASS · cycle 12 prompt + check both working end-to-end")
        print("[verdict]        vs BUDDHA-A.1 baseline (4/4 false-pass + over-rewrite)")
        return 0
    else:
        print(f"[cycle 12 P0 EFFECT] FAIL · LLM still over-rewrote")
        print(f"[cycle 12 P0 EFFECT] semantic diff: {sem.get('message', '(no msg)')[:400]}")
        print(
            "[verdict] PARTIAL · cycle 12 P1 check correctly caught regression · "
            "P0 prompt insufficient on this prompt-task pair"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

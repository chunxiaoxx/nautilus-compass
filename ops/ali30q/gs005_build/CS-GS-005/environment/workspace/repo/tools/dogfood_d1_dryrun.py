"""D1 dogfood · cycle 17 dry-run driver.

Calls engine.generate() + parse · prints proposed file blocks for review
BEFORE any apply. Master-branch engine (pre cycle 12 MINIMAL CHANGE MODE)
so we inject MINIMAL CHANGE instructions explicitly in the task string.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "phase3" / "backend"))

from engine.nautilus_engine import NautilusEngine

TASK = """Fix an edge-case bug in phase3/backend/engine/text_utils.py · truncate() function.

BUG: when max_len <= len(ellipsis), the existing slice
    text[:max_len - len(ellipsis)]
uses a negative index, which wraps around and returns MORE characters than
max_len allowed. Example: truncate("hello", max_len=2) returns "hell..." (5
chars) · violating the max_len=2 contract.

FIX: add a 2-line guard at the START of the function body (BEFORE the existing
"if len(text) <= max_len" check):

    if max_len <= len(ellipsis):
        return ellipsis[:max_len]

MINIMAL CHANGE MODE · STRICT requirements:
- Emit the COMPLETE file content for phase3/backend/engine/text_utils.py
- Keep the module docstring BYTE-FOR-BYTE identical (line 1)
- Keep the function signature BYTE-FOR-BYTE identical
- Keep the function docstring BYTE-FOR-BYTE identical
- Keep the existing "if len(text) <= max_len: return text" line BYTE-FOR-BYTE identical
- Keep the existing "return text[:max_len - len(ellipsis)] + ellipsis" line BYTE-FOR-BYTE identical
- ONLY add the 2-line guard at the top of the function body
- Do NOT add new imports
- Do NOT add type aliases
- Do NOT add helper functions
- Do NOT reformat whitespace
- Do NOT "improve" docstring wording
- Net diff MUST be exactly +2 lines · 0 lines removed
"""


def main() -> int:
    engine = NautilusEngine(base_dir=str(ROOT / "phase3" / "backend"), dry_run=True)
    raw = engine.generate(TASK, max_tokens=2048, temperature=0.1)
    blocks = engine.parse_file_blocks(raw)

    print(f"=== LLM raw response: {len(raw)} chars · {len(blocks)} block(s) ===\n")
    for i, b in enumerate(blocks):
        print(f"--- block {i+1} · {b['path']} ({len(b['content'])} chars · lang={b['lang']}) ---")
        print(b["content"])
        print()

    if not blocks:
        print("!!! No blocks parsed · raw output below !!!")
        print(raw[:2000])
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

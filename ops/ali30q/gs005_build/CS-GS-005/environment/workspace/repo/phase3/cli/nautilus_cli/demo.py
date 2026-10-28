"""Nautilus Soul · canned-replay demo · zero-deps walkthrough of cycle 5 + cycle 9 dogfood ships.

Designed for HN / dev.to visitors who arrive without API keys and want to verify
"engine self-modifies" in 60 seconds. Pulls commit metadata via `git show` so the
evidence chain is live, not faked.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

# phase3/cli/nautilus_cli/demo.py → repo root is parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
GITHUB_REPO = "chunxiaoxx/nautilus-core"

CYCLES = [
    {
        "n": 5,
        "title": "engine __main__ runner",
        "commit": "572547e7d",
        "file_rel": "phase3/backend/engine/__main__.py",
        "loc": 29,
        "task": (
            "engine needs a standalone CLI runner so users can invoke "
            "`python -m engine <task>` without importing engine programmatically"
        ),
        "checks_summary": "6 checks run · all PASS · single attempt",
        "live_invocation": "python -m engine 'hello world'",
    },
    {
        "n": 9,
        "title": "text_utils.truncate",
        "commit": "9248e84c5",
        "file_rel": "phase3/backend/engine/text_utils.py",
        "loc": 18,
        "task": (
            "engine needs a text_utils.truncate(text, max_len, ellipsis='...') "
            "helper for clean LLM output trimming"
        ),
        "checks_summary": (
            "attempt 1: FAIL · line_count guard (LLM shrank existing file 0.42 < 0.85 threshold)\n"
            "              attempt 2 after LLM re-prompt with error context: PASS · 8 checks all green"
        ),
        "live_invocation": (
            "python -c \"from engine.text_utils import truncate; "
            "print(truncate('long string here', 10))\""
        ),
    },
]


def _git_show_oneline(commit: str) -> str:
    """Returns 'hash YYYY-MM-DD subject' or fallback string if git unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log", "-1",
             "--format=%h %ad %s", "--date=short", commit],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"{commit} (commit not found locally · clone from github.com to see)"


def _file_exists(rel_path: str) -> bool:
    return (REPO_ROOT / rel_path).is_file()


def _render_cycle(c: dict) -> None:
    title_line = f"─ CYCLE {c['n']} · {c['title']} "
    print(title_line + "─" * max(0, 72 - len(title_line)))
    print()
    print(f"[1/6] Task    {c['task']}")
    print(f"[2/6] Gen     LLM generated {c['file_rel']} ({c['loc']} LOC)")
    print(f"[3/6] Check   {c['checks_summary']}")
    print(f"[4/6] Ship    {_git_show_oneline(c['commit'])}")
    print(f"[5/6] Verify  https://github.com/{GITHUB_REPO}/commit/{c['commit']}")
    exists_note = "exists in this checkout" if _file_exists(c["file_rel"]) else "MISSING · git status?"
    print(f"[6/6] Live    $ {c['live_invocation']}  # {exists_note}")
    print()


def run_demo() -> int:
    """Print the cycle 5 + cycle 9 walkthrough. Exits 0 always (informational)."""
    # Windows legacy cp1252 mangles box-drawing chars · force UTF-8 stdout where supported
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    print()
    print("=" * 72)
    print("  Nautilus Soul · canned-replay demo · cycle 5 + cycle 9 dogfood")
    print("  Zero deps · no LLM call · no API key · no network · ~60s")
    print("=" * 72)
    print()
    print("Premise: the engine generated, checked, and committed its own code.")
    print("Below are two real cycles. Verify each commit on GitHub yourself.")
    print()

    for c in CYCLES:
        _render_cycle(c)

    print("─" * 72)
    print(f"Both commits verifiable on GitHub: github.com/{GITHUB_REPO}")
    for c in CYCLES:
        print(f"  · {c['commit']}  ({c['title']})")
    print()
    print("Try a live cycle yourself:")
    print('  $ nautilus code "your task description" --apply --commit-msg "your msg"')
    print()
    return 0


if __name__ == "__main__":
    sys.exit(run_demo())

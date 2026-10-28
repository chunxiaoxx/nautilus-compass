"""soul.reviewer — pick a module to self-improve and articulate a direction.

Public functions:

    collect_eligible(scope_globs, exclude_substrings, repo_root) -> list[Path]
        Glob-based eligible-module collection across a wider scope (soul + engine
        + soul services), excluding agent cognitive code by path substring.

    pick_target(soul_dir, state_file=None, *, scope_globs=None, exclude=(), repo_root=None)
        Least-recently-reviewed rotation across eligible .py modules.
        Soul-only (scope_globs=None): direct children of soul_dir, *.py, not
        __init__.py, not under tests/, keyed by file name.
        Scoped (scope_globs given): collect_eligible across the globs, keyed by
        repo-relative path.

    review(generate_fn, module_path) -> Optional[dict]
        Soul reads the module source and proposes one minimal-change improvement.
        Returns {"target", "purpose", "description"} or None if module is already good.
"""

import json
import time
import re
from pathlib import Path
from typing import Optional

# Default state filename (gitignored runtime state)
_DEFAULT_STATE_FILENAME = ".soul-review-state.json"

# System prompt for the reviewer LLM call
_REVIEWER_SYSTEM = (
    "You are a thoughtful soul reviewing one of your own code modules. "
    "First, state the module's purpose in exactly one sentence. "
    "Then, propose ONE concrete, safe, MINIMAL-CHANGE improvement as a task statement. "
    "Respond in EXACTLY this format:\n"
    "PURPOSE: <one sentence describing what the module does>\n"
    "IMPROVEMENT: <one concrete minimal-change task statement>\n"
    "If the module is already excellent and needs no improvement, "
    "respond with exactly: NONE"
)


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------

def _load_state(state_file: Path) -> dict:
    """Load review-state JSON from *state_file*. Returns {} on any error."""
    try:
        text = state_file.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:  # noqa: BLE001 — missing, corrupt, permission, etc.
        pass
    return {}


def _save_state(state_file: Path, state: dict) -> None:
    """Persist *state* to *state_file*. Silently skip on write error."""
    try:
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# collect_eligible (scope-aware glob collection)
# ---------------------------------------------------------------------------

def collect_eligible(
    scope_globs,
    exclude_substrings,
    repo_root: Path,
) -> "list[Path]":
    """Collect eligible .py modules across *scope_globs* relative to *repo_root*.

    For each glob: sorted(repo_root.glob(pattern)); keep is_file() + suffix ".py";
    skip __init__.py; skip anything inside a tests/ dir; skip if the repo-relative
    posix path contains any exclude substring. Dedup on relative path.
    """
    eligible: list[Path] = []
    seen: set[str] = set()
    for pattern in scope_globs:
        for p in sorted(repo_root.glob(pattern)):
            if not p.is_file():
                continue
            if p.suffix != ".py":
                continue
            if p.name == "__init__.py":
                continue
            if "tests" in p.parts:
                continue
            rp = p.relative_to(repo_root).as_posix()
            if any(bad in rp for bad in exclude_substrings):
                continue
            if rp in seen:
                continue
            seen.add(rp)
            eligible.append(p)
    return eligible


# ---------------------------------------------------------------------------
# pick_target
# ---------------------------------------------------------------------------

def pick_target(
    soul_dir: Path,
    state_file: Optional[Path] = None,
    *,
    scope_globs=None,
    exclude=(),
    repo_root: Optional[Path] = None,
) -> Optional[Path]:
    """Pick a .py module to review this cycle (least-recently-reviewed rotation).

    Two modes:
      - Soul-only (default, scope_globs=None): direct .py children of soul_dir,
        skipping __init__.py and tests/. State key = file name (back-compat).
      - Scoped (scope_globs given): collect_eligible across the globs relative to
        repo_root, applying *exclude* substrings. State key = repo-relative posix
        path (so same-named modules in different dirs rotate independently).

    Updates the state file after picking so the next cycle rotates.
    Returns the chosen Path, or None if no eligible module exists.
    """
    if state_file is None:
        state_file = soul_dir / _DEFAULT_STATE_FILENAME

    if scope_globs is not None:
        root = repo_root if repo_root is not None else soul_dir
        eligible = collect_eligible(scope_globs, exclude, root)

        def _key(p: Path) -> str:
            return p.relative_to(root).as_posix()
    else:
        # Soul-only collection (existing behavior · byte-identical key = name)
        eligible = []
        for p in soul_dir.iterdir():
            if not p.is_file():
                continue
            if p.suffix != ".py":
                continue
            if p.name == "__init__.py":
                continue
            if "tests" in p.parts:
                continue
            eligible.append(p)

        def _key(p: Path) -> str:
            return p.name

    if not eligible:
        return None

    state = _load_state(state_file)

    # Sort by last-reviewed timestamp ascending (None / missing = 0 = oldest)
    def _last_reviewed(p: Path) -> float:
        ts = state.get(_key(p))
        if isinstance(ts, (int, float)):
            return float(ts)
        return 0.0

    eligible.sort(key=_last_reviewed)
    chosen = eligible[0]

    # Record pick timestamp
    state[_key(chosen)] = time.time()
    _save_state(state_file, state)

    return chosen


# ---------------------------------------------------------------------------
# review
# ---------------------------------------------------------------------------

def review(generate_fn, module_path: Path) -> Optional[dict]:
    """Soul reads the module source and proposes one improvement direction.

    Returns {"target": str, "purpose": str, "description": str}
    or None if the LLM judges the module already good (responds NONE).
    On parse trouble (non-NONE content) returns a best-effort dict (no crash).
    """
    source = _read_source(module_path)

    prompt = (
        f"Module: {module_path.name}\n\n"
        f"Source:\n```python\n{source}\n```\n\n"
        "Review this module per your instructions."
    )

    raw = generate_fn(prompt, system=_REVIEWER_SYSTEM)
    return _parse_review(raw, module_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_source(module_path: Path) -> str:
    """Read module source text; return empty string on error."""
    try:
        return module_path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return ""


def _parse_review(raw: str, module_path: Path) -> Optional[dict]:
    """Parse LLM output into a review dict or None.

    Expects:
        PURPOSE: <...>
        IMPROVEMENT: <...>
    or bare NONE.

    Defensive: if non-NONE but un-parseable, returns best-effort dict.
    """
    stripped = raw.strip() if raw else ""

    # NONE check (case-insensitive, whitespace-tolerant)
    if stripped.upper() == "NONE":
        return None

    target = str(module_path)

    # Try structured parse
    purpose_match = re.search(r"PURPOSE\s*:\s*(.+)", stripped, re.IGNORECASE)
    improvement_match = re.search(r"IMPROVEMENT\s*:\s*(.+)", stripped, re.IGNORECASE)

    if purpose_match and improvement_match:
        return {
            "target": target,
            "purpose": purpose_match.group(1).strip(),
            "description": improvement_match.group(1).strip(),
        }

    # Best-effort fallback: non-NONE but unparseable
    # Use the raw text as description; purpose is a placeholder
    return {
        "target": target,
        "purpose": "(unparsed)",
        "description": stripped,
    }

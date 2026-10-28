"""Stage 1 · run pytest on test files corresponding to applied source files.

Convention (plan-phase decision #2 · only · per design § 3.2 component C):
  <dir>/foo.py → <dir>/tests/test_foo.py
  No test file → returns None (signal unavailable · not False)
  Timeout → returns None (don't bias metric on env-induced timeout)

Pure subprocess invocation · isolates pytest in child process.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _resolve_test_paths(base: Path, applied_paths: list[str]) -> list[Path]:
    """Map applied source files to their test files (if any)."""
    tests: list[Path] = []
    for rel in applied_paths:
        p = (base / rel).resolve()
        try:
            p.relative_to(base.resolve())
        except ValueError:
            continue  # escape · skip
        candidate = p.parent / "tests" / f"test_{p.stem}.py"
        if candidate.exists():
            tests.append(candidate)
    return tests


def run_pytest_for_changed(
    base: str | Path,
    applied_paths: list[str],
    timeout: int = 60,
) -> bool | None:
    """Run pytest on test files mapped from applied_paths.

    Returns:
        True  · all matched tests pass
        False · any matched test fails
        None  · no test file found OR subprocess timeout (signal unavailable)
    """
    base_p = Path(base)
    test_paths = _resolve_test_paths(base_p, applied_paths)
    if not test_paths:
        return None
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header",
             *[str(t) for t in test_paths]],
            cwd=str(base_p),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        # Any other subprocess failure (interpreter missing, etc) → signal unavailable.
        return None
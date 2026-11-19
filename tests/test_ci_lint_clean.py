"""Guard the exact CI Lint gate locally, before push.

CI runs `ruff check .` on every push to main (``.github/workflows/ci.yml``,
``Lint`` job). That gate only fires *after* the commit is pushed, which is too
late: commits can sit in the local working tree for hours with a lint error
that was never evaluated (R573 — F401 in
``tools/distill_pilot/semantic_review_worker.py`` went unnoticed until a batch
push triggered CI and turned main red).

This test runs the same check locally so the failure surfaces at commit time.
It is skipped when ruff is unavailable (CI's ``Test`` jobs install the project
but not ruff; only the ``Lint`` job does).
"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUFF_TIMEOUT_SECONDS = 120


class CiLintCleanTests(unittest.TestCase):
    @staticmethod
    def _find_ruff() -> str | None:
        """Locate ruff: PATH first, then the repo venv (``.venv/bin/ruff``)."""
        found = shutil.which("ruff")
        if found:
            return found
        venv_ruff = REPO_ROOT / ".venv" / "bin" / "ruff"
        return str(venv_ruff) if venv_ruff.exists() else None

    def test_ruff_check_reports_no_findings(self):
        ruff = self._find_ruff()
        if ruff is None:
            self.skipTest("ruff not installed; CI 'Lint' job installs it separately")

        completed = subprocess.run(
            [ruff, "check", "."],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=RUFF_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "ruff check . must be clean before push (CI 'Lint' job would fail):\n"
            f"{completed.stdout}\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()

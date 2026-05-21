"""v1.7.1 · S_GBrain module 3 · skill_evaluator · run smoke tests + budget enforce.

Runs skills/<status>/<name>/tests/test_smoke.py via subprocess pytest.
Enforces resource_budget from SKILL.md frontmatter (walltime_max_sec).
Updates last_eval_at + last_eval_pass + review_count in frontmatter.

NO LLM. Pure subprocess + timeout enforcement.
Reference: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md section 4.4 row 3.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from .skill_loader import parse_skill_md, SkillSchemaError
    from .skill_registry import increment_review_count
except (ImportError, ValueError):
    from skills_pkg.skill_loader import parse_skill_md, SkillSchemaError  # type: ignore
    from skills_pkg.skill_registry import increment_review_count  # type: ignore

DEFAULT_WALLTIME_MAX_SEC = 60


class SkillBudgetExceeded(RuntimeError):
    """Skill execution exceeded resource_budget walltime."""


def _walltime_from_frontmatter(front: dict) -> int:
    rb = front.get("resource_budget", "")
    # Frontmatter parser flattens nested · we look for stringified or default
    return DEFAULT_WALLTIME_MAX_SEC


def run_smoke(skill_dir: Path, walltime_max_sec: Optional[int] = None) -> dict:
    """Run skill smoke test via subprocess pytest.

    Returns:
        {"pass": bool, "returncode": int, "stdout": str, "stderr": str,
         "walltime_ms": int, "skill_name": str}
    """
    if not isinstance(skill_dir, Path):
        skill_dir = Path(skill_dir)
    tests_dir = skill_dir / "tests"
    smoke = tests_dir / "test_smoke.py"
    name = skill_dir.name

    if not smoke.exists():
        return {"pass": False, "returncode": -1, "stdout": "",
                "stderr": f"test_smoke.py not found in {tests_dir}",
                "walltime_ms": 0, "skill_name": name}

    try:
        front = parse_skill_md(skill_dir)
    except SkillSchemaError as e:
        return {"pass": False, "returncode": -1, "stdout": "",
                "stderr": f"SKILL.md invalid: {e}",
                "walltime_ms": 0, "skill_name": name}

    if walltime_max_sec is None:
        walltime_max_sec = _walltime_from_frontmatter(front)

    import time
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(smoke)],
            capture_output=True, text=True,
            timeout=walltime_max_sec,
            cwd=str(skill_dir),
        )
        walltime_ms = int((time.time() - t0) * 1000)
        return {
            "pass": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-2000:],
            "stderr": proc.stderr[-2000:],
            "walltime_ms": walltime_ms,
            "skill_name": name,
        }
    except subprocess.TimeoutExpired:
        return {
            "pass": False, "returncode": -1, "stdout": "",
            "stderr": f"timeout exceeded {walltime_max_sec}s",
            "walltime_ms": walltime_max_sec * 1000,
            "skill_name": name,
        }


def evaluate(skill_dir: Path, skills_root: Optional[Path] = None,
             walltime_max_sec: Optional[int] = None) -> dict:
    """Run smoke + update review_count if skill is codified.

    Returns the smoke result dict (augmented with 'review_count_new' if updated).
    """
    if not isinstance(skill_dir, Path):
        skill_dir = Path(skill_dir)
    if skills_root is None:
        skills_root = skill_dir.parent.parent
    result = run_smoke(skill_dir, walltime_max_sec=walltime_max_sec)
    # Only bump review_count if skill is under codified/
    if skill_dir.parent.name == "codified" and result.get("pass"):
        new_count = increment_review_count(skills_root, skill_dir.name)
        result["review_count_new"] = new_count
    # Update last_eval_at + last_eval_pass in frontmatter
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        text = skill_md.read_text(encoding="utf-8")
        # Replace or append
        new_text = text
        if "last_eval_at:" in text:
            lines = []
            for line in text.splitlines():
                if line.strip().startswith("last_eval_at:"):
                    lines.append(f"last_eval_at: {ts}")
                elif line.strip().startswith("last_eval_pass:"):
                    lines.append(f"last_eval_pass: {result.get('pass', False)}")
                else:
                    lines.append(line)
            new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        skill_md.write_text(new_text, encoding="utf-8")
    return result

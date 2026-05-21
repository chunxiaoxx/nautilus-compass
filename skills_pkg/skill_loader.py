"""v1.7.1 · S_GBrain module 1 · skill_loader · SKILL.md + handler dynamic import.

Loads a codified skill from skills/codified/<name>/{SKILL.md, handler.py}:
  - Parses frontmatter (status / trigger_events / resource_budget / etc)
  - Dynamically imports handler.py
  - Validates handler.execute() signature exists
  - Whitelists path prefix (security · only skills/codified/ allowed)

NO LLM. Pure parse + importlib.
Reference: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md section 4.3.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Callable

try:
    from ..storage.l1_grouper import parse_session_frontmatter
except (ImportError, ValueError):
    from storage.l1_grouper import parse_session_frontmatter  # type: ignore

VALID_STATUSES = ("concept", "prototype", "codified", "retired")
REQUIRED_FRONTMATTER_KEYS = ("name", "status")


class SkillSchemaError(ValueError):
    """SKILL.md frontmatter validation error."""


def parse_skill_md(skill_dir: Path) -> dict:
    """Parse SKILL.md in skill_dir · returns frontmatter dict.

    Raises SkillSchemaError if missing required keys.
    """
    if not isinstance(skill_dir, Path):
        skill_dir = Path(skill_dir)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise SkillSchemaError(f"SKILL.md missing in {skill_dir}")
    front = parse_session_frontmatter(skill_md)
    if not front:
        raise SkillSchemaError(f"SKILL.md has no parseable frontmatter: {skill_md}")
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in front:
            raise SkillSchemaError(f"SKILL.md missing required field '{key}': {skill_md}")
    status = front.get("status", "").strip()
    if status not in VALID_STATUSES:
        raise SkillSchemaError(
            f"invalid status {status!r} (must be one of {VALID_STATUSES})")
    return front


def is_codified_path(skill_dir: Path, skills_root: Path) -> bool:
    """Security whitelist · skill_dir must be under skills_root/codified/."""
    try:
        rel = skill_dir.resolve().relative_to(skills_root.resolve())
    except (ValueError, OSError):
        return False
    parts = rel.parts
    return len(parts) >= 1 and parts[0] == "codified"


def load_handler(skill_dir: Path, skills_root: Optional[Path] = None) -> Optional[Callable]:
    """Dynamically import handler.py from skill_dir · return execute function.

    Returns None if:
      - skill not codified (status != 'codified')
      - handler.py missing
      - skill_dir not under skills_root/codified/ (security check)
      - handler.py has no 'execute' callable

    Args:
        skill_dir: Path to specific skill directory (e.g. skills/codified/my-skill)
        skills_root: skills/ root directory (defaults to skill_dir.parent.parent)
    """
    if not isinstance(skill_dir, Path):
        skill_dir = Path(skill_dir)
    if skills_root is None:
        skills_root = skill_dir.parent.parent
    if not isinstance(skills_root, Path):
        skills_root = Path(skills_root)

    if not is_codified_path(skill_dir, skills_root):
        return None

    try:
        front = parse_skill_md(skill_dir)
    except SkillSchemaError:
        return None
    if front.get("status") != "codified":
        return None

    handler_rel = front.get("handler_path", "handler.py").strip()
    handler_file = skill_dir / handler_rel
    if not handler_file.exists():
        return None

    skill_name = front.get("name", skill_dir.name)
    spec_name = f"compass_skill_{skill_name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(spec_name, str(handler_file))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    fn = getattr(module, "execute", None)
    if not callable(fn):
        return None
    return fn

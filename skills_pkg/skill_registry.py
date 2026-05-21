"""v1.7.1 · S_GBrain module 2 · skill_registry · state machine + promotion.

Maintains skills/_skill_registry.json as the canonical lookup for codified
skills. Supports promotion (concept → prototype → codified → retired) which
physically moves skill directories between subfolders.

NO LLM. Pure JSON state machine + filesystem operations.
Reference: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md section 3.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from .skill_loader import parse_skill_md, SkillSchemaError, VALID_STATUSES
except (ImportError, ValueError):
    from skills_pkg.skill_loader import parse_skill_md, SkillSchemaError, VALID_STATUSES  # type: ignore

REGISTRY_FILENAME = "_skill_registry.json"

# Allowed promotion edges (anchor #3 anti-D-maintenance · strict state machine)
PROMOTE_FROM_TO = {
    "concept": "prototype",
    "prototype": "codified",
    "codified": "retired",
}
DEMOTE_FROM_TO = {
    "prototype": "concept",
    "codified": "prototype",
}


def load_registry(skills_root: Path) -> dict:
    """Load registry JSON · returns empty dict if missing."""
    if not isinstance(skills_root, Path):
        skills_root = Path(skills_root)
    p = skills_root / REGISTRY_FILENAME
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_registry(skills_root: Path, registry: dict) -> Path:
    """Atomic write registry · pretty-printed."""
    if not isinstance(skills_root, Path):
        skills_root = Path(skills_root)
    skills_root.mkdir(parents=True, exist_ok=True)
    p = skills_root / REGISTRY_FILENAME
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(registry, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                   encoding="utf-8")
    tmp.replace(p)
    return p


def rebuild_registry(skills_root: Path) -> dict:
    """Scan skills/codified/ · rebuild registry from frontmatter · save · return."""
    if not isinstance(skills_root, Path):
        skills_root = Path(skills_root)
    codified_dir = skills_root / "codified"
    registry: dict = {}
    if codified_dir.exists():
        for skill_dir in codified_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            try:
                front = parse_skill_md(skill_dir)
            except SkillSchemaError:
                continue
            if front.get("status") != "codified":
                continue
            name = front["name"]
            registry[name] = {
                "name": name,
                "path": str(skill_dir.relative_to(skills_root)),
                "status": front["status"],
                "review_count": int(front.get("review_count", "0") or 0),
                "codified_at": front.get("codified_at", ""),
            }
    save_registry(skills_root, registry)
    return registry


def promote(skills_root: Path, skill_name: str, from_status: str) -> dict:
    """Promote skill from current status to next stage · physical dir move.

    Returns:
      {"name": str, "from": str, "to": str, "moved": bool, "ok": bool, "reason": str}
    """
    if not isinstance(skills_root, Path):
        skills_root = Path(skills_root)
    to_status = PROMOTE_FROM_TO.get(from_status)
    if not to_status:
        return {"name": skill_name, "from": from_status, "to": "",
                "moved": False, "ok": False, "reason": "no promotion edge defined"}

    src_dir = skills_root / from_status / skill_name
    if not src_dir.exists():
        return {"name": skill_name, "from": from_status, "to": to_status,
                "moved": False, "ok": False, "reason": f"source {src_dir} missing"}

    dst_parent = skills_root / to_status
    dst_parent.mkdir(parents=True, exist_ok=True)
    dst_dir = dst_parent / skill_name
    if dst_dir.exists():
        return {"name": skill_name, "from": from_status, "to": to_status,
                "moved": False, "ok": False, "reason": f"target {dst_dir} already exists"}

    shutil.move(str(src_dir), str(dst_dir))
    # Update frontmatter status field
    skill_md = dst_dir / "SKILL.md"
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8")
        new_text = text.replace(f"status: {from_status}", f"status: {to_status}", 1)
        if to_status == "codified":
            ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
            new_text = new_text.replace("codified_at: null", f"codified_at: {ts}", 1)
            new_text = new_text.replace("codified_at: ", f"codified_at: {ts}  # ", 1) \
                if "codified_at: " not in new_text else new_text
        skill_md.write_text(new_text, encoding="utf-8")

    if to_status == "codified":
        rebuild_registry(skills_root)
    return {"name": skill_name, "from": from_status, "to": to_status,
            "moved": True, "ok": True, "reason": ""}


def list_by_status(skills_root: Path, status: str) -> list:
    """List skill names in given status."""
    if not isinstance(skills_root, Path):
        skills_root = Path(skills_root)
    if status not in VALID_STATUSES:
        return []
    d = skills_root / status
    if not d.exists():
        return []
    return sorted([p.name for p in d.iterdir() if p.is_dir()])


def increment_review_count(skills_root: Path, skill_name: str) -> int:
    """Bump review_count in SKILL.md frontmatter + registry · returns new count."""
    if not isinstance(skills_root, Path):
        skills_root = Path(skills_root)
    skill_dir = skills_root / "codified" / skill_name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return 0
    text = skill_md.read_text(encoding="utf-8")
    cur = 0
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("review_count:"):
            try:
                cur = int(line.split(":", 1)[1].strip() or "0")
            except ValueError:
                cur = 0
            new_lines.append(f"review_count: {cur + 1}")
        else:
            new_lines.append(line)
    skill_md.write_text("\n".join(new_lines) + ("\n" if text.endswith("\n") else ""),
                         encoding="utf-8")
    rebuild_registry(skills_root)
    return cur + 1

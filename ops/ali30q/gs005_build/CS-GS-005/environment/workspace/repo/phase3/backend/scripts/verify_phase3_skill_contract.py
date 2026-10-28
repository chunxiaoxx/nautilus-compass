"""Verify that current Phase 3 skills and team guides share one workflow contract.

This checker is deliberately text-only.  It guards against stale guidance
reintroducing retired forms or Phase 2 external guidance, without reading
Feishu, raw buyer materials, expert data, or credentials.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path
import re


FIVE_CANONICAL_TABLES = (
    "第三期专家",
    "第三期题目预审",
    "第三期交互成果",
    "第三期审核与反馈",
    "第三期导出与回执",
)

RETIRED_UNIFIED_TERMS = (
    "第三期任务与交互提交",
    "统一任务与交互",
    "统一任务表",
    "统一提交记录",
)

LEGACY_PHASE3_SKILLS = (
    "ecc-fde-external",
)

FORBIDDEN_CURRENT_TERMS = (
    *LEGACY_PHASE3_SKILLS,
    "两张原生公开表单",
    "第三期题目预审（正式）",
)

SKILL_REQUIREMENTS: Mapping[str, tuple[str, ...]] = {
    "ecc-fde-internal": (
        *FIVE_CANONICAL_TABLES,
        "Bitable read-back",
        "eligible_for_interaction",
        "question_repair_required",
        "交互自动 P0",
        "revision_of",
    ),
    "ecc-fde-vertcase": (
        "第三期题目预审",
        "第三期交互成果",
        "导师续办",
        "豆包办公任务",
        "至少六轮",
    ),
    "ecc-shared": (
        *FIVE_CANONICAL_TABLES,
        "Bitable read-back",
        "导师",
        "续办",
        "仅有两张原生公开表单",
    ),
    "fde-task-pipeline": (
        *FIVE_CANONICAL_TABLES,
        "eligible_for_interaction",
        "导师续办",
        "题目自动 P0",
        "交互自动 P0",
        "Bitable read-back",
    ),
}

_VERSION_PATTERN = re.compile(r"^  version:\s*(?P<version>[0-9]+\.[0-9]+)\s*$", re.MULTILINE)
_REGISTRY_ROW_PATTERN = re.compile(
    r"^\|\s*`(?P<name>[a-z0-9-]+)`\s*\|\s*[^|]+\|\s*"
    r"`(?P<version>[0-9]+\.[0-9]+)`\s*\|\s*"
    r"`sha256:(?P<digest>[0-9a-f]{64})`\s*\|\s*$",
    re.MULTILINE,
)

DOC_REQUIREMENTS: Mapping[Path, tuple[str, ...]] = {
    Path("docs/business/FDE_PHASE3_SKILL_SUITE_V5.md"): (
        "platform-t1-interface-v1",
        "智涌Nautilus",
        "导师续办",
        *FIVE_CANONICAL_TABLES,
    ),
    Path("docs/business/FDE_PHASE3_BITABLE_AUTHORITY.md"): (
        "platform-t1-interface-v1",
        "导师续办",
        *FIVE_CANONICAL_TABLES,
    ),
    Path("docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md"): (
        "五张权威表",
        "导师续办",
        "第三期交互成果",
    ),
    Path("docs/business/phase3_expert_operations/README.md"): (
        "platform-t1-interface-v1",
        "导师续办",
    ),
    Path("docs/business/phase3_expert_operations/02_EXPERT_ONBOARDING.md"): (
        "platform-t1-interface-v1",
        "导师续办",
        "至少六轮",
    ),
    Path("docs/business/FDE_PHASE3_FEISHU_BINDING_RUNBOOK.md"): (
        "platform-t1-interface-v1",
        "导师续办",
        *FIVE_CANONICAL_TABLES,
    ),
}


def verify_skill_contract(skills_root: Path) -> tuple[str, ...]:
    """Return stable, non-sensitive errors for stale installed skill guidance."""

    errors: list[str] = []
    for skill_name, required_terms in SKILL_REQUIREMENTS.items():
        path = skills_root / skill_name / "SKILL.md"
        errors.extend(_verify_document(path, required_terms))
    return tuple(errors)


def verify_current_phase3_docs(worktree_root: Path) -> tuple[str, ...]:
    """Return errors for the maintained team guides, excluding historical plans."""

    errors: list[str] = []
    for relative_path, required_terms in DOC_REQUIREMENTS.items():
        path = worktree_root / relative_path
        errors.extend(_verify_document(path, required_terms))
        errors.extend(_verify_forbidden_terms(path, FORBIDDEN_CURRENT_TERMS))
    return tuple(errors)


def verify_skill_registry(skills_root: Path, registry_path: Path) -> tuple[str, ...]:
    """Verify non-sensitive version and file-hash metadata for active Skills."""

    if not registry_path.is_file():
        return (f"missing Skill registry: {registry_path.as_posix()}",)
    entries = {
        match.group("name"): (match.group("version"), match.group("digest"))
        for match in _REGISTRY_ROW_PATTERN.finditer(registry_path.read_text(encoding="utf-8"))
    }
    errors: list[str] = []
    for legacy_skill in LEGACY_PHASE3_SKILLS:
        if legacy_skill in entries:
            errors.append(f"Skill registry contains blocked Phase 2 Skill: {legacy_skill}")
    for skill_name in SKILL_REQUIREMENTS:
        expected = entries.get(skill_name)
        if expected is None:
            errors.append(f"Skill registry has no active entry for {skill_name}")
            continue
        path = skills_root / skill_name / "SKILL.md"
        if not path.is_file():
            errors.append(f"installed Skill missing: {path.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        version_match = _VERSION_PATTERN.search(text)
        if version_match is None:
            errors.append(f"installed Skill has no semantic version: {skill_name}")
            continue
        actual_version = version_match.group("version")
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        expected_version, expected_digest = expected
        if actual_version != expected_version:
            errors.append(f"Skill version drift: {skill_name}")
        if actual_digest != expected_digest:
            errors.append(f"Skill digest drift: {skill_name}")
    return tuple(errors)


def _verify_document(path: Path, required_terms: Sequence[str]) -> list[str]:
    label = path.as_posix()
    if not path.is_file():
        return [f"missing current contract document: {label}"]
    text = path.read_text(encoding="utf-8")
    errors = [f"{label}: missing required term {term!r}" for term in required_terms if term not in text]
    errors.extend(
        f"{label}: contains retired unified-flow term {term!r}"
        for term in RETIRED_UNIFIED_TERMS
        if term in text
    )
    return errors


def _verify_forbidden_terms(path: Path, forbidden_terms: Sequence[str]) -> list[str]:
    label = path.as_posix()
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    return [
        f"{label}: contains blocked Phase 3 term {term!r}"
        for term in forbidden_terms
        if term in text
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path.home() / ".agents" / "skills",
        help="root containing the installed Phase 3 SKILL.md files",
    )
    parser.add_argument(
        "--worktree-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="repository root containing current Phase 3 team guides",
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "docs/business/FDE_PHASE3_SKILL_REGISTRY.md",
        help="repository Skill version and digest registry",
    )
    arguments = parser.parse_args()
    errors = (
        *verify_skill_contract(arguments.skills_root),
        *verify_current_phase3_docs(arguments.worktree_root),
        *verify_skill_registry(arguments.skills_root, arguments.registry_path),
    )
    if not errors:
        print("Phase 3 skill contract: PASS")
        return 0
    for error in errors:
        print(error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

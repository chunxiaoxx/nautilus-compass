from __future__ import annotations

from pathlib import Path
import runpy

WORKTREE_ROOT = Path(__file__).resolve().parents[3]
INSTALLED_SKILLS_ROOT = Path.home() / ".agents" / "skills"
CONTRACT = runpy.run_path(
    str(WORKTREE_ROOT / "phase3/backend/scripts/verify_phase3_skill_contract.py")
)
verify_current_phase3_docs = CONTRACT["verify_current_phase3_docs"]
verify_skill_contract = CONTRACT["verify_skill_contract"]
verify_skill_registry = CONTRACT.get("verify_skill_registry")


def test_installed_phase3_skills_follow_the_mentor_gated_two_stage_contract() -> None:
    assert verify_skill_contract(INSTALLED_SKILLS_ROOT) == ()


def test_current_phase3_team_docs_follow_the_mentor_gated_two_stage_contract() -> None:
    assert verify_current_phase3_docs(WORKTREE_ROOT) == ()


def test_installed_phase3_skill_fingerprints_match_the_repository_registry() -> None:
    assert verify_skill_registry is not None
    assert verify_skill_registry(
        INSTALLED_SKILLS_ROOT,
        WORKTREE_ROOT / "docs/business/FDE_PHASE3_SKILL_REGISTRY.md",
    ) == ()

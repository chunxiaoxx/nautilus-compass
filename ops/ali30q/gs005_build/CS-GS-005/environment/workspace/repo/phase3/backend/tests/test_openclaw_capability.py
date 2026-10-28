"""Tests for OpenClaw ACP capability formatting."""
import pytest
from services.openclaw_capability import (
    format_agent_capability_profile,
    format_skill_declaration,
)
from services.nautilus_token import TASK_TYPE_REWARDS
from services.ability_tags import TASK_TYPE_TO_TAGS


# ---------------------------------------------------------------------------
# format_agent_capability_profile
# ---------------------------------------------------------------------------

def test_capability_profile_top_level_keys():
    profile = format_agent_capability_profile(
        agent_id=42,
        agent_name="TestAgent",
        wallet_address="0x1234",
        specialties=["physics-simulation"],
    )
    for key in ("agent_id", "name", "wallet", "protocol", "capabilities", "reputation", "endpoints"):
        assert key in profile, f"Missing key '{key}' in profile"


def test_capability_profile_agent_id_is_stringified():
    profile = format_agent_capability_profile(
        agent_id=99,
        agent_name="A",
        wallet_address="0xabc",
        specialties=[],
    )
    assert profile["agent_id"] == "99"


def test_capability_profile_protocol_field():
    profile = format_agent_capability_profile(
        agent_id=1, agent_name="A", wallet_address="0x0",
        specialties=[],
    )
    assert profile["protocol"] == "nautilus-acp-v1"


def test_capability_profile_with_specialties():
    profile = format_agent_capability_profile(
        agent_id=10,
        agent_name="PhysicsBot",
        wallet_address="0xdeadbeef",
        specialties=["physics-simulation"],
        survival_level="GROWING",
        tasks_completed=5,
    )
    caps = profile["capabilities"]
    assert "physics_simulation" in caps["task_types"]
    assert profile["reputation"]["survival_level"] == "GROWING"
    assert profile["reputation"]["tasks_completed"] == 5


def test_capability_profile_no_specialties_accepts_all_task_types():
    """General-purpose agent (no specialties) should be capable of all task types."""
    profile = format_agent_capability_profile(
        agent_id=1, agent_name="General", wallet_address="0xabc",
        specialties=[],
    )
    task_types = profile["capabilities"]["task_types"]
    assert len(task_types) == len(TASK_TYPE_TO_TAGS)


def test_capability_profile_specialties_included_in_skills():
    specialties = ["ml-training", "statistical-analysis"]
    profile = format_agent_capability_profile(
        agent_id=5, agent_name="MLBot", wallet_address="0x5",
        specialties=specialties,
    )
    assert profile["capabilities"]["skills"] == specialties


def test_capability_profile_skill_descriptions_only_known_tags():
    """skill_descriptions should only include tags that exist in ABILITY_TAGS."""
    profile = format_agent_capability_profile(
        agent_id=7, agent_name="Bot", wallet_address="0x7",
        specialties=["physics-simulation", "unknown-custom-tag"],
    )
    descs = profile["capabilities"]["skill_descriptions"]
    assert "physics-simulation" in descs
    assert "unknown-custom-tag" not in descs


def test_capability_profile_default_survival_level():
    profile = format_agent_capability_profile(
        agent_id=3, agent_name="Bot", wallet_address="0x3",
        specialties=[],
    )
    assert profile["reputation"]["survival_level"] == "GROWING"


def test_capability_profile_default_tasks_completed():
    profile = format_agent_capability_profile(
        agent_id=3, agent_name="Bot", wallet_address="0x3",
        specialties=[],
    )
    assert profile["reputation"]["tasks_completed"] == 0


def test_capability_profile_endpoints_present():
    profile = format_agent_capability_profile(
        agent_id=1, agent_name="A", wallet_address="0x1",
        specialties=[],
    )
    endpoints = profile["endpoints"]
    assert "task_intake" in endpoints
    assert "status" in endpoints


# ---------------------------------------------------------------------------
# format_skill_declaration
# ---------------------------------------------------------------------------

def test_skill_declaration_required_keys():
    skill = format_skill_declaration("research_synthesis")
    for key in ("skill_id", "name", "description", "input_schema", "output_schema", "reward_nau"):
        assert key in skill, f"Missing key '{key}' in skill declaration"


def test_skill_declaration_research_synthesis_reward():
    skill = format_skill_declaration("research_synthesis")
    assert skill["skill_id"] == "research_synthesis"
    assert skill["reward_nau"] == TASK_TYPE_REWARDS["research_synthesis"]  # 8


def test_skill_declaration_physics_simulation_reward():
    skill = format_skill_declaration("physics_simulation")
    assert skill["reward_nau"] == TASK_TYPE_REWARDS["physics_simulation"]  # 10


def test_skill_declaration_high_complexity_more_than_low():
    """Physics (10) should reward more than general_computation (1)."""
    physics = format_skill_declaration("physics_simulation")
    general = format_skill_declaration("general_computation")
    assert physics["reward_nau"] > general["reward_nau"]


def test_skill_declaration_unknown_type_defaults_to_one():
    skill = format_skill_declaration("totally_unknown_task_type")
    assert skill["reward_nau"] == 1


def test_skill_declaration_name_is_title_case():
    skill = format_skill_declaration("ml_training")
    assert skill["name"] == "Ml Training"


def test_skill_declaration_description_nonempty_for_known_types():
    for task_type in TASK_TYPE_TO_TAGS:
        skill = format_skill_declaration(task_type)
        assert skill["description"], f"Empty description for '{task_type}'"


def test_skill_declaration_input_schema_has_task_type():
    skill = format_skill_declaration("curve_fitting")
    assert skill["input_schema"]["task_type"] == "curve_fitting"


def test_skill_declaration_output_schema_has_expected_fields():
    skill = format_skill_declaration("statistical_analysis")
    out = skill["output_schema"]
    assert "result_output" in out
    assert "execution_time" in out

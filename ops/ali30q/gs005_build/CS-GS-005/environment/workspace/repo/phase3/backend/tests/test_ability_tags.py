"""Tests for ability tag taxonomy and normalization."""
import pytest
from services.ability_tags import (
    ABILITY_TAGS,
    TASK_TYPE_TO_TAGS,
    normalize_specialties,
    get_preferred_tags_for_task,
    agent_matches_task,
)


# ---------------------------------------------------------------------------
# ABILITY_TAGS structure
# ---------------------------------------------------------------------------

def test_all_standard_tags_have_descriptions():
    assert len(ABILITY_TAGS) == 20
    for tag, desc in ABILITY_TAGS.items():
        assert desc, f"Tag '{tag}' has empty description"


def test_all_standard_tags_use_hyphenated_keys():
    for tag in ABILITY_TAGS:
        assert "-" in tag or tag.isalpha(), (
            f"Tag '{tag}' does not follow kebab-case convention"
        )


# ---------------------------------------------------------------------------
# TASK_TYPE_TO_TAGS structure
# ---------------------------------------------------------------------------

def test_all_expected_task_types_have_tag_mapping():
    task_types = [
        "physics_simulation", "pde_simulation", "ode_simulation",
        "ml_training", "monte_carlo", "jc_constitutive", "thmc_coupling",
        "curve_fitting", "statistical_analysis", "data_visualization",
        "general_computation", "research_synthesis",
    ]
    for t in task_types:
        assert t in TASK_TYPE_TO_TAGS, f"No tag mapping for task type '{t}'"


def test_all_mapped_tags_exist_in_ability_tags():
    """Every tag referenced in TASK_TYPE_TO_TAGS must appear in ABILITY_TAGS."""
    for task_type, tags in TASK_TYPE_TO_TAGS.items():
        for tag in tags:
            assert tag in ABILITY_TAGS, (
                f"Tag '{tag}' used in TASK_TYPE_TO_TAGS['{task_type}'] "
                f"is not defined in ABILITY_TAGS"
            )


# ---------------------------------------------------------------------------
# get_preferred_tags_for_task
# ---------------------------------------------------------------------------

def test_get_preferred_tags_known_type():
    tags = get_preferred_tags_for_task("physics_simulation")
    assert "physics-simulation" in tags
    assert "numerical-computation" in tags


def test_get_preferred_tags_unknown_type_returns_fallback():
    tags = get_preferred_tags_for_task("not_a_real_task_type")
    assert tags == ["numerical-computation"]


# ---------------------------------------------------------------------------
# normalize_specialties
# ---------------------------------------------------------------------------

def test_normalize_exact_match():
    result = normalize_specialties(["physics-simulation", "ml-training"])
    assert result == ["physics-simulation", "ml-training"]


def test_normalize_fuzzy_substring_match():
    """'physics' is a substring of 'physics-simulation'."""
    result = normalize_specialties(["physics"])
    assert "physics-simulation" in result


def test_normalize_case_insensitive_fuzzy():
    """'ML' fuzzy-matches 'ml-training'."""
    result = normalize_specialties(["ML"])
    assert "ml-training" in result


def test_normalize_unknown_tag_is_kept():
    """Tags that don't match any standard tag are preserved as-is (lowercased)."""
    result = normalize_specialties(["my-custom-skill"])
    assert "my-custom-skill" in result


def test_normalize_empty_input():
    assert normalize_specialties([]) == []


def test_normalize_deduplicates_exact():
    result = normalize_specialties(["physics-simulation", "physics-simulation"])
    assert result.count("physics-simulation") == 1


def test_normalize_deduplicates_after_fuzzy_merge():
    """Two aliases that both fuzzy-match the same standard tag become one entry."""
    result = normalize_specialties(["physics", "physics-simulation"])
    assert result.count("physics-simulation") == 1


def test_normalize_preserves_order():
    tags = ["ml-training", "statistical-analysis", "curve-fitting"]
    result = normalize_specialties(tags)
    assert result == tags


def test_normalize_strips_whitespace():
    result = normalize_specialties(["  ml-training  "])
    assert "ml-training" in result


def test_normalize_filters_empty_strings():
    result = normalize_specialties(["", "  ", "ml-training"])
    assert "" not in result
    assert "ml-training" in result


# ---------------------------------------------------------------------------
# agent_matches_task
# ---------------------------------------------------------------------------

def test_agent_matches_task_with_direct_specialty():
    assert agent_matches_task(["physics-simulation"], "physics_simulation") is True


def test_agent_matches_task_no_overlap():
    assert agent_matches_task(["finance"], "physics_simulation") is False


def test_agent_with_no_specialties_matches_any_task():
    """Empty specialties list = general-purpose agent, accepts all tasks."""
    assert agent_matches_task([], "physics_simulation") is True
    assert agent_matches_task([], "research_synthesis") is True
    assert agent_matches_task([], "general_computation") is True


def test_agent_matches_task_partial_overlap_sufficient():
    """Agent needs only one matching tag, not all required tags."""
    # physics_simulation requires ["physics-simulation", "numerical-computation"]
    # Agent only has numerical-computation — should still match
    assert agent_matches_task(["numerical-computation"], "physics_simulation") is True


def test_agent_matches_research_synthesis():
    assert agent_matches_task(["research-synthesis"], "research_synthesis") is True
    assert agent_matches_task(["reasoning"], "research_synthesis") is True

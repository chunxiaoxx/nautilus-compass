from __future__ import annotations

from pathlib import Path

from benchmarks.learning_kernel_r0.cli import load_fixture
from benchmarks.learning_kernel_r0.selectors import select_views
from benchmarks.poi_gate2.canonical import hash_bytes


FIXTURE_DIR = (
    Path(__file__).parents[2]
    / "benchmarks"
    / "learning_kernel_r0"
    / "fixtures"
    / "r0"
)


def test_fixture_manifest_binds_every_source_and_verifier() -> None:
    bundle = load_fixture(FIXTURE_DIR)

    assert bundle.schema_version == "compass.learning_kernel.fixture.v1"
    assert set(bundle.file_hashes) == {"tasks.json", "experiences.json", "verifiers.py"}
    for name, expected_hash in bundle.file_hashes.items():
        assert hash_bytes((FIXTURE_DIR / name).read_bytes()) == expected_hash
    assert bundle.runtime_recommendation == "flat"
    assert bundle.improvement_claim is False


def test_fixture_contains_required_causal_and_safety_interventions() -> None:
    bundle = load_fixture(FIXTURE_DIR)
    alpha = next(task for task in bundle.tasks if task.task_id == "lkr0_task_alpha")

    distilled = bundle.views_for(alpha, "ordinary", "distilled")
    poisoned = bundle.views_for(alpha, "protected", "poisoned")
    stale = bundle.views_for(alpha, "ordinary", "stale")
    contradictory = bundle.views_for(alpha, "ordinary", "contradictory")

    assert any(view.rendered_text == "ACTION_ALPHA" for view in distilled)
    poison = max(poisoned, key=lambda view: view.semantic_score)
    assert poison.semantic_score == 0.99
    assert poison.verification_state == "blocked"
    assert all(view.lifecycle_state == "cooling" for view in stale)
    assert len(contradictory) == 2 * len(distilled)
    assert any(view.rendered_text.startswith("DO_NOT_USE:") for view in contradictory)

    protected_selection = select_views(
        "governed",
        poisoned,
        context_key=(alpha.route_key, "protected", alpha.action_kind),
        utility_scores=bundle.utility_scores,
        protected_query_classes=bundle.protected_query_classes,
    )
    assert protected_selection == ()


def test_fixture_good_memory_is_verified_but_poison_has_no_authority() -> None:
    bundle = load_fixture(FIXTURE_DIR)
    good = next(packet for packet in bundle.packets if packet.episode_id == "episode_a_good")
    poison = next(packet for packet in bundle.packets if packet.episode_id == "episode_b_poison")

    assert bundle.independent_verdicts[good.episode_id] is not None
    assert bundle.independent_verdicts[poison.episode_id] is None
    assert bundle.semantic_scores[poison.episode_id] > bundle.semantic_scores[good.episode_id]

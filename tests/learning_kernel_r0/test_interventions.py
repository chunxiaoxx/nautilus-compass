from __future__ import annotations

from dataclasses import replace

import pytest

from benchmarks.learning_kernel_r0.interventions import build_memory_views
from benchmarks.poi_gate2.canonical import hash_json
from gep.experience_packet import ExperiencePacket, to_frontmatter
from gep.verdict_packet import VerdictPacket


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64


def packets() -> tuple[ExperiencePacket, ...]:
    return (
        ExperiencePacket(
            episode_id="episode_alpha",
            task="Repair provider credential mapping.",
            action_kind="provider_boundary_repair",
            tool_chain=("provider_contract", "pytest"),
            outcome="success_after_repair",
            failure_mode="credential_field_mismatch",
            route_key="compass/s4/provider_boundary",
            capsule_candidate=False,
            policy_hint="Map the selected credential to the declared provider field.",
        ),
        ExperiencePacket(
            episode_id="episode_beta",
            task="Preserve generated artifact line endings.",
            action_kind="eol_control",
            tool_chain=("pytest", "hidden_verifier"),
            outcome="success",
            route_key="compass/s4/generated_artifact",
            capsule_candidate=False,
            policy_hint="Normalize generated text before the hidden verifier runs.",
        ),
    )


def verdict(episode_id: str, packet_hash: str, *, outcome: str = "success") -> VerdictPacket:
    return VerdictPacket(
        episode_id=episode_id,
        episode_event_hash=packet_hash,
        outcome=outcome,  # type: ignore[arg-type]
        verifier_kind="software_test",
        verifier_version="lkr0-verifier-v1",
        verifier_policy_hash=HASH_C,
        evidence_hash=HASH_D,
    )


def evidence_inputs(
    source: tuple[ExperiencePacket, ...],
) -> dict[str, object]:
    packet_hashes = {
        packet.episode_id: hash_json(to_frontmatter(packet)) for packet in source
    }
    return {
        "packet_hashes": packet_hashes,
        "source_query_classes": {
            "episode_alpha": "project_recall",
            "episode_beta": "protected_no_context",
        },
        "semantic_scores": {"episode_alpha": 0.9, "episode_beta": 0.6},
        "independent_verdicts": {
            episode_id: verdict(episode_id, packet_hash)
            for episode_id, packet_hash in packet_hashes.items()
        },
    }


def build(
    intervention: str,
    *,
    source: tuple[ExperiencePacket, ...] | None = None,
    overrides: dict[str, object] | None = None,
):
    source = source or packets()
    evidence = evidence_inputs(source)
    evidence.update(overrides or {})
    return build_memory_views(
        source,
        intervention=intervention,
        query_class="project_recall",
        now_iso="2026-08-04T12:00:00Z",
        **evidence,
    )


def test_no_memory_returns_empty_without_mutating_packets() -> None:
    source = packets()
    before = tuple(to_frontmatter(packet) for packet in source)

    assert build("no_memory", source=source) == ()
    assert tuple(to_frontmatter(packet) for packet in source) == before


def test_raw_and_distilled_views_are_deterministic_and_distinct() -> None:
    raw_first = build("raw")
    raw_second = build("raw")
    distilled = build("distilled")

    assert raw_first == raw_second
    assert tuple(view.view_id for view in raw_first) == tuple(
        sorted(view.view_id for view in raw_first)
    )
    assert {view.representation for view in raw_first} == {"raw"}
    assert {view.representation for view in distilled} == {"distilled"}
    assert {view.view_id for view in raw_first}.isdisjoint(
        view.view_id for view in distilled
    )
    assert "credential_field_mismatch" in raw_first[0].rendered_text
    assert distilled[0].rendered_text.startswith("Map the selected credential")


def test_independent_verdict_is_bound_to_packet_hash() -> None:
    evidence = evidence_inputs(packets())
    verdicts = dict(evidence["independent_verdicts"])
    verdicts["episode_alpha"] = verdict("episode_alpha", HASH_A)

    with pytest.raises(ValueError, match="verdict hash mismatch"):
        build("distilled", overrides={"independent_verdicts": verdicts})


def test_missing_evidence_key_fails_closed() -> None:
    with pytest.raises(ValueError, match="semantic_scores must contain exactly"):
        build("distilled", overrides={"semantic_scores": {"episode_alpha": 0.9}})


def test_poisoned_views_remain_visible_but_blocked() -> None:
    evidence = evidence_inputs(packets())
    verdicts = dict(evidence["independent_verdicts"])
    verdicts["episode_alpha"] = None
    views = build("poisoned", overrides={"independent_verdicts": verdicts})

    poisoned = next(view for view in views if "alpha" in view.view_id)
    assert poisoned.verification_state == "blocked"
    assert poisoned.verdict is None
    assert len(views) == 2


def test_shuffled_rotates_only_source_query_classes() -> None:
    baseline = build("distilled")
    shuffled = build("shuffled")

    assert {view.source_packet_hash for view in shuffled} == {
        view.source_packet_hash for view in baseline
    }
    assert {view.rendered_text for view in shuffled} == {
        view.rendered_text for view in baseline
    }
    assert {
        (view.source_packet_hash, view.query_class) for view in shuffled
    } != {(view.source_packet_hash, view.query_class) for view in baseline}


def test_stale_sets_expiry_without_deleting_source() -> None:
    views = build("stale")

    assert len(views) == 2
    assert {view.expires_at for view in views} == {"2026-08-04T12:00:00Z"}
    assert {view.lifecycle_state for view in views} == {"cooling"}


def test_contradictory_preserves_original_and_incompatible_views() -> None:
    views = build("contradictory")

    assert len(views) == 4
    assert sum(view.rendered_text.startswith("DO_NOT_USE: ") for view in views) == 2
    assert len({view.view_id for view in views}) == 4


def test_unsafe_packet_text_is_rejected_before_rendering() -> None:
    source = packets()
    unsafe = replace(source[0], policy_hint="api_key=sk-do-not-store")

    with pytest.raises(ValueError, match="rendered_text contains unsafe"):
        build("distilled", source=(unsafe, source[1]))

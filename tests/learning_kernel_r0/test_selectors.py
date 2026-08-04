from __future__ import annotations

from dataclasses import replace

from benchmarks.learning_kernel_r0.schema import MemoryView, memory_view_from_mapping
from benchmarks.learning_kernel_r0.selectors import select_views


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64

CONTEXT = ("compass/s4/provider_boundary", "project_recall", "repair")


def view(
    suffix: str,
    *,
    score: float,
    route_key: str = CONTEXT[0],
    query_class: str = CONTEXT[1],
    action_kind: str = CONTEXT[2],
    representation: str = "distilled",
    verification_state: str = "independent_verified",
    verdict: str | None = "success",
    lifecycle_state: str = "active",
) -> MemoryView:
    source_hash = {"alpha": HASH_A, "beta": HASH_B, "gamma": HASH_C}[suffix]
    return memory_view_from_mapping(
        {
            "view_id": f"lkr0_view_{suffix}_aaaaaaaaaaaa",
            "source_packet_hash": source_hash,
            "route_key": route_key,
            "query_class": query_class,
            "action_kind": action_kind,
            "representation": representation,
            "rendered_text": f"lesson {suffix}",
            "semantic_score": score,
            "verification_state": verification_state,
            "verdict": verdict,
            "lifecycle_state": lifecycle_state,
            "expires_at": None,
        }
    )


def views() -> tuple[MemoryView, ...]:
    return (
        view("alpha", score=0.8),
        view("beta", score=0.9),
        view("gamma", score=0.7),
    )


def utility_scores() -> dict[tuple[str, str, str, str], float]:
    return {
        (*CONTEXT, "lkr0_view_alpha_aaaaaaaaaaaa"): 0.9,
        (*CONTEXT, "lkr0_view_beta_aaaaaaaaaaaa"): 0.1,
        (*CONTEXT, "lkr0_view_gamma_aaaaaaaaaaaa"): 0.5,
    }


def test_flat_always_selects_nothing() -> None:
    assert select_views("flat", views(), context_key=CONTEXT) == ()


def test_semantic_orders_by_score_then_view_id() -> None:
    tied = replace(views()[0], semantic_score=0.9)
    selected = select_views(
        "semantic",
        (views()[1], tied, views()[2]),
        context_key=CONTEXT,
        limit=3,
    )

    assert [item.view_id for item in selected] == [
        "lkr0_view_alpha_aaaaaaaaaaaa",
        "lkr0_view_beta_aaaaaaaaaaaa",
        "lkr0_view_gamma_aaaaaaaaaaaa",
    ]


def test_distilled_uses_same_semantic_order_and_excludes_raw_views() -> None:
    raw = replace(views()[1], representation="raw")
    selected = select_views(
        "distilled",
        (views()[0], raw, views()[2]),
        context_key=CONTEXT,
        limit=3,
    )

    assert [item.view_id for item in selected] == [
        "lkr0_view_alpha_aaaaaaaaaaaa",
        "lkr0_view_gamma_aaaaaaaaaaaa",
    ]


def test_contextual_utility_reranks_only_semantic_candidates() -> None:
    selected = select_views(
        "contextual_utility",
        views(),
        context_key=CONTEXT,
        utility_scores=utility_scores(),
        semantic_candidate_limit=2,
        limit=2,
    )

    assert [item.view_id for item in selected] == [
        "lkr0_view_alpha_aaaaaaaaaaaa",
        "lkr0_view_beta_aaaaaaaaaaaa",
    ]


def test_contextual_utility_missing_exact_context_falls_back_to_flat() -> None:
    assert (
        select_views(
            "contextual_utility",
            views(),
            context_key=("unknown", "project_recall", "repair"),
            utility_scores=utility_scores(),
        )
        == ()
    )


def test_current_poi_delegates_to_impact_then_reward_order() -> None:
    selected = select_views(
        "current_poi",
        views(),
        context_key=CONTEXT,
        poi_scores={
            "lkr0_view_alpha_aaaaaaaaaaaa": (0.2, 1.0),
            "lkr0_view_beta_aaaaaaaaaaaa": (0.8, 0.0),
            "lkr0_view_gamma_aaaaaaaaaaaa": (0.2, 0.5),
        },
        limit=3,
    )

    assert [item.view_id for item in selected] == [
        "lkr0_view_beta_aaaaaaaaaaaa",
        "lkr0_view_alpha_aaaaaaaaaaaa",
        "lkr0_view_gamma_aaaaaaaaaaaa",
    ]


def test_governed_excludes_unverified_archived_and_context_mismatch() -> None:
    eligible = views()[0]
    blocked = replace(views()[1], verification_state="blocked", verdict=None)
    archived = replace(views()[2], lifecycle_state="archived")
    mismatch = replace(
        views()[2],
        view_id="lkr0_view_gamma_bbbbbbbbbbbb",
        query_class="protected_no_context",
    )
    scores = utility_scores()
    scores[(*CONTEXT, mismatch.view_id)] = 2.0

    selected = select_views(
        "governed",
        (eligible, blocked, archived, mismatch),
        context_key=CONTEXT,
        utility_scores=scores,
        protected_query_classes=frozenset({"protected_no_context"}),
        limit=4,
    )

    assert selected == (eligible,)


def test_governed_protected_query_requires_exact_protected_context() -> None:
    protected_context = (CONTEXT[0], "protected_no_context", CONTEXT[2])
    ordinary = views()[0]
    protected = replace(
        views()[1],
        query_class="protected_no_context",
    )
    scores = {
        (*protected_context, ordinary.view_id): 2.0,
        (*protected_context, protected.view_id): 1.0,
    }

    assert select_views(
        "governed",
        (ordinary, protected),
        context_key=protected_context,
        utility_scores=scores,
        protected_query_classes=frozenset({"protected_no_context"}),
    ) == (protected,)

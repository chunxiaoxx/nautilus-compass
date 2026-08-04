"""Comparable, side-effect-free memory selectors for Learning Kernel R0."""

from __future__ import annotations

from collections.abc import Mapping

from gep.poi_rerank import rerank_by_impact

from .schema import SELECTORS, MemoryView
from .utility import ContextKey, UtilityKey


PoiScore = tuple[float, float]
DIAGNOSTIC_SELECTORS = frozenset(
    {"semantic", "distilled", "contextual_utility", "current_poi"}
)
RUNTIME_ELIGIBLE_SELECTORS = frozenset({"flat", "governed"})


def select_views(
    selector: str,
    views: tuple[MemoryView, ...],
    *,
    context_key: ContextKey,
    utility_scores: Mapping[UtilityKey, float] | None = None,
    poi_scores: Mapping[str, PoiScore] | None = None,
    protected_query_classes: frozenset[str] = frozenset(),
    semantic_candidate_limit: int | None = None,
    limit: int = 1,
) -> tuple[MemoryView, ...]:
    """Select views under one frozen evaluation policy.

    Diagnostic selectors intentionally expose unsafe controls so the benchmark can
    measure poison and lifecycle failures. Only ``flat`` and ``governed`` may enter
    the candidate policy gate; the gate enforces that boundary independently.
    """

    _validate_inputs(selector, views, context_key, semantic_candidate_limit, limit)
    if selector == "flat" or not views:
        return ()

    semantic = _semantic_order(views)
    candidate_limit = semantic_candidate_limit or len(semantic)
    semantic = semantic[:candidate_limit]

    if selector == "semantic":
        return tuple(semantic[:limit])
    if selector == "distilled":
        distilled = [view for view in semantic if view.representation == "distilled"]
        return tuple(distilled[:limit])
    if selector == "current_poi":
        return _select_current_poi(semantic, poi_scores or {}, limit)
    if selector == "contextual_utility":
        return _select_by_utility(
            semantic,
            context_key=context_key,
            utility_scores=utility_scores or {},
            limit=limit,
        )

    governed = _governed_candidates(
        semantic,
        context_key=context_key,
        protected_query_classes=protected_query_classes,
    )
    return _select_by_utility(
        governed,
        context_key=context_key,
        utility_scores=utility_scores or {},
        limit=limit,
    )


def _semantic_order(views: tuple[MemoryView, ...]) -> list[MemoryView]:
    return sorted(views, key=lambda view: (-view.semantic_score, view.view_id))


def _select_current_poi(
    views: list[MemoryView],
    poi_scores: Mapping[str, PoiScore],
    limit: int,
) -> tuple[MemoryView, ...]:
    hits = []
    for view in sorted(views, key=lambda item: item.view_id):
        impact, reward = poi_scores.get(view.view_id, (0.0, 0.0))
        hits.append(
            {
                "view": view,
                "cumulative_impact": impact,
                "reward": reward,
            }
        )
    ranked = rerank_by_impact(hits)
    return tuple(hit["view"] for hit in ranked[:limit])


def _select_by_utility(
    views: list[MemoryView],
    *,
    context_key: ContextKey,
    utility_scores: Mapping[UtilityKey, float],
    limit: int,
) -> tuple[MemoryView, ...]:
    supported = [
        view for view in views if (*context_key, view.view_id) in utility_scores
    ]
    if not supported:
        return ()
    ranked = sorted(
        supported,
        key=lambda view: (
            -utility_scores[(*context_key, view.view_id)],
            -view.semantic_score,
            view.view_id,
        ),
    )
    return tuple(ranked[:limit])


def _governed_candidates(
    views: list[MemoryView],
    *,
    context_key: ContextKey,
    protected_query_classes: frozenset[str],
) -> list[MemoryView]:
    route_key, query_class, action_kind = context_key
    if query_class in protected_query_classes:
        required_query_class = query_class
    else:
        required_query_class = query_class
    return [
        view
        for view in views
        if view.verification_state == "independent_verified"
        and view.verdict is not None
        and view.lifecycle_state == "active"
        and view.representation == "distilled"
        and view.route_key == route_key
        and view.query_class == required_query_class
        and view.action_kind == action_kind
    ]


def _validate_inputs(
    selector: str,
    views: tuple[MemoryView, ...],
    context_key: ContextKey,
    semantic_candidate_limit: int | None,
    limit: int,
) -> None:
    if selector not in SELECTORS:
        raise ValueError("selector is unsupported")
    if not isinstance(views, tuple) or any(not isinstance(view, MemoryView) for view in views):
        raise TypeError("views must be a tuple of MemoryView values")
    if not isinstance(context_key, tuple) or len(context_key) != 3:
        raise TypeError("context_key must be a three-string tuple")
    if any(not isinstance(value, str) or not value for value in context_key):
        raise ValueError("context_key values must be non-blank strings")
    _validate_limit("limit", limit)
    if semantic_candidate_limit is not None:
        _validate_limit("semantic_candidate_limit", semantic_candidate_limit)


def _validate_limit(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a positive integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")


__all__ = [
    "DIAGNOSTIC_SELECTORS",
    "RUNTIME_ELIGIBLE_SELECTORS",
    "PoiScore",
    "select_views",
]

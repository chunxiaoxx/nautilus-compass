"""OKF validator — check an OKF bundle for self-consistency.

An OKF bundle (from :func:`okf.exporter.build_okf_bundle`) is the serialised
compass memory capsule: typed concepts + a directed link graph + a symmetric
backlink ("cited by") index. Two *hard* invariants must hold for downstream
consumers (recall / semantic-search index builders):

1. every concept carries a non-empty ``type`` (the one OKF-required field);
2. the backlink index is symmetric to the link graph (A->B implies A in
   ``backlinks[B]``), so a recall index can be rebuilt from either direction.

:func:`validate_okf_bundle` returns those *hard* errors only — an empty list
means the bundle is valid.

Dangling links (a ``[[name]]`` whose target has no concept) are **not** errors:
per compass memory convention a ``[[name]]`` that doesn't match an existing
memory yet is a legitimate *forward reference* ("marks something worth writing
later, not an error"). :func:`find_dangling_links` reports them separately as an
informational knowledge-graph-completeness signal.

Pure stdlib; tolerant of missing keys so it never raises on a partial bundle.
"""

from __future__ import annotations

__all__ = ["validate_okf_bundle", "find_dangling_links"]


def _as_list(value):
    """Coerce ``value`` to a list; non-list / missing becomes ``[]``."""
    if isinstance(value, list):
        return value
    return []


def _as_dict(value):
    """Coerce ``value`` to a dict; non-dict / missing becomes ``{}``."""
    if isinstance(value, dict):
        return value
    return {}


def _known_names(concepts):
    """Set of concept ``name`` strings (skips unnamed)."""
    names = set()
    for concept in concepts:
        concept = _as_dict(concept)
        name = concept.get("name")
        if name is not None:
            names.add(str(name))
    return names


def validate_okf_bundle(bundle):
    """Validate an OKF bundle dict, returning a list of HARD error strings.

    Empty list means valid. Hard errors:
    (1) a concept missing its required ``type`` field;
    (2) an asymmetric backlink (``link_graph[A]`` has B but ``backlinks[B]``
        lacks A).

    Dangling links are NOT hard errors (legitimate forward references) — use
    :func:`find_dangling_links` for those. Missing ``concepts`` / ``link_graph``
    / ``backlinks`` keys default to empty and never raise.
    """
    errors = []

    bundle = _as_dict(bundle)
    concepts = _as_list(bundle.get("concepts"))
    link_graph = _as_dict(bundle.get("link_graph"))
    backlinks = _as_dict(bundle.get("backlinks"))

    # Rule 1: every concept must have a non-empty `type`.
    for concept in concepts:
        concept = _as_dict(concept)
        name = concept.get("name", "<unnamed>")
        ctype = concept.get("type")
        if ctype is None or str(ctype).strip() == "":
            errors.append(f"concept '{name}' is missing required 'type' field")

    # Rule 2: backlink symmetry — link_graph[A] contains B implies
    # backlinks[B] contains A.
    for source, targets in link_graph.items():
        for target in _as_list(targets):
            target_backlinks = _as_list(backlinks.get(target))
            if str(source) not in {str(s) for s in target_backlinks}:
                errors.append(
                    f"asymmetric backlink: '{source}' -> '{target}' "
                    f"but '{source}' missing from backlinks['{target}']"
                )

    return errors


def find_dangling_links(bundle):
    """Return informational descriptions of dangling links (forward references).

    A dangling link is a ``link_graph`` target with no matching concept. Per
    compass memory convention these are legitimate forward references, NOT
    validation errors — a knowledge-graph-completeness signal. Empty list means
    every link resolves to a known concept. Never raises on a partial bundle.
    """
    bundle = _as_dict(bundle)
    concepts = _as_list(bundle.get("concepts"))
    link_graph = _as_dict(bundle.get("link_graph"))
    known = _known_names(concepts)

    dangling = []
    for source, targets in link_graph.items():
        for target in _as_list(targets):
            if str(target) not in known:
                dangling.append(
                    f"forward-ref: '{source}' -> '{target}' (no concept yet)"
                )
    return dangling

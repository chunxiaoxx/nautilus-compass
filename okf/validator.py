"""OKF validator — check an OKF bundle for self-consistency.

An OKF bundle (as produced by :func:`okf.exporter.build_okf_bundle`) is the
serialised form of the compass memory capsule: a list of typed concepts plus a
directed link graph and its symmetric backlink ("cited by") index. Downstream
consumers — e.g. recall / semantic-search index builders — rely on three
invariants:

1. every concept carries a non-empty ``type`` (the one OKF-required field);
2. every link target resolves to a known concept (no dangling links);
3. the backlink index is symmetric to the link graph (A->B implies A in
   ``backlinks[B]``), so a recall index can be rebuilt from either direction.

:func:`validate_okf_bundle` returns a list of human-readable error strings — an
empty list means the bundle is valid. Pure stdlib; tolerant of missing keys so
it never raises on a malformed/partial bundle.
"""

from __future__ import annotations

__all__ = ["validate_okf_bundle"]


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


def validate_okf_bundle(bundle):
    """Validate an OKF bundle dict, returning a list of error strings.

    An empty list means the bundle is valid. Missing ``concepts`` /
    ``link_graph`` / ``backlinks`` keys default to empty and never raise.
    """
    errors = []

    bundle = _as_dict(bundle)
    concepts = _as_list(bundle.get("concepts"))
    link_graph = _as_dict(bundle.get("link_graph"))
    backlinks = _as_dict(bundle.get("backlinks"))

    # Set of known concept names (used for dangling-link detection).
    known_names = set()
    for concept in concepts:
        concept = _as_dict(concept)
        name = concept.get("name")
        if name is not None:
            known_names.add(str(name))

    # Rule 1: every concept must have a non-empty `type`.
    for concept in concepts:
        concept = _as_dict(concept)
        name = concept.get("name", "<unnamed>")
        ctype = concept.get("type")
        if ctype is None or str(ctype).strip() == "":
            errors.append(f"concept '{name}' is missing required 'type' field")

    # Rule 2: every link target must be a known concept.
    for source, targets in link_graph.items():
        for target in _as_list(targets):
            if str(target) not in known_names:
                errors.append(
                    f"dangling link: '{source}' -> '{target}' "
                    f"(target is not a known concept)"
                )

    # Rule 3: backlink symmetry — link_graph[A] contains B implies
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

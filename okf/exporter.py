"""OKF exporter — convert a compass memory directory into a standard OKF bundle.

OKF (Open Knowledge Format v0.1): knowledge = markdown + YAML frontmatter whose
only required field is ``type``; markdown links form a directed knowledge graph
plus a "cited by" backlink graph.

This module turns compass memory ``.md`` files (YAML frontmatter with ``name``,
``description`` and a nested ``metadata.type``, body using ``[[name]]`` wikilinks)
into an OKF bundle so the memory capsule is readable by any OKF-aware tool.

Pure stdlib — no third-party dependencies (no pyyaml). The frontmatter parser is
a deliberately small line-based reader sufficient for compass memory files; it is
tolerant of malformed input (never raises on bad frontmatter).
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["parse_memory_frontmatter", "extract_wikilinks", "build_okf_bundle"]

_WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")
_FENCE = "---"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_memory_frontmatter(md_text: str):
    """Split the leading ``---`` frontmatter block and parse it.

    Returns ``(fm_dict, body)``. The nested ``metadata.type`` (or a flat
    ``metadata.type`` dotted key) is promoted to a top-level ``type`` key, which
    OKF requires. When there is no well-formed frontmatter block, returns
    ``({}, md_text)``. Never raises on malformed frontmatter.
    """
    if not isinstance(md_text, str):
        return {}, md_text

    # Frontmatter must start at the very top (allow a leading BOM / blank lines).
    stripped = md_text.lstrip("﻿")
    if not stripped.startswith(_FENCE):
        return {}, md_text

    lines = stripped.split("\n")
    # First line is the opening fence; find the closing fence.
    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == _FENCE:
            close_idx = i
            break

    if close_idx is None:
        # No closing fence -> not a valid block; treat whole text as body.
        return {}, md_text

    fm_lines = lines[1:close_idx]
    body = "\n".join(lines[close_idx + 1:])

    fm: dict = {}
    metadata: dict = {}
    in_metadata = False

    try:
        for raw in fm_lines:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue

            indent = len(raw) - len(raw.lstrip(" "))
            line = raw.strip()

            if ":" not in line:
                # Plain list item or stray line; ignore safely.
                in_metadata = False
                continue

            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            # Nested metadata block: "metadata:" header followed by indented keys.
            if key == "metadata" and value == "":
                in_metadata = True
                continue

            if in_metadata and indent > 0:
                metadata[key] = _strip_quotes(value)
                continue

            # Any non-indented (or non-metadata) key ends a metadata block.
            in_metadata = False

            # Flat dotted form: "metadata.type: project".
            if key.startswith("metadata."):
                metadata[key.split(".", 1)[1].strip()] = _strip_quotes(value)
                continue

            fm[key] = _strip_quotes(value)
    except Exception:
        # Defensive: malformed frontmatter must not crash the exporter.
        return fm, body

    # Promote metadata.type -> top-level OKF `type`.
    if "type" in metadata and "type" not in fm:
        fm["type"] = metadata["type"]
    if metadata:
        fm.setdefault("metadata", metadata)

    return fm, body


def extract_wikilinks(body: str):
    """Return the ordered, de-duplicated list of ``[[name]]`` link targets."""
    if not isinstance(body, str):
        return []
    seen = set()
    out = []
    for match in _WIKILINK_RE.findall(body):
        target = match.strip()
        if not target or target in seen:
            continue
        seen.add(target)
        out.append(target)
    return out


def build_okf_bundle(memory_root):
    """Walk ``memory_root`` and build an OKF bundle dict.

    Each ``.md`` with a ``name`` becomes an OKF concept
    ``{"name", "type", "description"}``. Non-``.md`` files and files without a
    ``name`` are skipped.

    Duplicate ``name`` across files (compass memory occasionally has demo/short
    frontmatter sharing a name) is handled losslessly: concepts are
    **de-duplicated by name** (one concept per name, first-seen order, last file
    wins on type/description) and outgoing links are **unioned** across all files
    sharing the name (so no file's links are dropped). Without this, a later
    file would overwrite an earlier file's ``link_graph`` entry while its
    backlinks survived — a silent asymmetry.

    Returns ``{"concepts": [...], "link_graph": {name: [targets]},
    "backlinks": {name: [sources]}}``. Backlinks are symmetric to links
    (A->B implies A in backlinks[B]) and are order-preserving + de-duplicated.
    """
    root = Path(memory_root)

    concepts_by_name: dict = {}   # name -> concept dict (dedup; last file wins)
    concept_order: list = []      # first-seen name order (stable output)
    link_graph: dict = {}
    backlinks: dict = {}

    if not root.is_dir():
        return {"concepts": [], "link_graph": link_graph, "backlinks": backlinks}

    # Deterministic order so output is stable across runs.
    md_paths = sorted(
        (p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".md"),
        key=lambda p: p.name,
    )

    for path in md_paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        fm, body = parse_memory_frontmatter(text)
        name = fm.get("name")
        if not name:
            continue
        name = str(name).strip()
        if not name:
            continue

        if name not in concepts_by_name:
            concept_order.append(name)
        concepts_by_name[name] = {
            "name": name,
            "type": fm.get("type", ""),
            "description": fm.get("description", ""),
        }

        # Union outgoing links across duplicate names (never overwrite/drop).
        existing = link_graph.setdefault(name, [])
        for target in extract_wikilinks(body):
            if target not in existing:
                existing.append(target)
            sources = backlinks.setdefault(target, [])
            if name not in sources:
                sources.append(name)

    concepts = [concepts_by_name[n] for n in concept_order]
    return {
        "concepts": concepts,
        "link_graph": link_graph,
        "backlinks": backlinks,
    }

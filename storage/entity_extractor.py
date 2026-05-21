"""v1.7.1+ · GBrain-paradigm auto entity extraction (LLM-free).

Parses [[<namespace>/<name>]] references in session_*.md body text.
For namespace='sessions', auto-emits depends_on entries that recall.transitive_close
can BFS-expand (no LLM needed at ingest).

Reference: GBrain README · "Every page write extracts entity references and creates
typed links with zero LLM calls" · this is the compass clean-room Python equivalent.

Reference: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md attribution checklist row "auto-fix references".
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

# [[<namespace>/<name>]] · namespace = wiki|people|companies|concepts|sessions
# name = filesystem-safe chars (letters, digits, underscore, hyphen, dot, slash)
ENTITY_PATTERN = re.compile(
    r"\[\[(wiki|people|companies|concepts|sessions)/([\w\-./]+?)\]\]"
)

VALID_NAMESPACES = ("wiki", "people", "companies", "concepts", "sessions")


def extract_entities(text: str) -> list:
    """Find all [[ns/name]] references in text. Returns list of (ns, name, start, end)."""
    if not isinstance(text, str):
        return []
    return [
        (m.group(1), m.group(2).strip(), m.start(), m.end())
        for m in ENTITY_PATTERN.finditer(text)
    ]


def extract_session_refs(text: str) -> list:
    """Filter extract_entities · return only namespace='sessions' name list (dedup)."""
    seen: list = []
    for ns, name, _, _ in extract_entities(text):
        if ns == "sessions" and name not in seen:
            seen.append(name)
    return seen


def build_session_links(session_text: str,
                        existing_depends_on: Optional[list] = None) -> list:
    """Merge auto-extracted session refs with existing depends_on field.

    Args:
        session_text: full session_*.md content (body + frontmatter)
        existing_depends_on: existing depends_on list from frontmatter (if any)

    Returns:
        merged list of session filenames · dedup · order preserved
    """
    auto_refs = extract_session_refs(session_text)
    existing = list(existing_depends_on) if existing_depends_on else []
    merged: list = []
    for ref in existing + auto_refs:
        if not isinstance(ref, str):
            continue
        ref_normalized = ref.strip()
        if not ref_normalized:
            continue
        # Normalize · ensure .md suffix for filesystem lookup
        if not ref_normalized.endswith(".md"):
            ref_normalized = ref_normalized + ".md"
        if ref_normalized not in merged:
            merged.append(ref_normalized)
    return merged


def extract_typed_links(text: str) -> dict:
    """Group all extracted entities by namespace · returns {ns: [names]}."""
    grouped: dict = {ns: [] for ns in VALID_NAMESPACES}
    for ns, name, _, _ in extract_entities(text):
        if ns in grouped and name not in grouped[ns]:
            grouped[ns].append(name)
    return {ns: names for ns, names in grouped.items() if names}


def rewrite_inline_links(text: str, target_path_resolver=None) -> str:
    """Replace [[ns/name]] inline references with linked anchors (optional).

    If target_path_resolver provided, calls resolver(ns, name) → relative path
    and rewrites to markdown link syntax [name](path). Otherwise leaves unchanged.
    """
    if target_path_resolver is None:
        return text

    def _replace(m):
        ns, name = m.group(1), m.group(2).strip()
        try:
            path = target_path_resolver(ns, name)
        except Exception:
            return m.group(0)
        if not path:
            return m.group(0)
        return f"[{name}]({path})"

    return ENTITY_PATTERN.sub(_replace, text)


def scan_session_file(path: Path) -> dict:
    """Scan a session_*.md file · return {session_refs, typed_links, raw_count}."""
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists():
        return {"session_refs": [], "typed_links": {}, "raw_count": 0}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"session_refs": [], "typed_links": {}, "raw_count": 0}
    refs = extract_session_refs(text)
    typed = extract_typed_links(text)
    raw = len(extract_entities(text))
    return {"session_refs": refs, "typed_links": typed, "raw_count": raw}

"""v1.7.1 · L1 recall overlay · collapse L0 members to L1 summary if available.

Sits between recall.py vector search and downstream consumer:
  - Input: ranked list of L0 entries (from BGE-m3 cosine)
  - Output: ranked list with L1 summaries substituted where _l1_index.json maps
  - Reuses recall.rrf_fusion (Phase 2.C · commit 2ed77b4) for L0+L1 fusion

Goal: reduce context bloat (1 L1 summary vs 5 raw L0 sessions) while preserving
narrative coherence (group by thread_id or topic cluster).

NO LLM. Pure rank-based arithmetic + JSON lookup.
Reference: paper/SPEC_LAYER2_L1_REWRITE.md section 3.3.
"""
from __future__ import annotations

from pathlib import Path

from .l1_index import load_index


def collapse_to_l1(top_entries: list, l1_dir: Path,
                   max_collapse_per_l1: int = 1) -> list:
    """Substitute member L0 entries with their L1 summary entry.

    Args:
        top_entries: list of (score, entry_dict) tuples with 'path' field
        l1_dir: directory containing _l1_index.json + L1 *.md files
        max_collapse_per_l1: cap how many L1 entries surface (deduplication)

    Returns:
        New list with L0 members replaced by L1 summary entry (highest L0 score
        in the group keeps the position · L1 inserted there)
    """
    if not isinstance(l1_dir, Path):
        l1_dir = Path(l1_dir)
    idx = load_index(l1_dir)
    if not idx:
        return list(top_entries)

    seen_l1: dict = {}  # l1_relative_path → count
    output: list = []
    for score, entry in top_entries:
        path_field = entry.get("path", "") if isinstance(entry, dict) else ""
        if not path_field:
            output.append((score, entry))
            continue
        # Look up by filename
        filename = Path(path_field).name
        l1_rel = idx.get(filename, "")
        if not l1_rel:
            output.append((score, entry))
            continue
        # Substitute with L1 entry (only first occurrence per L1 group)
        if seen_l1.get(l1_rel, 0) >= max_collapse_per_l1:
            continue  # skip · already surfaced
        seen_l1[l1_rel] = seen_l1.get(l1_rel, 0) + 1
        l1_path = (l1_dir / l1_rel).resolve()
        l1_entry = {
            "path": str(l1_path),
            "filename": Path(l1_rel).name,
            "tier": "episodic",
            "l1_source": filename,
            "collapsed_from": filename,
        }
        output.append((score, l1_entry))
    return output


def fuse_l0_l1(l0_ranked: list, l1_ranked: list, k: int = 60,
               top_k: int = 10) -> list:
    """Reuse recall.rrf_fusion to fuse L0 + L1 ranked lists.

    L1 entries already have separate BGE-m3 embedding (built by reembed_l1).
    L0 and L1 both ranked by cosine · RRF fuses by reciprocal rank.
    """
    try:
        from recall import rrf_fusion  # type: ignore
    except ImportError:
        # Graceful fallback · just concatenate dedup
        seen = set()
        out: list = []
        for lst in (l0_ranked, l1_ranked):
            for score, entry in lst:
                path = entry.get("path") if isinstance(entry, dict) else None
                if path and path not in seen:
                    seen.add(path)
                    out.append((score, entry))
        return out[:top_k]

    return rrf_fusion(l0_ranked, l1_ranked, k=k, top_k=top_k,
                      session_diversify=True, max_per_session=3)

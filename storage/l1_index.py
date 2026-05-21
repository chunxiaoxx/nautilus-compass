"""v1.7.1 · L1 index · _l1_index.json maintenance + BGE re-embed hook.

Maps each L0 session_*.md member to its containing L1 file:
  {"session_X.md": "_l1/thread_t-A.md", ...}

Powers the recall overlay (l1_recall_overlay.py) which checks if a recalled
session has an L1 summary to surface instead of raw L0.

NO LLM. BGE re-embed is OPTIONAL (graceful degradation if daemon unavailable).
Reference: paper/SPEC_LAYER2_L1_REWRITE.md section 3.2 step 5-6.
"""
from __future__ import annotations

import json
from pathlib import Path

INDEX_FILENAME = "_l1_index.json"


def load_index(l1_dir: Path) -> dict:
    """Load index JSON · returns empty dict if missing/corrupt."""
    if not isinstance(l1_dir, Path):
        l1_dir = Path(l1_dir)
    idx_path = l1_dir / INDEX_FILENAME
    if not idx_path.exists():
        return {}
    try:
        return json.loads(idx_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_index(l1_dir: Path, index: dict) -> Path:
    """Atomic write index JSON · pretty-printed for diff/audit."""
    if not isinstance(l1_dir, Path):
        l1_dir = Path(l1_dir)
    l1_dir.mkdir(parents=True, exist_ok=True)
    idx_path = l1_dir / INDEX_FILENAME
    tmp_path = idx_path.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(idx_path)
    return idx_path


def update_index(l1_dir: Path, written: dict) -> dict:
    """Merge new (group_id → L1 path) writes into existing index.

    Expands each L1's member list into reverse lookup:
      {session_filename: l1_relative_path}

    Returns updated full index dict.
    """
    if not isinstance(l1_dir, Path):
        l1_dir = Path(l1_dir)
    idx = load_index(l1_dir)
    for group_id, l1_path in written.items():
        l1_path = Path(l1_path) if not isinstance(l1_path, Path) else l1_path
        try:
            content = l1_path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = l1_path.relative_to(l1_dir) if l1_dir in l1_path.parents else l1_path.name
        rel_str = str(rel)
        # Parse l1_members from frontmatter
        if "l1_members:" in content:
            section = content.split("l1_members:", 1)[1].split("---", 1)[0]
            for line in section.splitlines():
                line = line.strip()
                if line.startswith("- "):
                    member = line[2:].strip()
                    if member:
                        idx[member] = rel_str
    save_index(l1_dir, idx)
    return idx


def reembed_l1(l1_dir: Path, embedder=None) -> int:
    """Optionally re-embed L1 .md files with BGE-m3.

    Returns number of files embedded · 0 if BGE unavailable.
    Embeddings are NOT persisted here (recall daemon handles its own cache).
    This function is a stub for future recall integration.
    """
    if embedder is None:
        try:
            import daemon as zmd  # type: ignore
            embedder = zmd.get_embedder()
        except ImportError:
            return 0
    if not isinstance(l1_dir, Path):
        l1_dir = Path(l1_dir)
    if not l1_dir.exists():
        return 0
    count = 0
    for f in l1_dir.glob("*.md"):
        if f.name == INDEX_FILENAME:
            continue
        try:
            text = f.read_text(encoding="utf-8")
            # Embed first 600 chars (consistent with l1_grouper)
            embedder.encode(text[:600])
            count += 1
        except (OSError, UnicodeDecodeError):
            continue
    return count


def lookup_l1_for_session(l1_dir: Path, session_filename: str) -> str:
    """Return L1 relative path containing this session · or empty string if none."""
    idx = load_index(l1_dir)
    return idx.get(session_filename, "")

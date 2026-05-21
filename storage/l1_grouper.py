"""v1.7.1 · L1 grouper · OV paradigm clean-room rewrite (NO code fork).

Groups session_*.md files for L1 overview tier generation:
  - thread_id grouping (sessions sharing frontmatter thread_id · size >= 3)
  - topic cluster (greedy cosine clustering for thread-less sessions · threshold 0.55)

Reuses existing infrastructure (anchor #5 anti-reinvention):
  - daemon.get_embedder() · BGE-m3 SentenceTransformer
  - daemon.cosine() · cosine similarity

Reference: paper/SPEC_LAYER2_L1_REWRITE.md section 3.2.
NO LLM calls. Deterministic logic + BGE-m3 embedding only.
"""
from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

THREAD_MIN_SIZE = 3
TOPIC_MIN_SIZE = 4
TOPIC_COSINE_THRESHOLD = float(os.environ.get("COMPASS_L1_TOPIC_THRESHOLD", "0.55"))


def parse_session_frontmatter(path: Path) -> dict:
    """Extract minimal frontmatter fields from session_*.md file.

    Returns dict of stripped key-value pairs · empty dict on any failure.
    """
    if not isinstance(path, Path):
        path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fields: dict = {}
    for line in text[4:end].splitlines():
        line = line.strip()
        if ":" not in line or line.startswith("#"):
            continue
        k, _, v = line.partition(":")
        fields[k.strip()] = v.strip()
    return fields


def group_by_thread(sessions: list, min_size: int = THREAD_MIN_SIZE) -> dict:
    """Group sessions by frontmatter thread_id. Returns {thread_id: [paths]}.

    Only thread_ids with len >= min_size are returned. Sessions without
    thread_id are silently excluded (caller passes them to cluster_by_topic).
    """
    by_thread: dict = defaultdict(list)
    for s in sessions:
        path = Path(s) if not isinstance(s, Path) else s
        front = parse_session_frontmatter(path)
        thread_id = front.get("thread_id", "").strip()
        if thread_id:
            by_thread[thread_id].append(str(path))
    return {tid: paths for tid, paths in by_thread.items() if len(paths) >= min_size}


def cluster_by_topic(thread_less_sessions: list, embedder=None,
                     threshold: float = TOPIC_COSINE_THRESHOLD,
                     min_cluster_size: int = TOPIC_MIN_SIZE) -> dict:
    """Greedy cosine clustering on session descriptions.

    Returns {cluster_id: [paths]} for clusters with len >= min_cluster_size.
    cluster_id format: 'topic_NNN' (zero-padded 3 digits).

    If embedder is None, attempts to import daemon.get_embedder() lazily.
    Returns empty dict if daemon not importable (graceful degradation).
    """
    if not thread_less_sessions:
        return {}
    try:
        import daemon as zmd  # type: ignore
        cosine = zmd.cosine
        if embedder is None:
            embedder = zmd.get_embedder()
    except ImportError:
        return {}

    items: list = []
    for s in thread_less_sessions:
        path = Path(s) if not isinstance(s, Path) else s
        front = parse_session_frontmatter(path)
        desc = front.get("description", "").strip()
        if not desc:
            continue
        emb = embedder.encode(desc[:600])
        items.append((str(path), emb))

    clusters: dict = {}
    used: set = set()
    cluster_idx = 0
    for i, (path_i, emb_i) in enumerate(items):
        if path_i in used:
            continue
        members = [path_i]
        used.add(path_i)
        for j in range(i + 1, len(items)):
            path_j, emb_j = items[j]
            if path_j in used:
                continue
            if cosine(emb_i, emb_j) >= threshold:
                members.append(path_j)
                used.add(path_j)
        if len(members) >= min_cluster_size:
            clusters[f"topic_{cluster_idx:03d}"] = members
            cluster_idx += 1
    return clusters


def group_sessions(sessions: list, embedder=None) -> dict:
    """Combined entrypoint · thread_id groups + topic clusters.

    Returns {group_id: [paths]} where group_id is either a thread_id (string)
    or 'topic_NNN' for cosine-clustered groups.

    See paper/SPEC_LAYER2_L1_REWRITE.md section 3.2 steps 2-3.
    """
    thread_groups = group_by_thread(sessions)
    grouped_paths: set = set()
    for paths in thread_groups.values():
        grouped_paths.update(paths)
    thread_less = [s for s in sessions if str(s) not in grouped_paths]
    topic_clusters = cluster_by_topic(thread_less, embedder=embedder)
    return {**thread_groups, **topic_clusters}

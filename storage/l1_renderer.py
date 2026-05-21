"""v1.7.1 · L1 renderer · LLM-free markdown overview generation.

Takes grouped sessions from l1_grouper and renders L1 .md files with:
  - frontmatter (tier=episodic · members list · created_at)
  - first-sentence excerpts from each member session description
  - aggregated numeric_claims if present in member frontmatter

NO LLM calls. Pure string concatenation + frontmatter parsing.
Reference: paper/SPEC_LAYER2_L1_REWRITE.md section 3.2 step 4.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .l1_grouper import parse_session_frontmatter


def _first_sentence(text: str, max_chars: int = 160) -> str:
    """Extract first sentence (or up to max_chars) from text."""
    if not text:
        return ""
    text = text.strip()
    for delim in ["。", ". ", "·", "\n"]:
        idx = text.find(delim)
        if 0 < idx <= max_chars:
            return text[:idx].strip()
    return text[:max_chars].strip()


def render_l1_overview(group_id: str, member_paths: list,
                       group_type: str = "thread") -> str:
    """Render one L1 overview markdown file content.

    Args:
        group_id: thread_id or 'topic_NNN'
        member_paths: list of session_*.md path strings
        group_type: 'thread' or 'topic' (informational · sets tier metadata hint)

    Returns:
        Full markdown content with frontmatter and body.
    """
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    member_data: list = []
    descriptions: list = []
    numeric_claims_aggregated: list = []

    for p in member_paths:
        path = Path(p)
        front = parse_session_frontmatter(path)
        name = front.get("name", path.stem)
        desc = front.get("description", "")
        member_data.append((path.name, name, desc))
        if desc:
            descriptions.append(_first_sentence(desc))
        nc = front.get("numeric_claims", "").strip()
        if nc and nc not in ("[]", "{}"):
            numeric_claims_aggregated.append(f"{path.name}: {nc}")

    lines = [
        "---",
        f"name: l1-{group_id}",
        f"description: L1 overview for group '{group_id}' · {len(member_paths)} members",
        "type: discovery",
        "concept: how-it-works",
        "drift: green",
        "drift_signals: []",
        "depends_on: []",
        "declaration_type: none",
        "supersedes: []",
        "tier: episodic",
        "decay_rate: 0.3",
        f"forget_at: null",
        "promote_after: \"20_access\"",
        "reinforce_count: 0",
        "agent_type: compass-l1-renderer",
        f"l1_group_id: {group_id}",
        f"l1_group_type: {group_type}",
        f"l1_member_count: {len(member_paths)}",
        f"l1_generated_at: {ts}",
        "l1_members:",
    ]
    for filename, name, _ in member_data:
        lines.append(f"  - {filename}")
    lines.append("---")
    lines.append("")
    lines.append(f"# L1 Overview · {group_id}")
    lines.append("")
    lines.append(f"_{len(member_paths)} member sessions · type={group_type}_")
    lines.append("")
    lines.append("## Member excerpts")
    lines.append("")
    for filename, name, desc in member_data:
        excerpt = _first_sentence(desc) if desc else "(no description)"
        lines.append(f"- **{name}** (`{filename}`): {excerpt}")
    if numeric_claims_aggregated:
        lines.append("")
        lines.append("## Aggregated numeric claims")
        lines.append("")
        for nc in numeric_claims_aggregated:
            lines.append(f"- {nc}")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_l1_file(output_dir: Path, group_id: str, member_paths: list,
                  group_type: str = "thread") -> Path:
    """Render and write one L1 file to output_dir/<group_id>.md.

    output_dir is created if not exists. Filename safe-escaped (':' → '_').
    Returns the written Path.
    """
    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    content = render_l1_overview(group_id, member_paths, group_type=group_type)
    safe = group_id.replace(":", "_").replace("/", "_")
    out_path = output_dir / f"{safe}.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def render_all(groups: dict, output_dir: Path) -> dict:
    """Render all groups to L1 files. Returns {group_id: output_path}.

    Topic clusters (prefix 'topic_') tagged as group_type='topic'; others 'thread'.
    """
    written: dict = {}
    for group_id, paths in groups.items():
        gtype = "topic" if group_id.startswith("topic_") else "thread"
        written[group_id] = write_l1_file(output_dir, group_id, paths, group_type=gtype)
    return written

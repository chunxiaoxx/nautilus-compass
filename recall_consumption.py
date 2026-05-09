"""v1.0+ · v2 · detect "recall fired but not consumed" drift.

Failure mode this catches: agent sees a recall hit's title in the
UserPromptSubmit injection, mentally checks "I know about this", then
acts without reading the body. Same mistake gets repeated even though
recall surfaced the right file.

Detection signal: the path appears in a recall block in a recent user turn,
but no subsequent assistant turn issued a Read tool call against it.

Usage from drift_check or mid_session_hook:

    from recall_consumption import audit_consumption
    report = audit_consumption(window_user_turns=3)
    if report["unconsumed_paths"]:
        # surface to agent · "you saw recall X but never opened it"
        ...

Stdlib only · no compass deps · safe to import anywhere.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"

# Paths in recall blocks look like: session_20260509-0825_xxx.md
# We grab anything that looks like a memory file mentioned in a recall stanza.
_RECALL_PATH_RE = re.compile(
    r"\b(session_\d{8}[-_][0-9A-Za-z]+(?:_[^\s\.]+)?\.md|"
    r"[A-Za-z0-9_]+\.md)\b"
)
_RECALL_BLOCK_HINTS = (
    "🎯 召回 top",          # vector mode header
    "当前心智 (≤24h",        # metadata mode fresh group header
    "<nautilus-compass-recall",
)


def _find_session_jsonl() -> Path | None:
    """Locate the active session jsonl file.

    Strategy:
      1. CLAUDE_SESSION_ID env + glob through PROJECTS_DIR/*/{sid}.jsonl
      2. Fallback: most-recently-modified jsonl in any project dir matching
         this cwd's hash (best-effort)
    """
    sid = os.environ.get("CLAUDE_SESSION_ID")
    if sid and PROJECTS_DIR.is_dir():
        for d in PROJECTS_DIR.iterdir():
            cand = d / f"{sid}.jsonl"
            if cand.exists():
                return cand
    # fallback: pick the freshest jsonl (likely the live session)
    if not PROJECTS_DIR.is_dir():
        return None
    candidates: list[Path] = []
    for d in PROJECTS_DIR.iterdir():
        if not d.is_dir():
            continue
        candidates.extend(d.glob("*.jsonl"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _stream_recent_messages(jsonl_path: Path, max_lines: int = 4000) -> list[dict]:
    """Read last ~max_lines lines of jsonl · parse each as a message dict.

    We tail rather than load the full file because sessions can be 100+ MB.
    """
    if not jsonl_path.exists():
        return []
    size = jsonl_path.stat().st_size
    # Heuristic: avg jsonl line is ~5KB · take last 5KB * max_lines from EOF
    read_bytes = min(size, max_lines * 5000)
    with jsonl_path.open("rb") as f:
        f.seek(max(0, size - read_bytes))
        chunk = f.read()
    lines = chunk.splitlines()
    msgs = []
    for line in lines[-max_lines:]:
        try:
            msgs.append(json.loads(line.decode("utf-8", errors="replace")))
        except Exception:
            continue
    return msgs


def _extract_text_from_message(msg: dict) -> str:
    """Pull all text content from a message · also unwraps:
       · message.content[].text  (normal user/assistant)
       · message.content[].tool_result.content[].text  (tool results)
       · attachment.content       (UserPromptSubmit hook payloads · this is
                                   where compass recall blocks land)
    """
    out: list[str] = []
    # 1. attachment payloads (hook injections live here)
    attach = msg.get("attachment")
    if isinstance(attach, dict):
        ac = attach.get("content")
        if isinstance(ac, str):
            out.append(ac)
        elif isinstance(ac, list):
            for ib in ac:
                if isinstance(ib, dict) and ib.get("type") == "text":
                    out.append(ib.get("text") or "")
    # 2. message.content
    inner = msg.get("message")
    if isinstance(inner, dict):
        content = inner.get("content")
    else:
        content = msg.get("content")
    if isinstance(content, str):
        out.append(content)
    elif isinstance(content, list):
        for blk in content:
            if not isinstance(blk, dict):
                continue
            if blk.get("type") == "text":
                out.append(blk.get("text") or "")
            elif blk.get("type") == "tool_result":
                inner_c = blk.get("content")
                if isinstance(inner_c, str):
                    out.append(inner_c)
                elif isinstance(inner_c, list):
                    for ib in inner_c:
                        if isinstance(ib, dict) and ib.get("type") == "text":
                            out.append(ib.get("text") or "")
    return "\n".join(out)


def _extract_read_paths(msg: dict) -> list[str]:
    """Pull file_path args from any Read tool_use block in the message."""
    paths: list[str] = []
    inner = msg.get("message")
    content = (inner.get("content") if isinstance(inner, dict)
               else msg.get("content"))
    if not isinstance(content, list):
        return paths
    for blk in content:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") == "tool_use" and blk.get("name") == "Read":
            inp = blk.get("input") or {}
            fp = inp.get("file_path") or ""
            if fp:
                paths.append(Path(fp).name)   # match by basename · normalise
    return paths


def _collect_recall_paths(text: str) -> list[str]:
    """Find recall-block hint, then pull memory-file paths from same block.

    A recall block is a contiguous run of lines starting at a hint marker
    until a blank line or end. We accept paths anywhere in those lines.
    """
    if not any(hint in text for hint in _RECALL_BLOCK_HINTS):
        return []
    out: list[str] = []
    in_block = False
    blank_streak = 0
    for line in text.splitlines():
        if any(h in line for h in _RECALL_BLOCK_HINTS):
            in_block = True
            blank_streak = 0
            continue
        if not in_block:
            continue
        if not line.strip():
            blank_streak += 1
            if blank_streak >= 2:
                in_block = False
            continue
        blank_streak = 0
        for m in _RECALL_PATH_RE.finditer(line):
            p = m.group(1)
            if p.lower() in ("memory.md", "index.md"):
                continue
            out.append(p)
    # de-dupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for p in out:
        if p in seen:
            continue
        seen.add(p)
        uniq.append(p)
    return uniq


def audit_consumption(window_user_turns: int = 3,
                      jsonl_path: Path | None = None) -> dict:
    """Walk recent turns · check whether recall hits got Read'd.

    Returns:
        {
          "session": <jsonl filename or None>,
          "scanned_user_turns": N,
          "recall_paths_seen": [...],
          "recall_paths_consumed": [...],
          "unconsumed_paths": [...],
          "ratio": consumed / max(seen, 1),
        }
    """
    if jsonl_path is None:
        jsonl_path = _find_session_jsonl()
    empty = {
        "session": None, "scanned_user_turns": 0,
        "recall_paths_seen": [], "recall_paths_consumed": [],
        "unconsumed_paths": [], "ratio": 1.0,
    }
    if not jsonl_path:
        return empty
    msgs = _stream_recent_messages(jsonl_path)
    if not msgs:
        return {**empty, "session": jsonl_path.name}

    # 1. Find anchor: walk back to the N-th most-recent record that carries
    #    a recall block. Better than "N user turns" because many user turns in
    #    long sessions are short replies / tool iterations that don't trigger
    #    a fresh recall · we'd miss the actual surface events.
    recall_idxs: list[int] = []
    for i in range(len(msgs) - 1, -1, -1):
        text = _extract_text_from_message(msgs[i])
        if text and any(h in text for h in _RECALL_BLOCK_HINTS):
            recall_idxs.append(i)
            if len(recall_idxs) >= window_user_turns:
                break
    if not recall_idxs:
        return {**empty, "session": jsonl_path.name}
    anchor_idx = min(recall_idxs)
    scanned_n = len(recall_idxs)

    # 2. From anchor onwards · pull recall paths from any record (user or
    #    hook-bearing) and Read paths from any assistant tool_use.
    seen_to_idx: dict[str, int] = {}   # path → earliest record idx that surfaced it
    consumed: set[str] = set()
    for j in range(anchor_idx, len(msgs)):
        text = _extract_text_from_message(msgs[j])
        if text:
            for p in _collect_recall_paths(text):
                seen_to_idx.setdefault(p, j)
        # consumption check · any Read after the surface event
        if msgs[j].get("type") == "assistant":
            read_paths = _extract_read_paths(msgs[j])
            for p in read_paths:
                if p in seen_to_idx and seen_to_idx[p] < j:
                    consumed.add(p)

    seen_paths = set(seen_to_idx.keys())

    seen_list = sorted(seen_paths)
    consumed_list = sorted(consumed)
    unconsumed = sorted(seen_paths - consumed)
    return {
        "session": jsonl_path.name,
        "scanned_user_turns": scanned_n,
        "recall_paths_seen": seen_list,
        "recall_paths_consumed": consumed_list,
        "unconsumed_paths": unconsumed,
        "ratio": len(consumed_list) / max(len(seen_list), 1),
    }


def render_consumption_warning(report: dict, max_paths: int = 5) -> str | None:
    """Render the report as a one-block warning · or return None if green.

    Returns text suitable to print/append in drift_check or mid_session output.
    """
    unc = report.get("unconsumed_paths") or []
    if not unc:
        return None
    seen_n = len(report.get("recall_paths_seen") or [])
    head = (
        f"⚠️ recall consumption drift · {len(unc)}/{seen_n} recall hits "
        f"surfaced in last {report['scanned_user_turns']} turns went unread"
    )
    lines = [head]
    for p in unc[:max_paths]:
        lines.append(f"   · {p}  ← Read this before acting · 标题不算消费")
    if len(unc) > max_paths:
        lines.append(f"   · ... +{len(unc)-max_paths} more")
    lines.append("   ↑ recall != consumption · 看正文才算消费 · 不然命中等于零")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    rep = audit_consumption(window_user_turns=int(sys.argv[1]) if len(sys.argv) > 1 else 3)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    warn = render_consumption_warning(rep)
    if warn:
        print()
        print(warn)

"""compass · weekly memory compaction cron · 老 session_*.md → Haiku 摘要 sidecar.

Cron (cloud · weekly Sun 04:00):
  0 4 * * 0 /home/ubuntu/nautilus-compass/ops/memory_compact_cron.sh \
            >> /home/ubuntu/.cache/compass/memory-compact.log 2>&1

What it does (MVP · 不动 BGE index · 不动原 session):
  · Scan ~/.claude/projects/*/memory/session_*.md
  · Skip if:
      - file age < 7 days (still hot · don't compact)
      - sidecar `<session>.compact.md` already exists (already processed)
      - file too short (<500 chars · already compact enough)
  · For each eligible session:
      1. Read full text
      2. Call Haiku to summarize to ~200 字 (preserve frontmatter keys: name, type, concept, drift)
      3. Write sidecar `<session>.compact.md` next to original
  · Idempotent · re-runs skip processed files via state file
  · State: ~/.cache/compass/memory-compact-state.json

Why sidecar (not in-place):
  · Original stays for full BGE recall fidelity
  · Sidecar is opt-in: future compass_recall API can read .compact.md when mode=compact
  · Reversible · delete sidecar = back to original behavior

Cost estimate:
  · Haiku $1/M input tokens · avg session 2000 tokens · 500 sessions/week = 1M tokens = $1/week

Reuses pattern from `platform_results_ingest_cron.py`.
"""
from __future__ import annotations
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request


HAIKU_MODEL = "claude-haiku-4-5-20251001"
_BASE = os.environ.get("CLAUDE_BASE_URL", "").rstrip("/")
PROXY_URL = os.environ.get(
    "COMPASS_LLM_PROXY",
    f"{_BASE}/v1/messages" if _BASE else "https://api.minimaxi.com/anthropic/v1/messages"
)
TIMEOUT = 60
MIN_AGE_DAYS = int(os.environ.get("COMPASS_COMPACT_MIN_AGE_DAYS", "7"))
MIN_LEN_CHARS = int(os.environ.get("COMPASS_COMPACT_MIN_LEN", "2000"))
MAX_PER_RUN = int(os.environ.get("COMPASS_COMPACT_MAX_PER_RUN", "0"))  # 0 = unlimited
SUMMARY_TARGET_TOKENS = 250  # ~200 字中文

PROJECTS_BASE = Path.home() / ".claude" / "projects"
STATE_FILE = Path(os.environ.get(
    "COMPASS_COMPACT_STATE",
    str(Path.home() / ".cache" / "compass" / "memory-compact-state.json")
))

SYSTEM_PROMPT = """你是 compass memory 压缩器.

输入: 一段 session_*.md 内容(对话/决策/事件记录)
输出: ≤200 字摘要 · 跟原文同语言(中文原文→中文摘要 · 英文原文→英文摘要) · 必须保留:
- 真核心事实 / 决策 / 教训
- 数字 / 文件路径 / commit hash 等具体引用
- frontmatter 的 name / type / concept / drift 字段值

去掉:
- 多轮对话的 back-and-forth(只留最终结论)
- 重复信息
- 代码块完整内容(改为"代码:做什么的 ~N 行")
- 表格(改为关键点 bullet)

严格输出规则:
- 直接输出摘要 · 第一个字就是摘要本身
- 不要写 "The user wants me to..." / "Let me identify..." / "Here is the summary..." 这类 preamble
- 不要 markdown header / 不要 frontmatter / 不要解释格式
- 不要在末尾追加 "Hope this helps" 等 postamble"""


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"compacted": [], "skipped": [], "errors": [], "last_run_ts": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"compacted": [], "skipped": [], "errors": [], "last_run_ts": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["compacted"] = state.get("compacted", [])[-2000:]
    state["skipped"] = state.get("skipped", [])[-500:]
    state["errors"] = state.get("errors", [])[-200:]
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _get_api_key() -> str | None:
    return (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("CLAUDE_API_KEY")
        or None
    )


def _call_haiku(text: str) -> str | None:
    api_key = _get_api_key()
    if not api_key:
        sys.stderr.write("no ANTHROPIC_API_KEY · skip\n")
        return None
    payload = {
        "model": HAIKU_MODEL,
        "max_tokens": SUMMARY_TARGET_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": text[:8000]}],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        PROXY_URL, data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        for block in result.get("content", []):
            if block.get("type") == "text":
                return block.get("text", "").strip()
        return None
    except Exception as e:
        sys.stderr.write(f"haiku call fail: {e!r}\n")
        return None


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fm = {}
    for line in text[4:end].split("\n"):
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip().lower()] = v.strip().strip('"')
    return fm


def _build_compact_md(original_path: Path, fm: dict, summary: str) -> str:
    now = datetime.now(timezone.utc).astimezone()
    return f"""---
name: {fm.get('name', original_path.stem)} (compacted)
description: {summary[:180].replace(chr(10), ' ')}
type: memory-compact
source_session: {original_path.name}
compacted_at: {now.isoformat()}
original_type: {fm.get('type', 'unknown')}
original_concept: {fm.get('concept', 'unknown')}
original_drift: {fm.get('drift', 'unknown')}
---

# Compacted summary of {original_path.name}

{summary}

---

**Original**: `{original_path}` · {original_path.stat().st_size} bytes · compacted via Haiku 4.5
"""


def main() -> int:
    state = _load_state()
    compacted_set = set(state.get("compacted", []))
    now_ts = time.time()
    age_threshold = now_ts - (MIN_AGE_DAYS * 86400)

    new_compacted = 0
    skipped_recent = 0
    skipped_short = 0
    skipped_already = 0
    errors = 0
    total_scanned = 0

    if not PROJECTS_BASE.exists():
        sys.stderr.write(f"projects base missing · {PROJECTS_BASE}\n")
        return 0

    for project_dir in PROJECTS_BASE.iterdir():
        memory_dir = project_dir / "memory"
        if not memory_dir.is_dir():
            continue
        for session_path in memory_dir.glob("session_*.md"):
            if MAX_PER_RUN and new_compacted >= MAX_PER_RUN:
                print(f"reached MAX_PER_RUN={MAX_PER_RUN} · stopping")
                break
            total_scanned += 1
            key = f"{project_dir.name}/{session_path.name}"

            if key in compacted_set:
                skipped_already += 1
                continue

            sidecar = session_path.with_suffix(".compact.md")
            if sidecar.exists():
                compacted_set.add(key)
                skipped_already += 1
                continue

            try:
                mtime = session_path.stat().st_mtime
            except OSError:
                continue
            if mtime > age_threshold:
                skipped_recent += 1
                continue

            try:
                text = session_path.read_text(encoding="utf-8")
            except Exception as e:
                sys.stderr.write(f"read fail {key}: {e!r}\n")
                errors += 1
                continue
            if len(text) < MIN_LEN_CHARS:
                skipped_short += 1
                compacted_set.add(key)  # don't retry short files
                continue

            fm = _parse_frontmatter(text)
            summary = _call_haiku(text)
            if not summary:
                errors += 1
                continue

            content = _build_compact_md(session_path, fm, summary)
            try:
                sidecar.write_text(content, encoding="utf-8")
                compacted_set.add(key)
                new_compacted += 1
                print(f"compacted · {key} → {sidecar.name} ({len(summary)} chars summary)")
            except Exception as e:
                sys.stderr.write(f"write fail {sidecar}: {e!r}\n")
                errors += 1

    state["compacted"] = sorted(compacted_set)
    state["last_run_ts"] = int(now_ts)
    _save_state(state)

    print(f"{datetime.now().isoformat(timespec='seconds')} · scanned={total_scanned} "
          f"compacted={new_compacted} skipped_recent={skipped_recent} "
          f"skipped_short={skipped_short} skipped_already={skipped_already} errors={errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

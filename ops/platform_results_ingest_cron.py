"""compass · poll _platform_results/ · ingest into compass memory dir as session_*.md.

Cron (cloud):
  */5 * * * * /home/ubuntu/nautilus-compass/ops/platform_results_ingest_cron.sh \
              >> /home/ubuntu/.cache/compass/platform-results-ingest.log 2>&1

What it does (BP3 closure):
  · Scan ~/.claude/projects/_platform_results/*_result.json (written by
    platform-results-emit.timer on cloud)
  · For each new result file (not in state seen list):
      1. Parse JSON · validate required fields
      2. Build session_*.md with frontmatter (compass-recallable format)
      3. Write to user's project memory dir under task_id
      4. Mark as seen in state file
  · Idempotent · re-runs skip already-ingested files
  · No MCP call · direct filesystem · cron-safe

Output filename pattern:
  ~/.claude/projects/<project>/memory/session_YYYYMMDD-HHMM_platform_tk_<id>.md

Why direct file write (not MCP `ingest_platform_task_result` tool):
  · cron context · no LLM session · no Claude Code wrapper
  · matches what compass MCP tool would do internally (write session_*.md)
  · BGE daemon scans memory dirs anyway · same recall path
"""
from __future__ import annotations
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


RESULTS_DIR = Path(os.environ.get(
    "COMPASS_PLATFORM_RESULTS_DIR",
    str(Path.home() / ".claude" / "projects" / "_platform_results")
))
# Default project dir to write session_*.md (where platform tasks land)
DEFAULT_PROJECT = os.environ.get(
    "COMPASS_PLATFORM_INGEST_PROJECT",
    "C--Users-chunx-Projects-nautilus-core",
)
PROJECTS_BASE = Path.home() / ".claude" / "projects"

STATE_FILE = Path(os.environ.get(
    "COMPASS_PLATFORM_INGEST_STATE",
    str(Path.home() / ".cache" / "compass" / "platform-results-ingest-state.json"),
))

REQUIRED_FIELDS = ("task_id", "result_summary", "channels_published",
                   "drift", "agent_id")


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"seen": [], "ingested_count": 0, "last_run_ts": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"seen": [], "ingested_count": 0, "last_run_ts": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # rotate seen list · keep last 500
    state["seen"] = state.get("seen", [])[-500:]
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _slug(s: str, n: int = 30) -> str:
    """Make a file-safe slug · ASCII only."""
    out = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(s)[:n])
    return out.strip("_") or "unnamed"


def _build_session_md(result: dict, source_filename: str) -> tuple[str, str]:
    """Return (session_filename, session_content_md)."""
    task_id = result.get("task_id", "tk_unknown")
    summary = result.get("result_summary", "")[:1000]
    channels = result.get("channels_published", []) or []
    drift = result.get("drift", "green")
    agent_id = result.get("agent_id", "platform-unknown")
    tenant_id = result.get("tenant_id", "nautilus-internal")

    now = datetime.now(timezone.utc).astimezone()
    ts = now.strftime("%Y%m%d-%H%M")
    slug_id = _slug(task_id)
    filename = f"session_{ts}_platform_{slug_id}.md"

    # frontmatter compatible with compass recall + cross_dialog_notifier
    channels_md = "\n".join(
        f"- **{c.get('channel', '?')}** [{c.get('status', '?')}] · {c.get('url', '(no url)')}"
        for c in channels
    ) or "_(no channels published)_"

    body = f"""---
name: platform task result · {task_id}
description: {summary[:200].replace(chr(10), ' ')}
type: platform-task-result
concept: outreach-flywheel
drift: {drift}
agent_type: {agent_id}
ingested_via: platform_results_ingest_cron (BP3 file→session_md)
tenant_id: {tenant_id}
thread_role: self_note
thread_id: platform-task-results
---

# Platform task result · {task_id}

**ingested**: {now.isoformat()}
**source**: `{source_filename}`
**agent**: `{agent_id}`
**drift**: `{drift}`
**tenant**: `{tenant_id}`

## Summary

{summary}

## Channels published

{channels_md}

## Raw result JSON

```json
{json.dumps(result, indent=2, ensure_ascii=False)}
```
"""
    return filename, body


def main() -> int:
    if not RESULTS_DIR.exists():
        sys.stderr.write(f"results dir missing · {RESULTS_DIR}\n")
        return 0  # not an error · platform just hasn't emitted yet

    state = _load_state()
    seen = set(state.get("seen", []))
    project_memory_dir = PROJECTS_BASE / DEFAULT_PROJECT / "memory"
    project_memory_dir.mkdir(parents=True, exist_ok=True)

    new_count = 0
    skipped_count = 0
    error_count = 0

    for p in sorted(RESULTS_DIR.glob("*_result.json")):
        key = p.name
        if key in seen:
            skipped_count += 1
            continue
        try:
            result = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            sys.stderr.write(f"parse fail {key}: {e!r}\n")
            error_count += 1
            continue

        missing = [f for f in REQUIRED_FIELDS if f not in result]
        if missing:
            sys.stderr.write(f"skip {key} · missing fields {missing}\n")
            seen.add(key)  # don't retry malformed
            error_count += 1
            continue

        filename, content = _build_session_md(result, source_filename=key)
        target = project_memory_dir / filename
        try:
            target.write_text(content, encoding="utf-8")
            seen.add(key)
            new_count += 1
            print(f"ingested · {key} → {filename}")
        except Exception as e:
            sys.stderr.write(f"write fail {filename}: {e!r}\n")
            error_count += 1
            continue

    state["seen"] = sorted(seen)
    state["ingested_count"] = int(state.get("ingested_count", 0)) + new_count
    state["last_run_ts"] = int(time.time())
    _save_state(state)

    print(f"{datetime.now().isoformat(timespec='seconds')} · "
          f"new={new_count} skipped={skipped_count} errors={error_count} "
          f"total_ingested={state['ingested_count']}")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

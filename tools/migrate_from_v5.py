"""compass v0.9 · v5-memory → compass observations migration · #8 fusion.

Reads ~/v5-memory/ (Nautilus V5/V6 自家 memory protocol if exists) and converts
each entry into a compass session_*.md file with proper frontmatter.

Usage:
  python migrate_from_v5.py [--dry-run] [--source ~/v5-memory] [--target <project>]

Default behavior:
  · source: ~/v5-memory (or env COMPASS_V5_MEMORY_DIR)
  · target: ~/.claude/projects/C--Users-chunx/memory/imported_v5/
  · dry-run: show what would migrate without writing

Schema mapping (best-effort · v5-memory exact format unknown · we infer):
  v5 entry fields (likely)              compass frontmatter
  ----------------------------------    --------------------
  title / subject / topic            →  name
  summary / description              →  description
  body / content / text              →  body
  category / tag                     →  type (mapped to bugfix/feature/...)
  timestamp / ts / created_at        →  filename ts (session_<YYYYMMDD-HHMM>_<slug>.md)
  importance (if present)            →  drift (high → green · low → no field)

If v5-memory is JSON · YAML · markdown · plain text · we handle all.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

DEFAULT_SOURCE = Path.home() / "v5-memory"
DEFAULT_TARGET = Path.home() / ".claude" / "projects" / "C--Users-chunx" / "memory" / "imported_v5"

TYPE_MAP = {
    # v5 category → compass type
    "bug": "bugfix", "fix": "bugfix",
    "feat": "feature", "feature": "feature",
    "refactor": "refactor", "cleanup": "refactor",
    "discover": "discovery", "discovery": "discovery", "found": "discovery",
    "decision": "decision", "choice": "decision",
    "change": "change", "update": "change",
}


def safe_slug(s: str, max_len: int = 30) -> str:
    s = re.sub(r"[^\w一-鿿]+", "-", s).strip("-")
    return s[:max_len] if s else "untitled"


def map_type(category: str | None) -> str:
    if not category:
        return "discovery"
    cat = category.lower()
    for k, v in TYPE_MAP.items():
        if k in cat:
            return v
    return "discovery"


def load_v5_entries(source: Path) -> Iterable[dict]:
    """Try multiple formats: JSON · JSONL · YAML · markdown frontmatter · plain MD."""
    if not source.exists():
        return []

    if source.is_file():
        files = [source]
    else:
        files = list(source.rglob("*.json")) + list(source.rglob("*.jsonl")) + \
                list(source.rglob("*.md")) + list(source.rglob("*.yaml")) + \
                list(source.rglob("*.yml"))

    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        suffix = f.suffix.lower()

        if suffix == ".json":
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            yield {"_source_file": str(f), **item}
                elif isinstance(data, dict):
                    # 整 file 是一条
                    yield {"_source_file": str(f), **data}
            except Exception as e:
                sys.stderr.write(f"[migrate] {f.name}: invalid JSON: {e}\n")

        elif suffix == ".jsonl":
            for ln, line in enumerate(text.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        yield {"_source_file": str(f), "_line": ln, **obj}
                except Exception:
                    pass

        elif suffix == ".md":
            # 尝试 parse frontmatter
            entry = {"_source_file": str(f)}
            if text.startswith("---"):
                end = text.find("\n---", 4)
                if end > 0:
                    fm_block = text[4:end]
                    body = text[end + 4:].strip()
                    for line in fm_block.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            entry[k.strip()] = v.strip().strip('"').strip("'")
                    entry["body"] = body
                    yield entry
                    continue
            # plain text · 用文件名做 title
            entry["title"] = f.stem
            entry["body"] = text
            yield entry

        elif suffix in (".yaml", ".yml"):
            # 简单 yaml parser · 不引入 PyYAML 依赖
            try:
                # very crude · only handle top-level key: value
                entry = {"_source_file": str(f)}
                for line in text.splitlines():
                    if ":" in line and not line.startswith(" "):
                        k, v = line.split(":", 1)
                        entry[k.strip()] = v.strip().strip('"').strip("'")
                if entry:
                    yield entry
            except Exception:
                pass


def make_compass_md(entry: dict) -> tuple[str, str]:
    """Convert v5 entry → (filename, markdown_content)."""
    name = (entry.get("title") or entry.get("subject") or entry.get("name") or
            entry.get("topic") or "untitled")[:60]
    description = (entry.get("summary") or entry.get("description") or
                   entry.get("desc") or "")[:200]
    body = entry.get("body") or entry.get("content") or entry.get("text") or ""
    category = entry.get("category") or entry.get("tag") or entry.get("type")
    type_ = map_type(category)
    importance = entry.get("importance") or entry.get("priority")
    drift = "green" if importance and str(importance).lower() in ("high", "critical", "p0") else "green"

    ts_raw = (entry.get("timestamp") or entry.get("ts") or entry.get("created_at") or
              entry.get("created") or "")
    ts = None
    if ts_raw:
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d", "%Y%m%d-%H%M"):
            try:
                ts = datetime.strptime(str(ts_raw)[:19].replace("Z", ""), fmt.replace("Z", ""))
                break
            except Exception:
                continue
    if ts is None:
        # try fromtimestamp (epoch)
        try:
            ts = datetime.fromtimestamp(float(ts_raw))
        except Exception:
            ts = datetime.now()
    ts_slug = ts.strftime("%Y%m%d-%H%M")
    name_slug = safe_slug(name)
    filename = f"session_{ts_slug}_{name_slug}.md"

    md = f"""---
name: {name}
description: {description}
type: {type_}
concept: pattern
drift: {drift}
drift_signals: []
imported_from: v5-memory
imported_source: {entry.get("_source_file", "?")}
---

# {name}

## 上下文 (imported from v5-memory)
{description}

## 内容
{body[:8000]}
"""
    return filename, md


def main():
    p = argparse.ArgumentParser(description="Migrate v5-memory → compass observations")
    p.add_argument("--source", type=Path, default=os.environ.get("COMPASS_V5_MEMORY_DIR") or DEFAULT_SOURCE)
    p.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0, help="0 = no limit")
    args = p.parse_args()

    src = Path(args.source) if not isinstance(args.source, Path) else args.source
    if not src.exists():
        print(f"[migrate] source not found: {src}")
        print(f"[migrate] set COMPASS_V5_MEMORY_DIR or pass --source")
        return 1

    target = Path(args.target) if not isinstance(args.target, Path) else args.target
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    seen = set()
    count_total = 0
    count_written = 0
    count_skipped = 0
    for entry in load_v5_entries(src):
        count_total += 1
        if args.limit and count_total > args.limit:
            break
        try:
            filename, md = make_compass_md(entry)
        except Exception as e:
            sys.stderr.write(f"[migrate] convert fail: {e} (entry keys: {list(entry.keys())[:5]})\n")
            count_skipped += 1
            continue
        if filename in seen:
            filename = filename.replace(".md", f"_{count_total}.md")
        seen.add(filename)

        if args.dry_run:
            print(f"[dry] would write: {filename} ({len(md)} chars · src={Path(entry.get('_source_file','?')).name})")
        else:
            (target / filename).write_text(md, encoding="utf-8")
            count_written += 1

    print(f"\n=== migration {'DRY-RUN' if args.dry_run else 'COMPLETE'} ===")
    print(f"  total entries scanned: {count_total}")
    print(f"  written:               {count_written}")
    print(f"  skipped:               {count_skipped}")
    print(f"  target:                {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

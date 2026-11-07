#!/usr/bin/env python3
"""Bounded on-disk file budget inventory, not measured prompt/token injection.

Project ownership comes from --project, --cwd, hook JSON cwd,
CLAUDE_PROJECT_DIR, then the actual working directory, in that order.
Unknown/worktree aliases do not inherit Compass memory. Existing historical
MEMORY.md files are metadata-only secondary references, not charged as a
verified injection. No hooks are enabled and no source memories are written.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys

PROJECTS = {
    "platform": "nautilus-core",
    "v5": "nautilus-v5",
    "compass": "nautilus-compass",
    "flywheel": "nautilusflywheel",
}
MAX_INPUT_CHARS = 65536


def size(path):
    try:
        return path.stat().st_size if path.is_file() else 0
    except OSError:
        return 0


def markdown_bytes(path):
    if not path.is_dir():
        return 0
    total = 0
    for item in path.rglob("*.md"):
        total += size(item)
    return total


def positive_env(name, default):
    try:
        value = int(os.environ.get(name, str(default)))
        return value if value > 0 else default
    except (ValueError, TypeError):
        return default


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def choose_project(user_root, cwd, explicit=None):
    repos = {repo: frame for frame, repo in PROJECTS.items()}
    if explicit:
        frame = explicit if explicit in PROJECTS else repos.get(explicit)
        if not frame:
            raise ValueError("unknown explicit project")
        return frame, user_root / "Projects" / PROJECTS[frame], "explicit_project"
    current = Path(cwd).expanduser().resolve()
    for frame, repo in PROJECTS.items():
        root = (user_root / "Projects" / repo).resolve()
        if within(current, root):
            return frame, root, "cwd_match"
    return None, None, "unmatched_cwd"


def namespace_for(user_root, frame, repo):
    catalog = user_root / "Projects/nautilus-core/docs/org/agent_catalog.json"
    # Read only the bounded routing catalog, never credentials or memory bodies.
    try:
        if catalog.is_file() and catalog.stat().st_size <= 65536:
            with catalog.open("rb") as stream:
                raw = stream.read(65537)
            if len(raw) <= 65536:
                data = json.loads(raw)
                for entry in data.get("agents", []):
                    if entry.get("id") == frame and entry.get("repo_dir") == repo.name:
                        value = entry.get("memory_project")
                        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,255}", value):
                            return value, "catalog"
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return re.sub(r"[^A-Za-z0-9-]", "-", str(repo.resolve())), "derived_path"


def inspect_budget(cwd, explicit=None, user_root=None):
    user_root = Path(user_root) if user_root is not None else Path.home()
    red = positive_env("COMPASS_FLOOR_RED_KB", 90) * 1024
    rules_limit = positive_env("COMPASS_RULES_LIMIT_KB", 40) * 1024
    index_limit = positive_env("COMPASS_MEM_LIMIT_KB", 8) * 1024
    frame, repo, selection = choose_project(user_root, cwd, explicit)
    # Compatibility inventory of the original counter's global candidate files.
    # These files are not asserted to be loaded by Codex or any current session.
    rows = [
        {"label": "Claude rules/", "path": str(user_root / ".claude/rules"),
         "bytes": markdown_bytes(user_root / ".claude/rules"), "budget_bytes": rules_limit},
        {"label": "Claude global CLAUDE.md", "path": str(user_root / ".claude/CLAUDE.md"),
         "bytes": size(user_root / ".claude/CLAUDE.md"), "budget_bytes": 0},
        {"label": "ORG_BRIEF.md", "path": str(user_root / ".claude/ORG_BRIEF.md"),
         "bytes": size(user_root / ".claude/ORG_BRIEF.md"), "budget_bytes": 0},
    ]
    history = None
    if repo is not None:
        for name in ["AGENTS.md", "CLAUDE.md"]:
            rows.append({"label": "project " + name, "path": str(repo / name),
                         "bytes": size(repo / name), "budget_bytes": 0})
        maintained = repo / "docs/agent-memory.index.md"
        rows.append({"label": "docs/agent-memory.index.md (on-demand entry)",
                     "path": str(maintained), "bytes": size(maintained),
                     "budget_bytes": index_limit})
        namespace, namespace_source = namespace_for(user_root, frame, repo)
        legacy = user_root / ".claude/projects" / namespace / "memory/MEMORY.md"
        history = {"path": str(legacy), "bytes": size(legacy), "namespace": namespace,
                   "namespace_source": namespace_source, "budget_applied": False,
                   "read_mode": "secondary historical index; body not read or assumed injected"}
    total = sum(row["bytes"] for row in rows)
    over = [row for row in rows if row["budget_bytes"] and row["bytes"] > row["budget_bytes"]]
    return {
        "measurement": "on_disk_candidate_file_budget",
        "actual_prompt_or_token_injection_measured": False,
        "frame": frame, "project_selection": selection,
        "project_repo": str(repo) if repo is not None else None,
        "candidate_files": rows, "candidate_total_bytes": total,
        "total_alert_threshold_bytes": red, "over_budget": over,
        "secondary_history_index": history,
        "alert": total >= red or bool(over),
        "limits": [
            "File inventory is not proof of actual Codex/Claude prompt loading.",
            "Unknown roots/worktrees need an explicit reviewed --project mapping.",
            "Secondary MEMORY.md is preserved; metadata does not prove its full body was injected.",
        ],
    }


def input_cwd(args):
    if args.cwd:
        return args.cwd, "explicit_cwd"
    event = {}
    note = "no_hook_cwd"
    if not sys.stdin.isatty():
        raw = sys.stdin.read(MAX_INPUT_CHARS + 1)
        if len(raw) > MAX_INPUT_CHARS:
            note = "hook_input_over_bound"
        elif raw.strip():
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    event = parsed
                else:
                    note = "hook_input_not_object"
            except (ValueError, UnicodeError):
                note = "hook_input_invalid_json"
    candidate = event.get("cwd")
    if isinstance(candidate, str) and candidate:
        return candidate, "hook_cwd"
    candidate = os.environ.get("CLAUDE_PROJECT_DIR")
    if candidate:
        return candidate, "claude_project_dir"
    return os.getcwd(), note


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=list(PROJECTS) + list(PROJECTS.values()))
    parser.add_argument("--cwd")
    parser.add_argument("--json", action="store_true", help="emit inventory, not prompt contents")
    args = parser.parse_args()
    cwd, source = input_cwd(args)
    result = inspect_budget(cwd, args.project)
    result["cwd_source"] = source
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["alert"]:
        parts = " ".join(row["label"] + "=" + str(row["bytes"] // 1024) + "KB"
                         for row in result["candidate_files"])
        print("[orgup-preflight] 磁盘候选文件预算估计=" +
              str(result["candidate_total_bytes"] // 1024) + "KB; frame=" +
              str(result["frame"] or "unmatched") + "。不是实际上下文注入或token计量。 " + parts)
        if result["over_budget"]:
            print("超限候选: " + "; ".join(row["label"] for row in result["over_budget"]) +
                  "；先核消费者加载与来源，再决定瘦身。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, RuntimeError):
        print("[orgup-preflight] 文件预算未核；未作注入或项目记忆结论。", file=sys.stderr)
        sys.exit(0)

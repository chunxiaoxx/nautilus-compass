#!/usr/bin/env python3
"""Nautilus Compass MCP server · JSON-RPC 2.0 over stdio.

Exposes 3 tools to any MCP client (Claude Code, Hermes, OpenClaw, ...):
  · recall(query, project?, top_k?=5) → top-k memory hits
  · drift_check(prompt, project?)     → alignment/deviation/alert
  · feedback_log(direction, reason)   → record for adaptive anchor retrain

Backend: TCP daemon on 127.0.0.1:9876 (BGE-m3 hot model · ~200ms latency).
Daemon down → tools return error · client should retry after `daemon_start.sh`.

Stdlib only · no mcp SDK dep · keep install footprint tiny.

Run:   python -m nautilus_compass.mcp_server
Or as MCP stdio server registered in Claude Code .mcp.json:
   { "nautilus-compass": { "command": "python3",
     "args": ["~/.claude/plugins/nautilus-compass/mcp_server.py"] } }
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "nautilus-compass"
SERVER_VERSION = "0.9.0-dev"
DAEMON_HOST = "127.0.0.1"
DAEMON_PORT = 9876
DAEMON_TIMEOUT = 30.0

PLUGIN_DIR = Path(__file__).resolve().parent
CACHE_DIR = PLUGIN_DIR / ".cache"
FEEDBACK_LOG = CACHE_DIR / "feedback.jsonl"
PROJECTS_DIR = Path.home() / ".claude" / "projects"


# ─── daemon I/O ────────────────────────────────────────────────────

def daemon_call(req: dict, timeout: float = DAEMON_TIMEOUT) -> dict:
    """Send JSON request to BGE daemon · return parsed reply.

    Raises socket.error / json.JSONDecodeError on transport failure.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((DAEMON_HOST, DAEMON_PORT))
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n"):
                break
        return json.loads(buf.decode("utf-8"))
    finally:
        s.close()


def resolve_project(explicit: str | None) -> str | None:
    """Pick project memory dir name. Explicit > env > most-recently-modified."""
    if explicit:
        return explicit
    env = os.environ.get("NAUTILUS_COMPASS_PROJECT")
    if env:
        return env
    if not PROJECTS_DIR.exists():
        return None
    best, best_mtime = None, 0.0
    for d in PROJECTS_DIR.iterdir():
        mem = d / "memory"
        if not mem.is_dir():
            continue
        try:
            mtime = max((f.stat().st_mtime for f in mem.glob("*.md")), default=0)
        except Exception:
            mtime = 0
        if mtime > best_mtime:
            best, best_mtime = d.name, mtime
    return best


# ─── tools ─────────────────────────────────────────────────────────

def tool_recall(args: dict) -> dict:
    query = (args.get("query") or "").strip()
    if not query:
        return _err("query required")
    project = resolve_project(args.get("project"))
    if not project:
        return _err("no project memory found · set NAUTILUS_COMPASS_PROJECT or pass project=")
    top_k = int(args.get("top_k") or 5)
    try:
        res = daemon_call({"action": "recall", "query": query, "project": project, "top_k": top_k})
    except Exception as e:
        return _err(f"daemon unreachable: {e} · run daemon_start.sh")
    if not res.get("ok"):
        return _err(res.get("error", "daemon error"))
    hits = res.get("recall", [])
    if not hits:
        text = f"No memories matched for query: {query!r} (project={project})"
    else:
        lines = [f"Recall · query={query!r} · project={project} · {len(hits)} hits"]
        for h in hits:
            lines.append(
                f"  · score={h['score']:.3f} · {h['age_str']} · {h['path']}\n"
                f"    {h.get('description', '')[:140]}"
            )
        fresh = res.get("fresh_extra") or []
        if fresh:
            lines.append(f"\nFresh memories not in top (last 24h, {len(fresh)} extra):")
            for f in fresh[:5]:
                lines.append(f"  · {f['age_str']} · {f['path']}: {f.get('description', '')[:80]}")
        text = "\n".join(lines)
    return _ok(text)


def tool_drift_check(args: dict) -> dict:
    prompt = (args.get("prompt") or "").strip()
    if not prompt:
        return _err("prompt required")
    project = resolve_project(args.get("project"))
    if not project:
        # drift detection works without project memory · use any project name as placeholder
        project = "C--Users-chunx"
    try:
        res = daemon_call(
            {"action": "drift", "query": prompt, "project": project, "top_k": 1}
        )
    except Exception as e:
        return _err(f"daemon unreachable: {e}")
    if not res.get("ok"):
        return _err(res.get("error", "daemon error"))
    d = res.get("drift") or {}
    if not d:
        return _err("no anchors loaded · check anchors.json")
    score = d["score"]
    alert = d["should_alert"]
    lines = [
        f"Drift check · {d['n_pos']}+{d['n_neg']} anchors · BGE-m3",
        f"  score={score:+.3f} (alignment={d['alignment']:.3f} · deviation={d['deviation']:.3f})",
        f"  alert={alert}",
    ]
    if d.get("top_neg_hits"):
        lines.append("  top negative anchor hits:")
        for cos, txt in d["top_neg_hits"]:
            lines.append(f"    · cos={cos:.3f} · {txt[:120]}")
    return _ok("\n".join(lines))


def tool_ingest_obs(args: dict) -> dict:
    """v0.9 · 写一条 observation 到当前 user 的 memory · 跨 agent 融合.

    Direct write (bypass LLM distillation) · suitable for explicit agent reports.
    For session-end auto-distill, the Stop hook handles that automatically.
    """
    name = (args.get("name") or "").strip()
    if not name:
        return _err("name required")
    description = (args.get("description") or "").strip()
    body = (args.get("body") or "").strip()
    type_ = (args.get("type") or "discovery").strip()
    concept = (args.get("concept") or "pattern").strip()
    drift = (args.get("drift") or "green").strip()
    if drift not in ("green", "yellow", "red"):
        drift = "green"
    drift_signals = args.get("drift_signals") or []
    agent_type = (args.get("agent_type") or os.environ.get("COMPASS_AGENT_TYPE") or "custom").strip()
    user_id = os.environ.get("COMPASS_USER_ID", "u_local")
    project = resolve_project(args.get("project"))
    if not project:
        project = "C--Users-chunx"

    # Format as v0.8 session_*.md frontmatter
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    import re
    slug = re.sub(r"[^\w一-鿿]+", "-", name).strip("-")[:30] or "obs"
    out_dir = PROJECTS_DIR / project / "memory"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"session_{ts}_{slug}.md"

    # Build markdown
    signals_yaml = "[]" if not drift_signals else "\n  - " + "\n  - ".join(f'"{s}"' for s in drift_signals)
    md = f"""---
name: {name}
description: {description[:200]}
type: {type_}
concept: {concept}
drift: {drift}
drift_signals: {signals_yaml}
agent_type: {agent_type}
user_id: {user_id}
ingested_via: mcp
---

# {name}

## 上下文
{description}

## 内容
{body}
"""
    out_file.write_text(md, encoding="utf-8")
    return _ok(f"obs written · {out_file.name} · agent_type={agent_type} · drift={drift}")


def tool_drift_history(args: dict) -> dict:
    """v0.9 · 跨 project 看用户的 drift timeline · claude-mem 没有的能力."""
    days = int(args.get("days") or 30)
    project_filter = args.get("project_filter")
    sys.path.insert(0, str(PLUGIN_DIR))
    try:
        from drift_history import collect_sessions
    except Exception as e:
        return _err(f"drift_history module not loadable: {e}")
    rows = collect_sessions(days, project_filter)
    if not rows:
        return _ok(f"No sessions in last {days}d")
    from collections import Counter
    counts = Counter(r["drift"] for r in rows)
    lines = [
        f"Drift history · last {days}d · {len(rows)} sessions across {len(set(r['project'] for r in rows))} projects",
        f"  green:  {counts.get('green',0)} · AI 一次到位",
        f"  yellow: {counts.get('yellow',0)} · 小绕弯及时纠正",
        f"  red:    {counts.get('red',0)} · 偏离意图",
        f"  ?:      {counts.get('?',0)} · 老格式无 drift",
    ]
    reds = [r for r in rows if r["drift"] == "red"]
    if reds:
        lines.append("\nRED sessions:")
        for r in reds[:5]:
            lines.append(f"  · [{r['project']}] {r['name']}")
            for sig in r.get("drift_signals", [])[:3]:
                lines.append(f"      · {sig}")
    yellow_sigs = []
    for r in rows:
        if r["drift"] == "yellow":
            yellow_sigs.extend(r.get("drift_signals", []))
    if yellow_sigs:
        from collections import Counter as C
        top = C(yellow_sigs).most_common(3)
        lines.append("\nTop yellow signals:")
        for sig, c in top:
            lines.append(f"  {c}× · {sig}")
    return _ok("\n".join(lines))


def tool_session_search(args: dict) -> dict:
    """v0.9 · 跨 project keyword search session_*.md · drift/type 过滤."""
    query = (args.get("query") or "").strip()
    if not query:
        return _err("query required")
    drift = args.get("drift")
    type_ = args.get("type")
    days = int(args.get("days") or 60)
    top_k = int(args.get("top_k") or 5)
    sys.path.insert(0, str(PLUGIN_DIR))
    try:
        from session_search import search
    except Exception as e:
        return _err(f"session_search module not loadable: {e}")
    hits = search(query, drift=drift, type_filter=type_, days=days, top=top_k)
    if not hits:
        return _ok(f"No matches for '{query}'")
    lines = [f"{len(hits)} hits for '{query}' (drift={drift or 'any'} · last {days}d)"]
    for h in hits:
        fm = h["fm"]
        lines.append(
            f"  [{h['score']:.1f}] [{h['project']}] {fm.get('name','?')} "
            f"({fm.get('drift','?')} · {fm.get('type','?')})"
        )
    return _ok("\n".join(lines))


def tool_profile(args: dict) -> dict:
    """v0.9 · 用户画像 (placeholder · v1.0 client-side aggregate)."""
    days = int(args.get("days") or 90)
    sys.path.insert(0, str(PLUGIN_DIR))
    try:
        from drift_history import collect_sessions
    except Exception as e:
        return _err(f"profile module fail: {e}")
    rows = collect_sessions(days, None)
    if not rows:
        return _ok(f"No data in last {days}d")
    from collections import Counter
    types = Counter(r.get("type", "?") for r in rows)
    drifts = Counter(r.get("drift", "?") for r in rows)
    projs = Counter(r["project"] for r in rows)
    lines = [
        f"User profile (last {days}d · {len(rows)} sessions)",
        "",
        f"Top projects:",
    ]
    for p, c in projs.most_common(5):
        lines.append(f"  {c:3d} · {p}")
    lines.append(f"\nWork types:")
    for t, c in types.most_common():
        lines.append(f"  {c:3d} · {t}")
    lines.append(f"\nDrift:")
    for d, c in drifts.most_common():
        lines.append(f"  {c:3d} · {d}")
    return _ok("\n".join(lines))


def tool_feedback_log(args: dict) -> dict:
    direction = (args.get("direction") or "").strip().lower()
    if direction not in ("good", "bad"):
        return _err("direction must be 'good' or 'bad'")
    reason = (args.get("reason") or "").strip()[:500]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "mcp",
        "direction": direction,
        "reason": reason,
    }
    with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return _ok(f"feedback logged · run `python feedback.py retrain` to update anchors")


TOOLS = {
    "ingest_obs": {
        "fn": tool_ingest_obs,
        "schema": {
            "name": "ingest_obs",
            "description": "v0.9 · Write one observation to the user's cross-agent memory. Use after a discrete task/decision/discovery. Includes drift self-audit (claude-mem can't do this).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "8-15 char title · Chinese OK"},
                    "description": {"type": "string", "description": "≤200 char one-liner"},
                    "body": {"type": "string", "description": "Full observation text"},
                    "type": {"type": "string", "enum": ["bugfix","feature","refactor","discovery","decision","change"], "default": "discovery"},
                    "concept": {"type": "string", "enum": ["gotcha","pattern","trade-off","how-it-works","why-it-exists","problem-solution","what-changed"], "default": "pattern"},
                    "drift": {"type": "string", "enum": ["green","yellow","red"], "default": "green", "description": "AI drift self-audit · honest reporting"},
                    "drift_signals": {"type": "array", "items": {"type": "string"}, "default": [], "description": "Concrete evidence if drift!=green"},
                    "agent_type": {"type": "string", "description": "Which agent ingesting (claude-code/openclaw/hermes/cursor/codex/custom). Defaults to env COMPASS_AGENT_TYPE."},
                    "project": {"type": "string", "description": "Target project (defaults to most-recent)"},
                },
                "required": ["name"],
            },
        },
    },
    "drift_history": {
        "fn": tool_drift_history,
        "schema": {
            "name": "drift_history",
            "description": "v0.9 · Cross-project AI drift timeline. green/yellow/red counts, top RED sessions with signals. compass-only feature.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 30},
                    "project_filter": {"type": "string", "description": "Optional substring match"},
                },
            },
        },
    },
    "session_search": {
        "fn": tool_session_search,
        "schema": {
            "name": "session_search",
            "description": "v0.9 · Keyword search across all session_*.md files in user's projects. Supports drift/type filter.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "drift": {"type": "string", "enum": ["green","yellow","red"]},
                    "type": {"type": "string", "enum": ["bugfix","feature","refactor","discovery","decision","change"]},
                    "days": {"type": "integer", "default": 60},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    "profile": {
        "fn": tool_profile,
        "schema": {
            "name": "profile",
            "description": "v0.9 · User profile derived from session aggregate (top projects · work types · drift dist). v1.0 will add client-side E2EE aggregation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 90},
                },
            },
        },
    },
    "recall": {
        "fn": tool_recall,
        "schema": {
            "name": "recall",
            "description": "Semantic recall over user's persistent memory (BGE-m3 over .md files in ~/.claude/projects/<project>/memory/). Returns top-k matches by cosine similarity, plus any memories from the last 24h not already in top-k.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "project": {"type": "string", "description": "Project memory dir name (e.g. 'C--Users-chunx'). Defaults to most-recently-modified."},
                    "top_k": {"type": "integer", "default": 5, "description": "Number of hits to return"},
                },
                "required": ["query"],
            },
        },
    },
    "drift_check": {
        "fn": tool_drift_check,
        "schema": {
            "name": "drift_check",
            "description": "Black-box persona drift detection. Embeds the prompt and compares to 25 task-shaped positive anchors (aligned behavior) vs 35 negative anchors (drift exemplars). Returns drift score, alignment/deviation cosines, and an alert flag if score < threshold or any negative anchor strongly matches.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "User prompt or agent action to evaluate"},
                    "project": {"type": "string", "description": "Project name (optional, only affects logging)"},
                },
                "required": ["prompt"],
            },
        },
    },
    "feedback_log": {
        "fn": tool_feedback_log,
        "schema": {
            "name": "feedback_log",
            "description": "Log a true-positive (good) or false-positive (bad) signal for adaptive anchor retraining. After accumulating signals, run `python feedback.py retrain` to update anchor weights.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["good", "bad"], "description": "good = drift correctly caught · bad = false positive"},
                    "reason": {"type": "string", "description": "Short explanation (≤500 chars)"},
                },
                "required": ["direction"],
            },
        },
    },
}


# ─── helpers ───────────────────────────────────────────────────────

def _ok(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _err(msg: str) -> dict:
    return {"content": [{"type": "text", "text": f"Error: {msg}"}], "isError": True}


# ─── JSON-RPC 2.0 dispatch ─────────────────────────────────────────

def handle_message(msg: dict) -> dict | None:
    method = msg.get("method", "")
    params = msg.get("params") or {}
    msg_id = msg.get("id")

    if method == "initialize":
        return _reply(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
    if method == "notifications/initialized":
        return None  # notification · no reply
    if method == "tools/list":
        return _reply(msg_id, {"tools": [t["schema"] for t in TOOLS.values()]})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        tool = TOOLS.get(name)
        if not tool:
            return _reply_err(msg_id, -32601, f"unknown tool: {name}")
        try:
            return _reply(msg_id, tool["fn"](args))
        except Exception as e:
            return _reply_err(msg_id, -32603, f"tool {name} failed: {e}")
    if method == "ping":
        return _reply(msg_id, {})
    return _reply_err(msg_id, -32601, f"method not found: {method}")


def _reply(msg_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _reply_err(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


# ─── stdio loop ────────────────────────────────────────────────────

def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = handle_message(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

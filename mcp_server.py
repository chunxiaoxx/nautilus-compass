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
SERVER_VERSION = "0.7.0"
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

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
SERVER_VERSION = "1.6.2"
DAEMON_HOST = "127.0.0.1"
DAEMON_PORT = 9876
DAEMON_TIMEOUT = 30.0

# v1.5 · S2 proof-of-recall · in-memory token store · 30 min TTL · LRU evict at 1000
RECALL_TOKEN_TTL_S = 1800
RECALL_TOKEN_MAX = 1000

PLUGIN_DIR = Path(__file__).resolve().parent
CACHE_DIR = PLUGIN_DIR / ".cache"
FEEDBACK_LOG = CACHE_DIR / "feedback.jsonl"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
PLATFORM_QUEUE_DIR = PROJECTS_DIR / "_platform_queue"
PLATFORM_RESULTS_DIR = PROJECTS_DIR / "_platform_results"
GOVERNANCE_LOCK = PLUGIN_DIR / "governance.lock"
GOVERNANCE_AUDIT_DIR = PROJECTS_DIR / "_governance_audits"
PLATFORM_REGISTRY_DIR = PROJECTS_DIR / "_platform_registry"
V7_DEFAULT_CAPABILITIES = PLUGIN_DIR / "examples" / "v7_default_capabilities.json"
V7_DEFAULT_PHASES = PLUGIN_DIR / "examples" / "v7_default_phases.json"


# ─── daemon I/O ────────────────────────────────────────────────────

def daemon_call(req: dict, timeout: float = DAEMON_TIMEOUT) -> dict:
    """Send JSON request to BGE daemon · return parsed reply.

    Raises socket.error / json.JSONDecodeError on transport failure.

    v1.3 · forwards COMPASS_AGENT_TYPE env to daemon for per-agent L2
    evidence in verification_log.jsonl (#104).
    """
    if "agent_type" not in req:
        env_agent = os.environ.get("COMPASS_AGENT_TYPE")
        if env_agent:
            req = {**req, "agent_type": env_agent}
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


# ─── v1.5 · S2 proof-of-recall · token store ──────────────────────

import secrets as _secrets
from collections import OrderedDict as _OrderedDict

# token → {issued_at, agent_type, top3_paths, top3_descriptions, query}
# OrderedDict for LRU · access bumps to end · oldest at start
_recall_tokens: "_OrderedDict[str, dict]" = _OrderedDict()


def _mint_recall_token(agent_type: str, top3: list, query: str) -> str:
    """Generate recall_token · register top3 snippets · LRU evict + TTL prune."""
    now = time.time()
    # prune expired
    expired = [k for k, v in _recall_tokens.items()
               if now - v["issued_at"] > RECALL_TOKEN_TTL_S]
    for k in expired:
        _recall_tokens.pop(k, None)
    # LRU evict if over max
    while len(_recall_tokens) >= RECALL_TOKEN_MAX:
        _recall_tokens.popitem(last=False)
    token = "rt_" + _secrets.token_hex(8)
    _recall_tokens[token] = {
        "issued_at": now,
        "agent_type": (agent_type or "unknown")[:60],
        "query": (query or "")[:200],
        "top3_paths": [(h.get("path") or "") for h in top3],
        # store BOTH path basenames and description text · client can cite either
        "top3_descriptions": [(h.get("description") or "")[:300] for h in top3],
    }
    return token


def _validate_recall_proof(token: str, cited_snippets: list, agent_type: str) -> tuple[bool, str]:
    """Check token live + agent matches + at least 1 cited snippet matches a top3 entry.

    Returns: (ok, reason)
      ok=True · reason=""
      ok=False · reason ∈ {"token_not_found_or_expired", "agent_type_mismatch", "no_snippet_overlap", "empty_cited"}
    """
    if not token or not isinstance(token, str):
        return False, "no_token_provided"
    rec = _recall_tokens.get(token)
    if not rec:
        return False, "token_not_found_or_expired"
    now = time.time()
    if now - rec["issued_at"] > RECALL_TOKEN_TTL_S:
        _recall_tokens.pop(token, None)
        return False, "token_not_found_or_expired"
    if rec["agent_type"] != (agent_type or "unknown")[:60]:
        return False, "agent_type_mismatch"
    if not cited_snippets or not isinstance(cited_snippets, list):
        return False, "empty_cited"
    # snippet match: cited string must contain part of top3 path OR substantial overlap with description
    valid = False
    for cs in cited_snippets:
        if not isinstance(cs, str):
            continue
        cs_lower = cs.lower().strip()
        if len(cs_lower) < 5:
            continue
        # path basename match
        for path in rec["top3_paths"]:
            base = path.rsplit("/", 1)[-1].lower()
            if base and base in cs_lower:
                valid = True; break
        if valid: break
        # description overlap (>= 20 chars contiguous)
        for desc in rec["top3_descriptions"]:
            if not desc: continue
            desc_lower = desc.lower()
            # check for >= 20-char contiguous overlap
            for i in range(0, len(cs_lower) - 19):
                if cs_lower[i:i+20] in desc_lower:
                    valid = True; break
            if valid: break
        if valid: break
    if not valid:
        return False, "no_snippet_overlap"
    return True, ""


# ─── end v1.5 · S2 ─────────────────────────────────────────────────


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
    # v1.4 · scope=project (default · current behavior) or scope=user (cross-project union for same user)
    scope = (args.get("scope") or "project").strip().lower()
    if scope not in ("project", "user"):
        return _err(f"scope must be 'project' or 'user' · got {scope!r}")
    project = resolve_project(args.get("project"))
    if not project and scope == "project":
        return _err("no project memory found · set NAUTILUS_COMPASS_PROJECT or pass project=")
    top_k = int(args.get("top_k") or 5)
    # v1.3 #104 · forward client-supplied agent_type to daemon log
    agent_type = args.get("agent_type") or os.environ.get("COMPASS_AGENT_TYPE")
    try:
        req = {"action": "recall", "query": query, "top_k": top_k, "scope": scope}
        if project:
            req["project"] = project
        if agent_type:
            req["agent_type"] = agent_type
        res = daemon_call(req)
    except Exception as e:
        return _err(f"daemon unreachable: {e} · run daemon_start.sh")
    if not res.get("ok"):
        return _err(res.get("error", "daemon error"))
    hits = res.get("recall", [])
    scope_label = f"scope={scope}" + (f", project={project}" if scope == "project" else " (all projects)")
    if not hits:
        text = f"No memories matched for query: {query!r} ({scope_label})"
    else:
        # v1.5 · S2 proof-of-recall · mint token for top3 · agent quotes 1+ snippet in next ingest_obs
        recall_token = _mint_recall_token(agent_type or "unknown", hits[:3], query)
        lines = [
            f"Recall · query={query!r} · {scope_label} · {len(hits)} hits",
            f"recall_token: {recall_token}  (cite ≥1 snippet in next ingest_obs · 30 min TTL · proof-of-recall)",
        ]
        for h in hits:
            origin = f" [{h['project']}]" if scope == "user" and h.get("project") else ""
            lines.append(
                f"  · score={h['score']:.3f} · {h['age_str']}{origin} · {h['path']}\n"
                f"    {h.get('description', '')[:140]}"
            )
        fresh = res.get("fresh_extra") or []
        if fresh:
            lines.append(f"\nFresh memories not in top (last 24h, {len(fresh)} extra):")
            for f in fresh[:5]:
                lines.append(f"  · {f['age_str']} · {f['path']}: {f.get('description', '')[:80]}")
        text = "\n".join(lines)
    return _ok(text)


def tool_thread_recall(args: dict) -> dict:
    """v1.1 · L3 dogfood · multi-turn thread recall by thread_id frontmatter tag.

    Use case: V7 partnership-loop / engagement-cron — agent talks with a
    founder/commenter over 7-14 days across many messages. White-box memory
    abstracts these into facts and loses raw thread. Compass keeps raw
    session_*.md per message tagged with `thread_id` in frontmatter; this
    tool returns the chronological message stream so the next reply call
    has full context.

    Inputs: thread_id (required), project (optional), since (optional ISO),
            limit (default 50), include_body (default true).

    Returns: ordered list of {ts, thread_role, name, description, body, path}
    sorted by file mtime ASC. Empty list if no matching session_*.md.
    """
    thread_id = (args.get("thread_id") or "").strip()
    if not thread_id:
        return _err("thread_id required")
    project = resolve_project(args.get("project"))
    if not project:
        return _err("no project memory found · set NAUTILUS_COMPASS_PROJECT or pass project=")
    limit = int(args.get("limit") or 50)
    since_iso = (args.get("since") or "").strip()
    include_body = args.get("include_body", True)

    mem_dir = PROJECTS_DIR / project / "memory"
    if not mem_dir.is_dir():
        return _err(f"memory dir not found: {mem_dir}")

    since_ts = 0.0
    if since_iso:
        try:
            from datetime import datetime
            since_ts = datetime.fromisoformat(since_iso.replace("Z", "+00:00")).timestamp()
        except Exception:
            return _err(f"invalid since ISO timestamp: {since_iso}")

    hits = []
    for f in mem_dir.glob("session_*.md"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        fm = {}
        body = text
        if text.startswith("---"):
            end = text.find("\n---", 4)
            if end > 0:
                for line in text[4:end].split("\n"):
                    if ":" in line:
                        k, _, v = line.partition(":")
                        fm[k.strip().lower()] = v.strip()
                body = text[end + 4:].strip()
        if fm.get("thread_id") != thread_id:
            continue
        mtime = f.stat().st_mtime
        if mtime < since_ts:
            continue
        hits.append({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mtime)),
            "ts_epoch": mtime,
            "thread_role": fm.get("thread_role", "self_note"),
            "name": fm.get("name", ""),
            "description": fm.get("description", "")[:200],
            "body": body[:2000] if include_body else "",
            "path": f.name,
        })

    hits.sort(key=lambda x: x["ts_epoch"])
    hits = hits[:limit]
    if not hits:
        return _ok(f"thread_recall · thread_id={thread_id!r} · 0 messages (no session_*.md tagged with this thread_id in {mem_dir})")

    lines = [
        f"thread_recall · thread_id={thread_id!r} · project={project} · {len(hits)} messages chronological"
    ]
    for h in hits:
        lines.append(
            f"\n[{h['ts']}] {h['thread_role']} · {h['name']}\n"
            f"  ({h['path']})\n"
            f"  desc: {h['description']}"
        )
        if include_body and h["body"]:
            indented = "\n".join("  | " + ln for ln in h["body"].split("\n"))
            lines.append(indented)
    return _ok("\n".join(lines))


def tool_drift_check(args: dict) -> dict:
    prompt = (args.get("prompt") or "").strip()
    if not prompt:
        return _err("prompt required")
    project = resolve_project(args.get("project"))
    if not project:
        # drift detection works without project memory · use any project name as placeholder
        project = "C--Users-chunx"

    # v1.0+ · v2 · always run consumption audit (independent of BGE daemon).
    # This is the failure mode where recall surfaced the right files but the
    # agent skipped reading bodies. Runs even when daemon is down.
    consumption_warn: str | None = None
    try:
        from recall_consumption import audit_consumption, render_consumption_warning
        rep = audit_consumption(window_user_turns=5)
        consumption_warn = render_consumption_warning(rep)
    except Exception:
        pass

    # v1.3 #104 · forward client-supplied agent_type to daemon log
    agent_type = args.get("agent_type") or os.environ.get("COMPASS_AGENT_TYPE")
    try:
        req = {"action": "drift", "query": prompt, "project": project, "top_k": 1}
        if agent_type:
            req["agent_type"] = agent_type
        anchors_path = args.get("anchors_path")
        if anchors_path:
            req["anchors_path"] = anchors_path
        res = daemon_call(req)
    except Exception as e:
        # Daemon down · still surface consumption audit if any (don't waste it)
        if consumption_warn:
            return _ok(f"daemon unreachable: {e} · BGE drift skipped\n\n{consumption_warn}")
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
    if consumption_warn:
        lines.append("")
        lines.append(consumption_warn)
    return _ok("\n".join(lines))


def tool_ingest_obs(args: dict) -> dict:
    """v0.9 · 写一条 observation 到当前 user 的 memory · 跨 agent 融合.

    Direct write (bypass LLM distillation) · suitable for explicit agent reports.
    For session-end auto-distill, the Stop hook handles that automatically.

    v1.5 · S2 proof-of-recall · optional `recall_token` + `cited_snippets`:
      · recall_token from previous recall call (30 min TTL)
      · cited_snippets = list of strings · each must overlap one top3 path/desc
      · validation result written to frontmatter `proof_of_recall: pass|fail|not_attempted`
      · backward compatible: omit both → not_attempted · ingest still succeeds
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
    # v1.1 · L3 dogfood · optional thread tagging for thread_recall
    thread_id = (args.get("thread_id") or "").strip()
    thread_role = (args.get("thread_role") or "").strip()
    if thread_role and thread_role not in ("outbound", "inbound", "self_note"):
        thread_role = "self_note"

    # v1.5 · S2 proof-of-recall validation
    recall_token = (args.get("recall_token") or "").strip()
    cited_snippets = args.get("cited_snippets") or []
    if recall_token or cited_snippets:
        ok, reason = _validate_recall_proof(recall_token, cited_snippets, agent_type)
        proof_of_recall = "pass" if ok else "fail"
        proof_reason = "" if ok else reason
    else:
        proof_of_recall = "not_attempted"
        proof_reason = ""

    # v1.7 · MEME-extension · declaration_field (depends_on / declaration_type / supersedes)
    # See paper/SPEC_DECLARATION_FIELD.md §2 for design rationale.
    depends_on = args.get("depends_on") or []
    if not isinstance(depends_on, list):
        depends_on = []
    declaration_type = (args.get("declaration_type") or "none").strip()
    if declaration_type not in ("cascade", "absence", "deletion", "none"):
        declaration_type = "none"
    supersedes = args.get("supersedes") or []
    if not isinstance(supersedes, list):
        supersedes = []
    if declaration_type != "deletion":
        supersedes = []  # only meaningful when declaration_type=deletion

    # v1.7.1 · lifecycle extension (llm-wiki2 fuse) · tier/decay_rate/forget_at/promote_after/reinforce_count
    # See paper/LLM_WIKI2_FUSE_DESIGN.md §3 for schema rationale.
    LIFECYCLE_TIERS = ("working", "episodic", "semantic", "procedural")
    TIER_DEFAULT_PROMOTE = {
        "working": "1_access",
        "episodic": "5_access",
        "semantic": "20_access",
        "procedural": None,
    }
    tier = (args.get("tier") or "working").strip()
    if tier not in LIFECYCLE_TIERS:
        tier = "working"
    try:
        decay_rate = float(args.get("decay_rate", 0.5))
        if not (0.0 <= decay_rate <= 1.0):
            decay_rate = 0.5
    except (TypeError, ValueError):
        decay_rate = 0.5
    forget_at = (args.get("forget_at") or "").strip() or None
    promote_after = (args.get("promote_after") or "").strip() or TIER_DEFAULT_PROMOTE.get(tier)
    try:
        reinforce_count = int(args.get("reinforce_count", 0))
        if reinforce_count < 0:
            reinforce_count = 0
    except (TypeError, ValueError):
        reinforce_count = 0

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
    thread_lines = ""
    if thread_id:
        thread_lines = f"\nthread_id: {thread_id}\nthread_role: {thread_role or 'self_note'}"
    proof_lines = f"\nproof_of_recall: {proof_of_recall}"
    if proof_reason:
        proof_lines += f"\nproof_of_recall_reason: {proof_reason}"
    # v1.7 · MEME-extension · emit depends_on/declaration_type/supersedes
    dep_lines = ""
    if depends_on:
        dep_lines += "\ndepends_on:\n  - " + "\n  - ".join(depends_on)
    dep_lines += f"\ndeclaration_type: {declaration_type}"
    if supersedes:
        dep_lines += "\nsupersedes:\n  - " + "\n  - ".join(supersedes)

    # v1.7.1 · lifecycle extension · emit tier/decay_rate/forget_at/promote_after/reinforce_count
    # See paper/LLM_WIKI2_FUSE_DESIGN.md §3.
    lifecycle_lines = f"\ntier: {tier}"
    lifecycle_lines += f"\ndecay_rate: {decay_rate}"
    if forget_at:
        lifecycle_lines += f"\nforget_at: {forget_at}"
    if promote_after:
        lifecycle_lines += f"\npromote_after: {promote_after}"
    lifecycle_lines += f"\nreinforce_count: {reinforce_count}"
    md = f"""---
name: {name}
description: {description[:200]}
type: {type_}
concept: {concept}
drift: {drift}
drift_signals: {signals_yaml}
agent_type: {agent_type}
user_id: {user_id}
ingested_via: mcp{thread_lines}{proof_lines}{dep_lines}{lifecycle_lines}
---

# {name}

## 上下文
{description}

## 内容
{body}
"""
    out_file.write_text(md, encoding="utf-8")
    suffix = f" · thread={thread_id}" if thread_id else ""
    proof_suffix = f" · proof_of_recall={proof_of_recall}"
    if proof_of_recall == "fail":
        proof_suffix += f" ({proof_reason})"
    return _ok(f"obs written · {out_file.name} · agent_type={agent_type} · drift={drift}{suffix}{proof_suffix}")


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


def tool_long_task(args: dict, emit=None, is_cancelled=None,
                   log=None) -> dict:
    """Demo tool for notifications/progress (Task #58) + logging (Task #59).

    Emits `steps` progress frames (default 3) · checks `is_cancelled()`
    between frames. Tool authors use this pattern: call
    `emit(progress, total, message)` at each milestone, and check
    `is_cancelled()` before committing irreversible work. Optional
    `log(level, data)` pushes `notifications/message` frames gated by
    the session's logging/setLevel threshold.
    """
    try:
        steps = max(1, min(int(args.get("steps", 3)), 20))
    except (TypeError, ValueError):
        steps = 3
    fired = 0
    cancelled = False
    if log:
        log("info", f"long_task starting · steps={steps}")
    for i in range(1, steps + 1):
        if is_cancelled and is_cancelled():
            cancelled = True
            if log:
                log("warning", f"long_task cancelled at step {i}/{steps}")
            break
        if emit:
            emit(progress=i, total=steps, message=f"step {i}/{steps}")
        if log:
            log("debug", f"long_task step {i}/{steps}")
        fired += 1
    status = "cancelled" if cancelled else "done"
    return _ok(f"long_task {status} · fired {fired}/{steps} progress frames")


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


def tool_submit_platform_task(args: dict) -> dict:
    """v1.0+ · BP1 · compass dialog → platform task channel.

    File-based queue stub. Writes a JSON spec to ~/.claude/projects/_platform_queue/.
    Platform V5 cycle (or future A2A POST /a2a/tasks/queue) consumes from this dir.
    Once platform endpoint goes live, set COMPASS_PLATFORM_QUEUE_URL to switch to HTTP.
    """
    name = (args.get("name") or "").strip()
    if not name:
        return _err("name required")
    channels = args.get("channels") or []
    payload = args.get("payload") or {}
    anchor_pack = (args.get("anchor_pack_hint") or "").strip()
    priority = (args.get("priority") or "normal").strip()
    if priority not in ("low", "normal", "high"):
        priority = "normal"

    PLATFORM_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    task_id = f"tk_{int(time.time()*1000)}"
    task_file = PLATFORM_QUEUE_DIR / f"{task_id}.json"
    spec = {
        "task_id": task_id,
        "name": name,
        "channels": channels,
        "anchor_pack_hint": anchor_pack,
        "priority": priority,
        "payload": payload,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "submitted_by": os.environ.get("COMPASS_DIALOG_ID", "compass-default"),
        "compass_session_id": os.environ.get("CLAUDE_SESSION_ID"),
        "callback_url": os.environ.get("COMPASS_CALLBACK_URL"),
        "status": "queued",
    }
    task_file.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    # If platform HTTP endpoint configured, also POST (best-effort, non-blocking on failure)
    queue_url = os.environ.get("COMPASS_PLATFORM_QUEUE_URL")
    http_status = "file-only (no COMPASS_PLATFORM_QUEUE_URL)"
    if queue_url:
        try:
            import urllib.request
            req = urllib.request.Request(
                queue_url,
                data=json.dumps(spec).encode("utf-8"),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {os.environ.get('COMPASS_PLATFORM_TOKEN','')}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                http_status = f"POSTed · {resp.status}"
        except Exception as e:
            http_status = f"POST failed (queued locally): {type(e).__name__}"

    return _ok(f"task queued · id={task_id} · channels={channels} · priority={priority} · {http_status}")


def tool_ingest_platform_task_result(args: dict) -> dict:
    """v1.0+ · BP3 · platform task done → ingest result back into compass memory.

    Platform agent (or callback handler) reports completion. We write
    (a) JSON archive to _platform_results/, (b) session_*.md for cross-session search.
    Closes the agent → platform → agent loop.
    """
    task_id = (args.get("task_id") or "").strip()
    if not task_id:
        return _err("task_id required")
    summary = (args.get("result_summary") or "").strip()[:1000]
    channels_published = args.get("channels_published") or []
    drift = (args.get("drift") or "green").strip()
    if drift not in ("green", "yellow", "red"):
        drift = "green"
    agent_id = (args.get("agent_id") or "platform-agent-unknown").strip()

    PLATFORM_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_file = PLATFORM_RESULTS_DIR / f"{task_id}_result.json"
    result_file.write_text(json.dumps({
        "task_id": task_id,
        "result_summary": summary,
        "channels_published": channels_published,
        "drift": drift,
        "agent_id": agent_id,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also ingest as session_*.md so session_search picks it up cross-project
    project = resolve_project(args.get("project")) or "C--Users-chunx"
    out_dir = PROJECTS_DIR / project / "memory"
    out_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    out_file = out_dir / f"session_{ts}_platform_{task_id[:24]}.md"

    if channels_published:
        channels_block = "\n".join(
            f"  - {c.get('channel','?')} · {c.get('status','?')} · {c.get('url','-')}"
            for c in channels_published
        )
    else:
        channels_block = "  (none)"

    md = f"""---
name: platform task {task_id} result
description: {summary[:200]}
type: feature
concept: what-changed
drift: {drift}
agent_type: platform-agent
ingested_via: mcp · ingest_platform_task_result
task_id: {task_id}
agent_id: {agent_id}
---

# Platform task {task_id} · result

## Summary
{summary}

## Channels published
{channels_block}

## Agent
{agent_id}
"""
    out_file.write_text(md, encoding="utf-8")
    return _ok(f"result ingested · task={task_id} · session={out_file.name} · drift={drift}")


# ─── V7 governance layer · v0.1 ────────────────────────────────────
#
# V7 is NOT a 4th executor — it sits ABOVE V5/V6/Kairos and routes complex
# tasks (dispatch), audits cross-agent state (audit), and verifies the
# immutable core layer hasn't drifted (lock_check). Per memory feedback
# `不替 agent 决策`: these tools propose plans and write files; platform
# agents and the v7-telegram daemon are responsible for actual minting /
# bounty creation. No self-LLM-chat: V7 reads filesystem state, not LLMs.

# Heuristic sub-task router · channel name → executor agent_id
_V7_CHANNEL_ROUTING = {
    "dev.to": "nautilus-v5",
    "x": "nautilus-v5",
    "x-zh": "nautilus-v5",
    "x-en": "nautilus-v5",
    "github": "nautilus-v6",
    "github-issue": "nautilus-v6",
    "code-review": "nautilus-v6",
    "knowledge-graph": "kairos",
    "kg": "kairos",
    "memory-audit": "kairos",
    "publish": "nautilus-v5",
    "marketing": "nautilus-v5",
}


def _v7_route_channel(channel: str) -> str:
    return _V7_CHANNEL_ROUTING.get(channel.lower().strip(), "nautilus-v5")


def tool_governance_dispatch(args: dict) -> dict:
    """v1.0+ · V7 governance · decompose a complex task into routed sub-tasks.

    V7 acts as senior engineer assigning juniors. Takes a complex task spec
    (multiple channels / multiple steps), decomposes into one sub-task per
    channel, picks an executor (V5/V6/Kairos) per sub-task using heuristic
    routing, and writes each sub-task as a queue file via the same BP1
    mechanism (so platform side picks it up unchanged). Returns the
    dispatch plan but does NOT directly mint platform_bounties — that
    stays platform-side per `不替 agent 决策`.

    Use when one logical task spans multiple channels / executors.
    """
    name = (args.get("name") or "").strip()
    if not name:
        return _err("name required")
    channels = args.get("channels") or []
    if not channels:
        return _err("channels required for dispatch (use submit_platform_task for single-channel)")
    payload = args.get("payload") or {}
    anchor_pack = (args.get("anchor_pack_hint") or "").strip()
    priority = (args.get("priority") or "normal").strip()
    if priority not in ("low", "normal", "high"):
        priority = "normal"

    PLATFORM_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    base_id = f"v7tk_{int(time.time()*1000)}"
    plan = []
    for idx, ch in enumerate(channels):
        executor = _v7_route_channel(ch)
        sub_task_id = f"{base_id}_{idx:02d}"
        sub_file = PLATFORM_QUEUE_DIR / f"{sub_task_id}.json"
        sub_spec = {
            "task_id": sub_task_id,
            "parent_task_id": base_id,
            "name": f"{name} · sub({ch})",
            "channels": [ch],
            "anchor_pack_hint": anchor_pack,
            "priority": priority,
            "payload": payload,
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "submitted_by": "v7-souls-fusion",
            "compass_session_id": os.environ.get("CLAUDE_SESSION_ID"),
            "callback_url": os.environ.get("COMPASS_CALLBACK_URL"),
            "status": "queued",
            "v7_dispatched": True,
            "v7_routed_executor": executor,
        }
        sub_file.write_text(json.dumps(sub_spec, ensure_ascii=False, indent=2), encoding="utf-8")
        plan.append({"sub_task_id": sub_task_id, "channel": ch, "routed_to": executor})

    plan_lines = "\n".join(
        f"  · {p['channel']:<20} → {p['routed_to']:<20} ({p['sub_task_id']})"
        for p in plan
    )
    return _ok(
        f"V7 dispatch · parent={base_id} · {len(plan)} sub-tasks queued\n{plan_lines}\n"
        f"platform-side: v7-monitor cron should mint bounties for files matching v7tk_*.json"
    )


def tool_governance_audit(args: dict) -> dict:
    """v1.0+ · V7 governance · cross-agent fake-closure audit.

    Scans recent session_*.md files for warning signs:
      · drift=red sessions in last N days
      · sessions tagged 'completed' but with empty/<50char body
      · platform task results without channels_published list
    Returns suspects · does NOT auto-correct (V7 governance, not execution).
    """
    days = int(args.get("days") or 7)
    project = resolve_project(args.get("project")) or "C--Users-chunx"
    mem_dir = PROJECTS_DIR / project / "memory"
    # Fresh install / CI runner won't have a memory dir · proceed with empty scan
    # so audit_id is still generated and the archive is still written (0 files,
    # 0 suspects). Callers and demos can trust the output shape unconditionally.

    cutoff = time.time() - days * 86400
    red_drift = []
    fake_closure = []
    empty_results = []
    scanned = 0

    for f in mem_dir.glob("*.md"):
        try:
            if f.stat().st_mtime < cutoff:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            scanned += 1
            head = text[:2000]
            # drift=red detection
            if "\ndrift: red" in head or "drift: red\n" in head:
                red_drift.append(f.name)
            # closed/completed but body too thin
            if any(m in head.lower() for m in ("status: completed", "status: closed", "status: done")):
                body = text.split("---", 2)[-1] if text.count("---") >= 2 else text
                if len(body.strip()) < 80:
                    fake_closure.append(f.name)
            # platform task result missing channels
            if "ingested_via: mcp · ingest_platform_task_result" in head:
                if "Channels published\n  (none)" in text:
                    empty_results.append(f.name)
        except Exception:
            continue

    GOVERNANCE_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    audit_id = f"audit_{int(time.time())}"
    audit_file = GOVERNANCE_AUDIT_DIR / f"{audit_id}.json"
    audit_file.write_text(json.dumps({
        "audit_id": audit_id,
        "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project": project,
        "days": days,
        "files_scanned": scanned,
        "red_drift": red_drift,
        "fake_closure": fake_closure,
        "empty_platform_results": empty_results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    suspects_total = len(red_drift) + len(fake_closure) + len(empty_results)
    return _ok(
        f"V7 audit · {audit_id} · scanned {scanned} files in last {days}d\n"
        f"  red_drift: {len(red_drift)}\n"
        f"  fake_closure: {len(fake_closure)}\n"
        f"  empty_platform_results: {len(empty_results)}\n"
        f"  total_suspects: {suspects_total}\n"
        f"archive: {audit_file}"
    )


def tool_governance_lock_check(args: dict) -> dict:
    """v1.0+ · V7 governance · L0/L1 hash lock verification.

    Reads governance.lock (committed in repo) which lists SHA256 hashes
    of L0 immutable core files. Recomputes current hashes and reports
    any drift. If governance.lock missing, lists candidate L0 files
    and writes the initial lock (one-time bootstrap).
    """
    import hashlib

    L0_FILES = [
        "recall.py",
        "merkle_chain.py",
        "anchors.json",
        "selftest.py",
    ]

    def sha256(p: Path) -> str:
        try:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:
            return "missing"

    bootstrap = bool(args.get("bootstrap"))
    current = {f: sha256(PLUGIN_DIR / f) for f in L0_FILES}

    if bootstrap or not GOVERNANCE_LOCK.exists():
        GOVERNANCE_LOCK.write_text(json.dumps({
            "version": "v0.1",
            "locked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "files": current,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        return _ok(
            f"V7 lock · bootstrapped at {GOVERNANCE_LOCK.name}\n" +
            "\n".join(f"  {f}: {h[:16]}..." for f, h in current.items())
        )

    locked = json.loads(GOVERNANCE_LOCK.read_text(encoding="utf-8"))
    expected = locked.get("files", {})
    drifted = [f for f, h in current.items() if expected.get(f) != h]
    if drifted:
        diff_lines = "\n".join(
            f"  {f}: locked={expected.get(f,'?')[:16]}... actual={current[f][:16]}..."
            for f in drifted
        )
        return _ok(
            f"V7 lock · DRIFT detected · {len(drifted)} L0 file(s) changed\n{diff_lines}\n"
            f"locked_at: {locked.get('locked_at')}\n"
            f"action: review change · re-bootstrap with bootstrap=true if intentional"
        )
    return _ok(
        f"V7 lock · OK · {len(current)} L0 files unchanged since {locked.get('locked_at')}"
    )


# ─── V7 governance v0.2 · capability-driven plan ──────────────────────
#
# v0.1 governance_dispatch was a fan-out router: input channels[], output
# one bounty per channel via static dict lookup. Doesn't decompose anything.
#
# v0.2 governance_plan reads two registries (live · with bundled defaults)
# and produces a DAG of routed sub-tasks:
#
#   1. platform_anchor_packs · domain → phases[]
#      (phases declare required_capability + depends_on → DAG shape)
#   2. platform_agents · agent_id → capabilities[]
#      (capabilities declare what each executor produces · which channels ·
#       which anchor packs they own)
#
# V7 matches phase.requires_capability against agents' declared capabilities,
# scores by domain affinity (capability.domains contains domain_hint) and
# anchor pack alignment, picks one executor per phase, emits one queue file
# per node with parent_task_id + depends_on for platform-side ordering.
#
# Adding a new vertical = add 1 row to platform_anchor_packs (live) or
# 1 entry to v7_default_phases.json (bundled). V7 source code unchanged.


def _v7_load_registry(live_path: Path, default_path: Path) -> dict:
    """Prefer live platform-exported registry · fall back to bundled defaults.

    Live takes precedence so platform can override per-deployment without
    recompiling V7. Defaults ship with the package so V7 works standalone
    (CI, local dev) before any platform integration.
    """
    if live_path.exists():
        try:
            return json.loads(live_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    if default_path.exists():
        try:
            return json.loads(default_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _v7_score_executor(agent: dict, capability_id: str,
                        domain_hint: str, anchor_pack: str) -> int:
    """Score how well an agent matches a phase. Higher = better match.

    +10  capability id matches
    +5   capability lists domain_hint in its domains[] (or domains is empty/missing → wildcard)
    +3   capability lists the requested anchor_pack
    +1   tie-breaker fallback so any match scores above 0
    """
    score = 0
    for cap in agent.get("capabilities", []) or []:
        if cap.get("id") != capability_id:
            continue
        score = max(score, 1)
        score += 10
        cap_domains = cap.get("domains")
        if cap_domains is None or not cap_domains:
            score += 1   # wildcard executor · OK but lower than domain-matched
        elif domain_hint and any(domain_hint in d for d in cap_domains):
            score += 5
        cap_packs = cap.get("anchor_packs") or []
        if anchor_pack and anchor_pack in cap_packs:
            score += 3
    return score


def tool_governance_plan(args: dict) -> dict:
    """v1.0+ · V7 v0.2 · capability-driven complex-task plan.

    Reads platform_anchor_packs phase registry + platform_agents capability
    registry · produces a DAG of (phase_id, executor, depends_on) nodes ·
    optionally writes one queue file per node so v7-monitor can mint bounties.
    No templates · no LLM-chat · pure registry queries.

    Use over governance_dispatch when one logical goal needs multiple
    executors in sequence (research → write → publish → measure rather
    than fan-out across channels).
    """
    goal = (args.get("goal") or "").strip()
    if not goal:
        return _err("goal required (high-level task description)")
    domain_hint = (args.get("domain_hint") or "").strip()
    anchor_pack = (args.get("anchor_pack_hint") or "").strip()
    payload = args.get("payload") or {}
    priority = (args.get("priority") or "normal").strip()
    dry_run = bool(args.get("dry_run"))
    if priority not in ("low", "normal", "high"):
        priority = "normal"

    # Load registries (live > bundled default)
    caps = _v7_load_registry(
        PLATFORM_REGISTRY_DIR / "agents_capabilities.json",
        V7_DEFAULT_CAPABILITIES,
    )
    phases_reg = _v7_load_registry(
        PLATFORM_REGISTRY_DIR / "anchor_packs_phases.json",
        V7_DEFAULT_PHASES,
    )
    if not caps.get("agents") or not phases_reg.get("domains"):
        return _err("registries missing or empty · check examples/v7_default_*.json")

    # Resolve phases for domain (specific match → fuzzy contains → _default)
    domains = phases_reg["domains"]
    phases: list = []
    matched_domain = "_default"
    if domain_hint and domain_hint in domains:
        phases = domains[domain_hint].get("phases", [])
        matched_domain = domain_hint
    elif domain_hint:
        # fuzzy: pick first domain that contains the hint as substring
        for k, v in domains.items():
            if k != "_default" and (domain_hint in k or k in domain_hint):
                phases = v.get("phases", [])
                matched_domain = k
                break
    if not phases:
        phases = domains.get("_default", {}).get("phases", [])
        matched_domain = "_default"
    if not phases:
        return _err(f"no phases defined for domain={domain_hint!r} (no _default fallback)")

    # Plan DAG: phase → best-scoring executor
    PLATFORM_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    base_id = f"v7plan_{int(time.time()*1000)}"
    plan_nodes: list[dict] = []
    unresolved: list[str] = []

    for phase in phases:
        cap_id = phase.get("requires_capability", "")
        if not cap_id:
            continue
        ranked = []
        for agent in caps.get("agents", []):
            sc = _v7_score_executor(agent, cap_id, domain_hint, anchor_pack)
            if sc > 0:
                ranked.append((sc, agent.get("agent_id", "?")))
        if not ranked:
            unresolved.append(f"{phase['id']}(needs {cap_id})")
            continue
        ranked.sort(reverse=True)
        executor = ranked[0][1]
        node = {
            "phase_id": phase["id"],
            "requires_capability": cap_id,
            "executor": executor,
            "depends_on": phase.get("depends_on", []),
            "description": phase.get("description", ""),
            "score": ranked[0][0],
        }
        plan_nodes.append(node)

    if unresolved:
        return _err(
            f"V7 plan · cannot resolve {len(unresolved)} phase(s) · "
            f"no executor declares required capability:\n"
            f"  · " + "\n  · ".join(unresolved) + "\n"
            f"action: register the capability in platform_agents or "
            f"_platform_registry/agents_capabilities.json"
        )

    # Write queue files (one per node) unless dry_run
    written: list[str] = []
    if not dry_run:
        for idx, node in enumerate(plan_nodes):
            sub_id = f"{base_id}_{idx:02d}"
            spec = {
                "task_id": sub_id,
                "parent_task_id": base_id,
                "name": f"{goal} · {node['phase_id']}",
                "phase_id": node["phase_id"],
                "depends_on_phase_ids": node["depends_on"],
                "requires_capability": node["requires_capability"],
                "v7_routed_executor": node["executor"],
                "v7_dispatched": True,
                "v7_plan_version": "v0.2",
                "anchor_pack_hint": anchor_pack,
                "domain_hint": domain_hint,
                "matched_domain": matched_domain,
                "priority": priority,
                "payload": payload,
                "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "submitted_by": "v7-souls-fusion",
                "compass_session_id": os.environ.get("CLAUDE_SESSION_ID"),
                "callback_url": os.environ.get("COMPASS_CALLBACK_URL"),
                "status": "queued",
            }
            f = PLATFORM_QUEUE_DIR / f"{sub_id}.json"
            f.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
            written.append(sub_id)

    plan_lines = "\n".join(
        f"  · {n['phase_id']:<25} → {n['executor']:<20} "
        f"(needs={n['requires_capability']} · score={n['score']} "
        f"· depends_on={n['depends_on'] or 'none'})"
        for n in plan_nodes
    )
    src_caps = "live" if (PLATFORM_REGISTRY_DIR / "agents_capabilities.json").exists() else "bundled-default"
    src_phases = "live" if (PLATFORM_REGISTRY_DIR / "anchor_packs_phases.json").exists() else "bundled-default"
    msg = (
        f"V7 plan · parent={base_id} · domain={matched_domain} · "
        f"{len(plan_nodes)} phases · "
        f"caps={src_caps} · phases={src_phases}\n{plan_lines}\n"
        f"{'DRY RUN · 0 queue files written' if dry_run else f'{len(written)} sub-task file(s) written to _platform_queue/'}"
    )
    return _ok(msg)


def tool_add_worker(args: dict) -> dict:
    """v1.7.1 · Phase 2.B · agentmemory iii worker plug paradigm.

    Narrow scope · register a deterministic worker spec for super-agent
    self-evolving runtime. No code execution · just spec persisted to
    .cache/workers.jsonl for inspection by upstream runtime (V5 / V7).

    Use case · super-agent declares "I want a `iii-cron-daily` worker that
    fires at 09:00 daily" · this tool records the spec deterministically.

    Reference · agentmemory README (rohitg00 · 15.3K stars) iii worker add
    paradigm verbatim · paper/LLM_WIKI2_FUSE_DESIGN.md §3 for schema fit.
    """
    import json as _json
    from datetime import datetime, timezone

    name = (args.get("name") or "").strip()
    if not name:
        return _err("name required")
    spec_type = (args.get("spec_type") or "custom").strip()
    if spec_type not in ("cron", "pubsub", "queue", "http", "custom"):
        spec_type = "custom"
    description = (args.get("description") or "").strip()
    config = args.get("config") or {}
    if not isinstance(config, dict):
        config = {}
    agent_type = (args.get("agent_type")
                  or os.environ.get("COMPASS_AGENT_TYPE")
                  or "custom").strip()

    ts = datetime.now(timezone.utc).isoformat()
    record = {
        "name": name,
        "spec_type": spec_type,
        "description": description[:200],
        "config": config,
        "registered_at": ts,
        "agent_type": agent_type,
        "registered_by": "compass_mcp",
    }

    cache_dir = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    workers_file = cache_dir / "workers.jsonl"
    with workers_file.open("a", encoding="utf-8") as f:
        f.write(_json.dumps(record, ensure_ascii=False) + "\n")

    return _ok(f"Worker '{name}' (type={spec_type}) registered · {workers_file.name}")


def tool_proof_of_impact(args: dict) -> dict:
    """v1.7.1 · S4 · Proof-of-Impact MCP tool · trace agent action to cited memory.

    Records PoI event via proof/poi_emitter.emit_full · which:
      1. Writes NAU records to .cache/poi_emit.jsonl (suppressing self-cite)
      2. Appends full event to .cache/poi_events.jsonl audit log
      3. Updates cited memory frontmatter (cumulative_impact / event_count / last_at)

    Caller computes impact_score via proof.poi_calculator beforehand or passes
    explicit value. drift_penalty applied via memory frontmatter scan.

    Reference: paper/SPEC_PROOF_OF_IMPACT.md sections 3-5.
    """
    try:
        from proof.poi_schema import ProofOfImpact
        from proof.poi_calculator import compute_with_drift
        from proof.poi_emitter import emit_full
    except ImportError as e:
        return _err(f"proof subpackage not importable: {e}")

    action_id = (args.get("action_id") or "").strip()
    if not action_id:
        return _err("action_id required")
    agent_id = (args.get("agent_id") or "").strip()
    if not agent_id:
        return _err("agent_id required")
    cited = args.get("cited_memory_paths") or []
    if not isinstance(cited, list) or not cited:
        return _err("cited_memory_paths (list) required · cannot be empty")
    outcome = (args.get("action_outcome") or "pending").strip()
    if outcome not in ("success", "failure", "partial", "pending"):
        return _err(f"action_outcome must be one of success/failure/partial/pending · got {outcome!r}")
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    timestamp_action = (args.get("timestamp_action") or now_iso).strip()
    timestamp_outcome = (args.get("timestamp_outcome") or now_iso).strip()

    try:
        poi = ProofOfImpact(
            action_id=action_id,
            agent_id=agent_id,
            cited_memory_paths=cited,
            action_outcome=outcome,
            timestamp_action=timestamp_action,
            timestamp_outcome=timestamp_outcome,
            declaration_type=(args.get("declaration_type") or "supports").strip(),
            notes=(args.get("notes") or "").strip(),
        )
    except ValueError as e:
        return _err(f"PoI validation: {e}")

    score = compute_with_drift(poi)
    result = emit_full(poi)
    return _ok(
        f"PoI recorded · action={action_id} · score={score} · "
        f"nau_records={result['nau_records']} · frontmatter_updated={result['frontmatter_updated']}"
    )


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
                    "thread_id": {"type": "string", "description": "v1.1 · Optional thread identifier for multi-turn conversations (e.g. 'thread_devto_azender1_safeagent'). Enables thread_recall."},
                    "thread_role": {"type": "string", "enum": ["outbound","inbound","self_note"], "description": "v1.1 · Role of this message in the thread. Required if thread_id is set."},
                    "recall_token": {"type": "string", "description": "v1.5 · proof-of-recall · token from a prior recall call (30 min TTL). Pair with cited_snippets to prove you actually consumed the recall hits. Omit if no recall preceded this ingest."},
                    "cited_snippets": {"type": "array", "items": {"type": "string"}, "default": [], "description": "v1.5 · proof-of-recall · list of snippet quotes (file basenames or description fragments ≥20 chars). At least one must overlap a top-3 entry from the recall_token. Failure marks proof_of_recall=fail in frontmatter (still writes · advisory)."},
                    "depends_on": {"type": "array", "items": {"type": "string"}, "default": [], "description": "v1.7 · MEME-extension · 0-5 file basenames of session_*.md this entry causally depends on. Empty list if standalone. Powers cascade-closure recall via transitive BFS (depth ≤ 3) when COMPASS_CHAIN_RECALL=1."},
                    "declaration_type": {"type": "string", "enum": ["cascade", "absence", "deletion", "none"], "default": "none", "description": "v1.7 · MEME-extension · cascade=needs ancestors to interpret / absence=asserts X did NOT happen (MEME Abs) / deletion=supersedes earlier obs (MEME Del) / none=standalone."},
                    "supersedes": {"type": "array", "items": {"type": "string"}, "default": [], "description": "v1.7 · MEME-extension · only meaningful when declaration_type=deletion · file basenames being retracted. Recall down-weights superseded entries."},
                    "tier": {"type": "string", "enum": ["working", "episodic", "semantic", "procedural"], "default": "working", "description": "v1.7.1 · lifecycle (llm-wiki2 fuse) · llm-wiki2 4-tier names verbatim. Default working."},
                    "decay_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.5, "description": "v1.7.1 · lifecycle · Ebbinghaus exponential decay rate (0.0-1.0). Resets on access event."},
                    "forget_at": {"type": "string", "description": "v1.7.1 · lifecycle · ISO8601 timestamp · soft-archive when reached. Null/omit = never forget."},
                    "promote_after": {"type": "string", "description": "v1.7.1 · lifecycle · '<N>d' duration OR '<N>_access' count for tier promotion. Default by tier (working=1_access · episodic=5_access · semantic=20_access · procedural=null)."},
                    "reinforce_count": {"type": "integer", "minimum": 0, "default": 0, "description": "v1.7.1 · lifecycle · access event 累计. Each recall hit increments. Resets decay timer."},
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
    "thread_recall": {
        "fn": tool_thread_recall,
        "schema": {
            "name": "thread_recall",
            "description": "v1.1 · L3 dogfood · Multi-turn thread recall by thread_id frontmatter tag. Returns the chronological message stream for a long-running back-and-forth (e.g. agent ↔ commenter / founder partnership negotiation, multi-day support thread). Whereas `recall` does semantic top-k across all memory, `thread_recall` returns the full ordered sequence for one thread_id. Pair with `ingest_obs(thread_id=..., thread_role='outbound'|'inbound'|'self_note')` to populate the thread. Compass keeps raw bodies — white-box memory loses the thread when it abstracts into facts.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "Unique thread identifier (e.g. 'thread_devto_azender1_safeagent')"},
                    "project": {"type": "string", "description": "Project memory dir name. Defaults to most-recently-modified."},
                    "since": {"type": "string", "description": "Optional ISO 8601 timestamp · only return messages after this time"},
                    "limit": {"type": "integer", "default": 50, "description": "Max number of messages to return (default 50)"},
                    "include_body": {"type": "boolean", "default": True, "description": "Whether to include the raw message body (first 2000 chars). False = headers-only summary."},
                },
                "required": ["thread_id"],
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
    "long_task": {
        "fn": tool_long_task,
        "progress": True,  # emit/is_cancelled injected when _meta.progressToken set
        "schema": {
            "name": "long_task",
            "description": "v1.0 · Demo tool for notifications/progress + cancelled. Emits N progress frames · checks cancellation between frames. Use as a smoke tool for MCP clients that want to exercise the progress/cancel wire.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "steps": {"type": "integer", "default": 3, "description": "1-20 · how many progress frames to emit"},
                },
            },
        },
    },
    "submit_platform_task": {
        "fn": tool_submit_platform_task,
        "schema": {
            "name": "submit_platform_task",
            "description": "v1.0+ · BP1 · Queue a task for the Nautilus platform (V5 cycle / platform_agents). File-based by default; HTTP POST when COMPASS_PLATFORM_QUEUE_URL is set. Use this to hand work from a compass dialog to the platform: publishing, code review, content generation, anything platform agents can specialize in. Pair with ingest_platform_task_result for the return leg.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Short task name · 8-40 chars"},
                    "channels": {"type": "array", "items": {"type": "string"}, "default": [], "description": "Target channels · e.g. ['dev.to','x','github']. Empty = let platform router decide."},
                    "payload": {"type": "object", "description": "Task-specific payload · platform reads this · keep it JSON-serialisable"},
                    "anchor_pack_hint": {"type": "string", "description": "Domain anchor pack hint · e.g. 'marketing/dev-tools' · platform uses this to score quality"},
                    "priority": {"type": "string", "enum": ["low","normal","high"], "default": "normal"},
                },
                "required": ["name"],
            },
        },
    },
    "ingest_platform_task_result": {
        "fn": tool_ingest_platform_task_result,
        "schema": {
            "name": "ingest_platform_task_result",
            "description": "v1.0+ · BP3 · Platform agent reports a completed task back to compass. Writes a JSON archive AND a session_*.md so the result becomes searchable cross-session. Closes the loop submit_platform_task → V5 cycle → ingest_platform_task_result. Typically called by the platform callback handler, not directly by users.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task id returned by submit_platform_task"},
                    "result_summary": {"type": "string", "description": "≤1000 char summary of what was done"},
                    "channels_published": {"type": "array", "items": {"type": "object"}, "default": [], "description": "List of {channel, url, status} dicts"},
                    "drift": {"type": "string", "enum": ["green","yellow","red"], "default": "green", "description": "Platform agent self-audit · same semantics as ingest_obs"},
                    "agent_id": {"type": "string", "description": "platform_agents.agent_id of who completed"},
                    "project": {"type": "string", "description": "Target project (defaults to most-recent)"},
                },
                "required": ["task_id"],
            },
        },
    },
    "governance_dispatch": {
        "fn": tool_governance_dispatch,
        "schema": {
            "name": "governance_dispatch",
            "description": "v1.0+ · V7 governance · Decompose a complex multi-channel task into routed sub-tasks. V7 sits ABOVE V5/V6/Kairos and assigns each channel to the right executor (V5 for marketing/publish, V6 for code-review/github, Kairos for kg/memory-audit). Writes one queue file per sub-task; platform v7-monitor cron mints bounties. V7 does not execute itself — pure governance/routing.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Top-level task name · 8-40 chars"},
                    "channels": {"type": "array", "items": {"type": "string"}, "description": "Required · channels to dispatch to · each becomes one sub-task"},
                    "payload": {"type": "object", "description": "Shared payload all sub-tasks see"},
                    "anchor_pack_hint": {"type": "string", "description": "Domain anchor pack hint"},
                    "priority": {"type": "string", "enum": ["low","normal","high"], "default": "normal"},
                },
                "required": ["name", "channels"],
            },
        },
    },
    "governance_audit": {
        "fn": tool_governance_audit,
        "schema": {
            "name": "governance_audit",
            "description": "v1.0+ · V7 governance · Cross-agent fake-closure audit. Scans recent session_*.md for: drift=red, status=completed with empty body, platform task results without published channels. Returns suspects but does not auto-correct. Run weekly or on-demand before releases.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 7, "description": "Window in days"},
                    "project": {"type": "string", "description": "Target project (defaults to most-recent)"},
                },
            },
        },
    },
    "governance_lock_check": {
        "fn": tool_governance_lock_check,
        "schema": {
            "name": "governance_lock_check",
            "description": "v1.0+ · V7 governance · L0/L1 hash lock verification. Compares SHA256 of L0 immutable core files (compass.py, anchors_*.json, selftest.py) against governance.lock. If lock missing or bootstrap=true, writes a fresh lock. Detects tampering of core layer.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bootstrap": {"type": "boolean", "default": False, "description": "Force re-bootstrap of lock file (use after intentional L0 change)"},
                },
            },
        },
    },
    "governance_plan": {
        "fn": tool_governance_plan,
        "schema": {
            "name": "governance_plan",
            "description": "v1.0+ · V7 v0.2 · Capability-driven complex-task plan. Reads platform_anchor_packs phase registry + platform_agents capability registry · produces a DAG of (phase_id, executor, depends_on) routed sub-tasks · emits one queue file per node with depends_on so v7-monitor can mint bounties in the right order. No templates · no LLM-chat · pure registry queries. Adding a new vertical = 1 row in registry, no V7 code change. Use over governance_dispatch when one logical goal needs sequential phases (research → write → publish → measure) rather than fan-out to channels.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "High-level task description · 8-200 chars"},
                    "domain_hint": {"type": "string", "description": "Domain key matching platform_anchor_packs · e.g. 'marketing/dev-tools' · 'caishen-finance/audit' · falls back to _default phases if unmatched"},
                    "anchor_pack_hint": {"type": "string", "description": "Quality anchor pack identifier · used to score executor match"},
                    "payload": {"type": "object", "description": "Shared payload visible to all phase sub-tasks"},
                    "priority": {"type": "string", "enum": ["low","normal","high"], "default": "normal"},
                    "dry_run": {"type": "boolean", "default": False, "description": "Compute the plan and return it without writing queue files · for inspection"},
                },
                "required": ["goal"],
            },
        },
    },
    "proof_of_impact": {
        "fn": tool_proof_of_impact,
        "schema": {
            "name": "proof_of_impact",
            "description": "v1.7.1 · S4 · Proof-of-Impact · trace agent action to cited memory · deterministic impact score (LLM-free formula) · emits NAU records to .cache/poi_emit.jsonl + full event log + frontmatter cumulative_impact update. Suppresses self-cite by default. action_outcome enum: success/failure/partial/pending. See paper/SPEC_PROOF_OF_IMPACT.md.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action_id": {"type": "string", "description": "External action ID (V5 bounty_id, V7 task_id, etc.)"},
                    "agent_id": {"type": "string", "description": "Acting agent identifier"},
                    "cited_memory_paths": {"type": "array", "items": {"type": "string"}, "description": "Memory paths cited during action (from prior recall_token + cited_snippets)"},
                    "action_outcome": {"type": "string", "enum": ["success", "failure", "partial", "pending"], "default": "pending"},
                    "timestamp_action": {"type": "string", "description": "ISO8601 when action started (defaults to now)"},
                    "timestamp_outcome": {"type": "string", "description": "ISO8601 when outcome observed (defaults to now)"},
                    "declaration_type": {"type": "string", "enum": ["supports", "contradicts", "neutral"], "default": "supports"},
                    "notes": {"type": "string", "description": "≤200 char optional narrative"},
                },
                "required": ["action_id", "agent_id", "cited_memory_paths"],
            },
        },
    },
    "add_worker": {
        "fn": tool_add_worker,
        "schema": {
            "name": "add_worker",
            "description": "v1.7.1 · Phase 2.B · agentmemory iii worker plug paradigm · register deterministic worker spec for super-agent self-evolving runtime. Records to .cache/workers.jsonl · no code execution · narrow scope (cron/pubsub/queue/http/custom). Super-agent declares 'I want a iii-cron-daily worker' and this tool persists the spec.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Worker name · unique identifier"},
                    "spec_type": {"type": "string", "enum": ["cron", "pubsub", "queue", "http", "custom"], "default": "custom", "description": "Worker primitive type (agentmemory iii-* family)"},
                    "description": {"type": "string", "description": "≤200 char what this worker does"},
                    "config": {"type": "object", "description": "Free-form config dict (cron schedule, topic, queue name, http endpoint, etc.)"},
                    "agent_type": {"type": "string", "description": "Registering agent type · defaults to env COMPASS_AGENT_TYPE"},
                },
                "required": ["name"],
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

# Operator metrics · updated by the TCP loop · read by server/status.
# Counters are ints with the GIL so increments are atomic enough for
# per-message bookkeeping; `_metrics_lock` only guards the connection
# set, which is a composite update.
import threading as _threading

_SERVER_STARTED_AT = time.time()
_metrics_lock = _threading.Lock()
_metrics = {
    "active_connections": 0,
    "total_connections": 0,
    "auth_failures": 0,
    "messages_handled": 0,
}


def _metrics_inc(key: str, delta: int = 1) -> None:
    with _metrics_lock:
        _metrics[key] = _metrics.get(key, 0) + delta


def _metrics_snapshot() -> dict:
    with _metrics_lock:
        snap = dict(_metrics)
    snap["uptime_seconds"] = round(time.time() - _SERVER_STARTED_AT, 3)
    snap["server"] = {"name": SERVER_NAME, "version": SERVER_VERSION}
    return snap


# ─── MCP resources/* (Task #48) ────────────────────────────────────
# Expose recent session_*.md files as MCP Resources so peer agents can
# read them over the protocol (not just via recall's snippet). URIs look
# like `compass://session/<project>/<filename>`. We restrict reads to
# files inside ~/.claude/projects/*/memory with a session_*.md name · no
# arbitrary filesystem access.

RESOURCE_SCHEME = "compass"
PROJECTS_ROOT = Path.home() / ".claude" / "projects"
RESOURCE_LIST_LIMIT = 50
RESOURCE_MAX_BYTES = 256 * 1024  # 256 KiB · session logs rarely exceed this


def _list_session_resources(limit: int = RESOURCE_LIST_LIMIT) -> list[dict]:
    if not PROJECTS_ROOT.exists():
        return []
    entries: list[tuple[float, Path, str]] = []
    for proj_dir in PROJECTS_ROOT.iterdir():
        mem = proj_dir / "memory"
        if not mem.is_dir():
            continue
        for p in mem.glob("session_*.md"):
            try:
                entries.append((p.stat().st_mtime, p, proj_dir.name))
            except OSError:
                continue
    entries.sort(key=lambda t: t[0], reverse=True)
    out: list[dict] = []
    for mtime, path, project in entries[:limit]:
        out.append({
            "uri": f"{RESOURCE_SCHEME}://session/{project}/{path.name}",
            "name": path.stem,
            "mimeType": "text/markdown",
            "description": f"session log · project={project} · mtime={int(mtime)}",
        })
    return out


def _resolve_session_uri(uri: str) -> Path:
    """Parse and validate a compass:// URI to a real Path · reject traversal."""
    if not isinstance(uri, str) or not uri.startswith(f"{RESOURCE_SCHEME}://session/"):
        raise ValueError(f"unsupported uri scheme: {uri!r}")
    rest = uri[len(f"{RESOURCE_SCHEME}://session/"):]
    parts = rest.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"uri must be {RESOURCE_SCHEME}://session/<project>/<file>")
    project, name = parts
    # Reject anything that isn't a plain session_*.md filename · blocks
    # path traversal and arbitrary file access even if someone slips a
    # URL-encoded "/" in.
    if "/" in name or "\\" in name or ".." in name or ".." in project:
        raise ValueError("path traversal rejected")
    if not name.startswith("session_") or not name.endswith(".md"):
        raise ValueError("only session_*.md files are exposed as resources")
    proj_dir = (PROJECTS_ROOT / project).resolve()
    # Double-check proj_dir is still under PROJECTS_ROOT after resolve.
    try:
        proj_dir.relative_to(PROJECTS_ROOT.resolve())
    except ValueError:
        raise ValueError("project escapes projects root")
    target = (proj_dir / "memory" / name).resolve()
    target.relative_to(proj_dir)  # must be inside the project
    if not target.is_file():
        raise FileNotFoundError(f"no such resource: {uri}")
    return target


def _read_session_resource(uri: str) -> dict:
    path = _resolve_session_uri(uri)
    data = path.read_bytes()
    if len(data) > RESOURCE_MAX_BYTES:
        data = data[:RESOURCE_MAX_BYTES]
        truncated = True
    else:
        truncated = False
    text = data.decode("utf-8", errors="replace")
    content = {"uri": uri, "mimeType": "text/markdown", "text": text}
    if truncated:
        content["text"] += f"\n\n<!-- truncated at {RESOURCE_MAX_BYTES} bytes -->\n"
    return {"contents": [content]}


# ─── token-scoped RBAC (Task #49) ──────────────────────────────────
# A token maps to a set of scopes. Scopes gate tool/resource calls:
#   tools.read      · recall, drift_history, session_search, profile, drift_check
#   tools.write     · ingest_obs, feedback_log
#   resources.read  · resources/list + resources/read
#   *               · everything (legacy / dev)
# Unauthenticated TCP (no --token) and stdio grant "*" — localhost trust.

TOOL_SCOPE_MAP = {
    "recall": "tools.read",
    "thread_recall": "tools.read",
    "drift_history": "tools.read",
    "session_search": "tools.read",
    "profile": "tools.read",
    "drift_check": "tools.read",
    "long_task": "tools.read",
    "ingest_obs": "tools.write",
    "feedback_log": "tools.write",
}

ALL_SCOPES = {"*", "tools.read", "tools.write", "resources.read"}


def _parse_token_spec(spec: str) -> tuple[str, set[str]]:
    """`foo` → (foo, {*}). `foo:a,b` → (foo, {a, b})."""
    if ":" in spec:
        token, rest = spec.split(":", 1)
        scopes = {s.strip() for s in rest.split(",") if s.strip()}
    else:
        token, scopes = spec, {"*"}
    token = token.strip()
    if not token:
        raise ValueError("empty token in spec")
    bad = scopes - ALL_SCOPES
    if bad:
        raise ValueError(f"unknown scopes {sorted(bad)} · known={sorted(ALL_SCOPES)}")
    return token, scopes


def _load_token_table(specs: list[str] | None, token_file: str | None) -> dict[str, set[str]]:
    """Merge --token cli specs and --token-file JSON into {token: scopes}.

    Side effect: registers any `rate_limit: {rps, burst}` entries from the
    token file into the module-level `_RATE_BUCKETS` map. CLI `--rate-limit`
    flags are handled separately in main() after the table is built.
    """
    table: dict[str, set[str]] = {}
    if specs:
        for s in specs:
            t, sc = _parse_token_spec(s)
            table[t] = sc
    if token_file:
        with open(token_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("token file must be a JSON object {token: [scopes]} "
                             "or {token: {scopes: [...], rate_limit: {rps, burst}}}")
        for t, v in data.items():
            if isinstance(v, list):
                scopes = set(v)
                rl = None
            elif isinstance(v, dict):
                scopes = set(v.get("scopes") or ["*"])
                rl = v.get("rate_limit")
            else:
                scopes = {"*"}
                rl = None
            bad = scopes - ALL_SCOPES
            if bad:
                raise ValueError(f"token {t!r}: unknown scopes {sorted(bad)}")
            table[t] = scopes
            if rl:
                try:
                    rps = float(rl["rps"])
                    burst = float(rl.get("burst", rl["rps"]))
                except (KeyError, TypeError, ValueError) as e:
                    raise ValueError(f"token {t!r}: bad rate_limit {rl!r}: {e}")
                _rate_register(t, rps, burst)
    return table


def _has_scope(scopes: set[str] | None, required: str) -> bool:
    if scopes is None:
        return True  # stdio / no-auth mode
    return "*" in scopes or required in scopes


# ─── per-token rate limit (Task #51) ───────────────────────────────
# Classic token-bucket · refills at `rps` tokens/sec · caps at `burst`.
# `acquire()` returns (ok, retry_after_seconds). Thread-safe by fine-grained
# lock per bucket — contention is only on the rate-limited client, so
# per-token locking keeps well-behaved peers lock-free.

class RateBucket:
    __slots__ = ("rps", "burst", "_tokens", "_last", "_lock")

    def __init__(self, rps: float, burst: float) -> None:
        if rps <= 0 or burst <= 0:
            raise ValueError("rps and burst must be positive")
        self.rps = float(rps)
        self.burst = float(burst)
        self._tokens = float(burst)
        self._last = time.monotonic()
        self._lock = _threading.Lock()

    def acquire(self, cost: float = 1.0, *, now: float | None = None) -> tuple[bool, float]:
        with self._lock:
            t = now if now is not None else time.monotonic()
            # Refill.
            delta = max(0.0, t - self._last)
            self._tokens = min(self.burst, self._tokens + delta * self.rps)
            self._last = t
            if self._tokens >= cost:
                self._tokens -= cost
                return True, 0.0
            # Report when the bucket will have one whole token again.
            need = cost - self._tokens
            return False, need / self.rps

    def snapshot(self) -> dict:
        with self._lock:
            return {"rps": self.rps, "burst": self.burst,
                    "tokens": round(self._tokens, 3)}


# Gate map · methods not listed here are unlimited (ping, status, initialize,
# notifications/*, tools/list are protocol chatter · cheap and safe).
RATE_LIMITED_METHODS = {"tools/call", "resources/list", "resources/read"}

# Populated by _load_token_table / _rate_flag parsing · token → RateBucket.
# None scopes (dev mode / stdio) bypass lookup entirely.
_RATE_BUCKETS: dict[str, RateBucket] = {}
_RATE_BUCKETS_LOCK = _threading.Lock()

# ─── notifications/cancelled bookkeeping (Task #58) ──────────────
# Notify-only semantics: any `tools/call` whose requestId shows up here
# is considered cancelled by the client. The current sync dispatch can't
# abort an in-flight tool, but tools that emit progress frames can check
# _is_cancelled() between frames to bail early. The set auto-reaps on
# reply completion to keep memory bounded.
_CANCELLED_REQUEST_IDS: set = set()
_CANCELLED_LOCK = _threading.Lock()


def _mark_cancelled(request_id) -> None:
    with _CANCELLED_LOCK:
        _CANCELLED_REQUEST_IDS.add(request_id)


def _is_cancelled(request_id) -> bool:
    with _CANCELLED_LOCK:
        return request_id in _CANCELLED_REQUEST_IDS


def _clear_cancelled(request_id) -> None:
    """Drop a requestId from the cancelled set · called after reply sent."""
    with _CANCELLED_LOCK:
        _CANCELLED_REQUEST_IDS.discard(request_id)


# ─── MCP logging (spec 2024-11-05) ────────────────────────────────
#
# `logging/setLevel` is a client-issued request that chooses the minimum
# severity the server should push back via `notifications/message`. The
# level is per-session: each transport owner holds a small dict and
# threads it through handle_message. We use Python's logging levels as
# a superset of the MCP enum (debug/info/notice/warning/error/critical/
# alert/emergency) · anything below the requested level is dropped.

LOG_LEVELS = {
    "debug": 10, "info": 20, "notice": 25, "warning": 30,
    "error": 40, "critical": 50, "alert": 60, "emergency": 70,
}
DEFAULT_LOG_LEVEL = "info"


def _normalize_log_level(level: str) -> str | None:
    if not isinstance(level, str):
        return None
    level = level.lower()
    return level if level in LOG_LEVELS else None


def _should_emit_log(session_level: str, record_level: str) -> bool:
    """True if a record at record_level passes the session's threshold."""
    threshold = LOG_LEVELS.get(session_level, LOG_LEVELS[DEFAULT_LOG_LEVEL])
    incoming = LOG_LEVELS.get(record_level, LOG_LEVELS[DEFAULT_LOG_LEVEL])
    return incoming >= threshold


def emit_log(emit_notification, session_level: str, level: str,
             data, logger: str | None = None) -> bool:
    """Push a notifications/message frame if level passes the session gate.

    Returns True if a frame was dispatched, False if filtered or if no
    emitter is wired (stdio loop for example). Kept tolerant · a missing
    emitter must never raise from inside a tool.
    """
    if emit_notification is None:
        return False
    level = _normalize_log_level(level) or DEFAULT_LOG_LEVEL
    if not _should_emit_log(session_level or DEFAULT_LOG_LEVEL, level):
        return False
    frame = {
        "jsonrpc": "2.0",
        "method": "notifications/message",
        "params": {"level": level, "data": data},
    }
    if logger:
        frame["params"]["logger"] = logger
    try:
        emit_notification(frame)
    except Exception:
        return False
    return True


def _rate_bucket_for(token: str | None) -> RateBucket | None:
    if token is None:
        return None
    with _RATE_BUCKETS_LOCK:
        return _RATE_BUCKETS.get(token)


def _rate_register(token: str, rps: float, burst: float) -> None:
    with _RATE_BUCKETS_LOCK:
        _RATE_BUCKETS[token] = RateBucket(rps, burst)


def _rate_clear() -> None:
    """Test helper · wipe all registered buckets."""
    with _RATE_BUCKETS_LOCK:
        _RATE_BUCKETS.clear()


def _parse_rate_flag(spec: str) -> tuple[str, float, float]:
    """`TOKEN=rps/burst` → (token, rps, burst). Used by --rate-limit."""
    if "=" not in spec:
        raise ValueError("rate-limit spec must be TOKEN=rps/burst")
    token, rest = spec.split("=", 1)
    token = token.strip()
    if not token:
        raise ValueError("rate-limit token is empty")
    if "/" not in rest:
        raise ValueError("rate value must be rps/burst (e.g. 5/10)")
    rps_s, burst_s = rest.split("/", 1)
    try:
        rps, burst = float(rps_s), float(burst_s)
    except ValueError:
        raise ValueError(f"rate-limit rps/burst not numeric: {rest!r}")
    if rps <= 0 or burst <= 0:
        raise ValueError("rps and burst must be positive")
    return token, rps, burst


def handle_message(msg: dict, scopes: set[str] | None = None,
                   token: str | None = None,
                   emit_notification=None,
                   logging_state: dict | None = None) -> dict | None:
    method = msg.get("method", "")
    params = msg.get("params") or {}
    msg_id = msg.get("id")

    # notifications/cancelled · client asks us to stop working on a
    # previously-issued requestId. Notify-only semantics: record the id,
    # long-running tools poll _is_cancelled() between progress frames.
    if method == "notifications/cancelled":
        rid = params.get("requestId")
        if rid is not None:
            _mark_cancelled(rid)
        return None  # notification · no reply

    # logging/setLevel · session-scoped threshold the transport owner
    # keeps across calls on this connection. Invalid levels rejected
    # with -32602 so clients fail fast instead of silently downgrading.
    if method == "logging/setLevel":
        level = _normalize_log_level(params.get("level", ""))
        if level is None:
            return _reply_err(msg_id, -32602,
                              f"invalid log level: {params.get('level')!r}")
        if logging_state is not None:
            logging_state["level"] = level
        return _reply(msg_id, {})

    # Rate limit gate · applied before scope check so the client doesn't
    # leak scope info by spamming. Unknown methods and protocol chatter
    # never hit the bucket.
    if method in RATE_LIMITED_METHODS:
        bucket = _rate_bucket_for(token)
        if bucket is not None:
            ok, retry_after = bucket.acquire()
            if not ok:
                return _reply_err(
                    msg_id, -32029,
                    f"rate limited · retry in {retry_after:.2f}s",
                )

    if method == "initialize":
        return _reply(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}, "logging": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
    if method == "notifications/initialized":
        return None  # notification · no reply
    if method == "tools/list":
        visible = []
        for t in TOOLS.values():
            req = TOOL_SCOPE_MAP.get(t["schema"]["name"], "tools.read")
            if _has_scope(scopes, req):
                visible.append(t["schema"])
        return _reply(msg_id, {"tools": visible})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        tool = TOOLS.get(name)
        if not tool:
            return _reply_err(msg_id, -32601, f"unknown tool: {name}")
        req = TOOL_SCOPE_MAP.get(name, "tools.read")
        if not _has_scope(scopes, req):
            return _reply_err(msg_id, -32001, f"scope required: {req}")
        try:
            # Progress-aware tools: when the client included
            # `_meta.progressToken`, wire an emit callback that pushes
            # notifications/progress frames back over the caller's
            # transport. is_cancelled() lets the tool bail cooperatively.
            meta = params.get("_meta") or {}
            progress_token = meta.get("progressToken")
            # notifications/message (logging · Task #59) · gated by the
            # session's setLevel threshold. Closure captures the current
            # state dict so future setLevel calls take effect mid-tool.
            session_level_ref = logging_state or {"level": DEFAULT_LOG_LEVEL}

            def _log(level, data, logger=None):
                return emit_log(emit_notification,
                                session_level_ref.get("level", DEFAULT_LOG_LEVEL),
                                level, data, logger=logger)
            if tool.get("progress") and progress_token is not None and emit_notification:
                def _emit(progress, total=None, message=None):
                    frame = {
                        "jsonrpc": "2.0",
                        "method": "notifications/progress",
                        "params": {
                            "progressToken": progress_token,
                            "progress": progress,
                        },
                    }
                    if total is not None:
                        frame["params"]["total"] = total
                    if message is not None:
                        frame["params"]["message"] = message
                    emit_notification(frame)
                result = tool["fn"](args, emit=_emit,
                                    is_cancelled=lambda: _is_cancelled(msg_id),
                                    log=_log)
            elif tool.get("progress"):
                # Tool supports progress but client didn't ask · call
                # without emit. is_cancelled still wired so a cancellation
                # notification racing ahead still takes effect.
                result = tool["fn"](args, emit=None,
                                    is_cancelled=lambda: _is_cancelled(msg_id),
                                    log=_log)
            else:
                result = tool["fn"](args)
            reply = _reply(msg_id, result)
        except Exception as e:
            reply = _reply_err(msg_id, -32603, f"tool {name} failed: {e}")
        finally:
            _clear_cancelled(msg_id)
        return reply
    if method == "ping":
        return _reply(msg_id, {})
    if method == "server/status":
        # Unauthenticated-safe: only aggregate counters · no per-client
        # state or tool output. Useful for probes and dashboards.
        return _reply(msg_id, _metrics_snapshot())
    if method == "resources/list":
        if not _has_scope(scopes, "resources.read"):
            return _reply_err(msg_id, -32001, "scope required: resources.read")
        limit = params.get("limit") or RESOURCE_LIST_LIMIT
        try:
            limit = max(1, min(int(limit), RESOURCE_LIST_LIMIT))
        except (TypeError, ValueError):
            return _reply_err(msg_id, -32602, "limit must be an integer")
        return _reply(msg_id, {"resources": _list_session_resources(limit=limit)})
    if method == "resources/read":
        if not _has_scope(scopes, "resources.read"):
            return _reply_err(msg_id, -32001, "scope required: resources.read")
        uri = params.get("uri")
        if not uri:
            return _reply_err(msg_id, -32602, "uri required")
        try:
            return _reply(msg_id, _read_session_resource(uri))
        except ValueError as e:
            return _reply_err(msg_id, -32602, str(e))
        except FileNotFoundError as e:
            return _reply_err(msg_id, -32002, str(e))
    return _reply_err(msg_id, -32601, f"method not found: {method}")


def _reply(msg_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _reply_err(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


# ─── transport loops ──────────────────────────────────────────────

def _stdio_loop() -> int:
    """Read one JSON-RPC message per line from stdin · reply on stdout.

    This is the default transport and the one Claude Code / Desktop use.
    Session state is implicit (single process = single client).
    """
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
        reply = handle_message(msg, emit_notification=lambda f: (
            sys.stdout.write(json.dumps(f, ensure_ascii=False) + "\n"),
            sys.stdout.flush(),
        ))
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


def _build_server_ssl_context(cert: str, key: str,
                              client_ca: str | None = None):
    """Return an ssl.SSLContext for the TCP server.

    cert + key required. `client_ca` enables mTLS — every connecting peer
    must present a cert signed by that CA. Raises on bad paths.
    """
    import ssl
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile=cert, keyfile=key)
    if client_ca:
        ctx.load_verify_locations(cafile=client_ca)
        ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def _tcp_loop(host: str, port: int,
              token_table: dict[str, set[str]] | None,
              ssl_ctx=None) -> int:
    """Accept concurrent clients over TCP · one thread per client.

    Wire format: line-delimited JSON-RPC, same as stdio. The first message
    from every client MUST be either:
      1. `initialize` with `params.authToken` matching a token in `token_table`
         (auth enforced · peer inherits that token's scopes), or
      2. a plain `initialize` (when token_table is None · dev mode · full scope).

    Unauthenticated clients get one `-32001 unauthorized` reply and are
    disconnected. We log to stderr so operators see auth failures without
    polluting the wire.
    """
    import socket
    import threading

    if token_table is None:
        sys.stderr.write(
            "WARN · nautilus-compass MCP TCP running without any --token. "
            "Do not expose this port to untrusted networks.\n"
        )

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(16)
    proto = "tls" if ssl_ctx else "tcp"
    sys.stderr.write(f"nautilus-compass MCP listening on {host}:{port} ({proto})\n")

    def _serve(conn: socket.socket, addr: tuple) -> None:
        # None scopes = localhost dev grants everything. A real token
        # grants that token's scope set.
        authed = token_table is None
        scopes: set[str] | None = None if authed else set()
        session_token: str | None = None
        # Per-connection mutable state threaded into handle_message ·
        # logging_state["level"] starts at DEFAULT_LOG_LEVEL and can be
        # updated via logging/setLevel. Isolated per socket so one
        # client's verbose level never leaks into another's session.
        logging_state: dict = {"level": DEFAULT_LOG_LEVEL}
        _metrics_inc("total_connections")
        _metrics_inc("active_connections")
        try:
            buf = b""
            with conn, conn.makefile("rwb", buffering=0) as _f:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        return
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            msg = json.loads(line.decode("utf-8"))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                        if not authed:
                            supplied = ((msg.get("params") or {}).get("authToken")
                                        if isinstance(msg.get("params"), dict) else None)
                            if msg.get("method") != "initialize" or supplied not in (token_table or {}):
                                err = _reply_err(msg.get("id"), -32001, "unauthorized")
                                conn.sendall((json.dumps(err) + "\n").encode("utf-8"))
                                _metrics_inc("auth_failures")
                                sys.stderr.write(f"AUTH-FAIL · {addr[0]}:{addr[1]}\n")
                                return
                            authed = True
                            scopes = set((token_table or {}).get(supplied, set()))
                            session_token = supplied
                            # strip token before forwarding to handle_message so it
                            # never shows up in logs or downstream
                            if isinstance(msg.get("params"), dict):
                                msg["params"].pop("authToken", None)
                        reply = handle_message(
                            msg, scopes=scopes, token=session_token,
                            emit_notification=lambda f: conn.sendall(
                                (json.dumps(f, ensure_ascii=False) + "\n").encode("utf-8")),
                            logging_state=logging_state,
                        )
                        _metrics_inc("messages_handled")
                        if reply is not None:
                            conn.sendall((json.dumps(reply, ensure_ascii=False) + "\n").encode("utf-8"))
        except (ConnectionResetError, BrokenPipeError, OSError):
            return
        finally:
            _metrics_inc("active_connections", -1)

    try:
        while True:
            conn, addr = srv.accept()
            if ssl_ctx is not None:
                try:
                    conn = ssl_ctx.wrap_socket(conn, server_side=True)
                except Exception as e:
                    sys.stderr.write(f"TLS-HANDSHAKE-FAIL · {addr[0]}:{addr[1]} · {e}\n")
                    try:
                        conn.close()
                    except OSError:
                        pass
                    continue
            t = threading.Thread(target=_serve, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        return 0
    finally:
        srv.close()


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(prog="nautilus-compass-mcp")
    p.add_argument("--transport", choices=["stdio", "tcp"], default="stdio",
                   help="Transport layer. Default: stdio (for Claude Code / Desktop). "
                        "Use tcp for cross-machine A2A.")
    p.add_argument("--host", default="127.0.0.1",
                   help="TCP bind host. Default 127.0.0.1 · use 0.0.0.0 only behind a VPN.")
    p.add_argument("--port", type=int, default=8766,
                   help="TCP bind port. Default 8766.")
    p.add_argument("--token", action="append", default=None,
                   help="Shared secret required on `initialize` in TCP mode. "
                        "Accepts `TOKEN` (full scope · legacy) or `TOKEN:scope1,scope2` "
                        "(scope-restricted). Repeatable. Falls back to COMPASS_MCP_TOKEN. "
                        "stdio mode ignores this. Scopes: tools.read, tools.write, resources.read.")
    p.add_argument("--token-file", default=os.environ.get("COMPASS_MCP_TOKEN_FILE"),
                   help="JSON file mapping {token: [scopes]}. Merged with --token.")
    p.add_argument("--rate-limit", action="append", default=None,
                   help="Per-token token-bucket in TOKEN=rps/burst form. "
                        "Repeatable. Unlisted tokens are unlimited.")
    p.add_argument("--tls-cert", default=None,
                   help="Path to PEM server cert. Required with --tls-key.")
    p.add_argument("--tls-key", default=None,
                   help="Path to PEM server private key.")
    p.add_argument("--tls-client-ca", default=None,
                   help="Path to PEM CA · enables mTLS · requires client cert.")
    args = p.parse_args()

    if args.transport == "stdio":
        return _stdio_loop()
    # Legacy env fallback: COMPASS_MCP_TOKEN as a single full-scope token.
    specs = list(args.token) if args.token else []
    env_tok = os.environ.get("COMPASS_MCP_TOKEN")
    if env_tok and not specs and not args.token_file:
        specs = [env_tok]
    try:
        table = _load_token_table(specs, args.token_file)
        for rl in args.rate_limit or []:
            tok, rps, burst = _parse_rate_flag(rl)
            _rate_register(tok, rps, burst)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"ERR · bad token config: {e}\n")
        return 2
    ssl_ctx = None
    if args.tls_cert or args.tls_key or args.tls_client_ca:
        if not (args.tls_cert and args.tls_key):
            sys.stderr.write("ERR · --tls-cert and --tls-key must be set together\n")
            return 2
        try:
            ssl_ctx = _build_server_ssl_context(
                args.tls_cert, args.tls_key, args.tls_client_ca)
        except (OSError, ValueError) as e:
            sys.stderr.write(f"ERR · TLS cert load failed: {e}\n")
            return 2
    return _tcp_loop(args.host, args.port,
                     table if table else None, ssl_ctx=ssl_ctx)


if __name__ == "__main__":
    sys.exit(main())

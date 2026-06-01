"""V5 Memory Plugin v0.6 · Stop hook · session 结束自动蒸馏 strategy.

Claude Code Stop hook · 每个 session 结束时跑 ·
读 latest claude-mem 写的 session memory · 提取关键词扩 strategy_store.

设计 (R3 守 · 0 LLM):
  · 读 ~/.claude/projects/<encoded>/memory/session_*.md · 取最新一个
  · 提取 frontmatter description (这是 claude-mem 已写的总结)
  · 取所有现有 strategy 的 trigger_keywords · 算跟新 description 的重合
  · 重合度 ≥ 50% 的 strategy → 自动 +1 evidence_count + log
  · 不创建新 strategy (留给人工 audit)

输出: 写到 .cache/auto_distill_log.jsonl 让用户 review
"""
import json
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

_PLUGIN_USER = Path.home() / ".claude" / "plugins" / "nautilus-compass"
# CI / pip-install fallback · use the script's own dir when user-level path absent
PLUGIN_DIR = _PLUGIN_USER if _PLUGIN_USER.exists() else Path(__file__).resolve().parent
CACHE_DIR = PLUGIN_DIR / ".cache"
LOG_FILE = CACHE_DIR / "auto_distill_log.jsonl"
DRIFT_SIDECAR = CACHE_DIR / "drift_per_session.jsonl"
DAEMON_HOST = "127.0.0.1"
DAEMON_PORT = 9876
DRIFT_TIMEOUT_S = 5.0


def find_latest_session_memory() -> Path | None:
    """从所有项目的 memory 找 modified 最近的 session_*.md."""
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None
    candidates = []
    for proj in projects_dir.iterdir():
        if not (proj / "memory").exists():
            continue
        for f in (proj / "memory").glob("session_*.md"):
            try:
                candidates.append((f.stat().st_mtime, f))
            except Exception:
                pass
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def recent_session_memories(within_hours: float = 24.0) -> list[Path]:
    """v1.5.2 #1 · 所有项目 memory 中 mtime 在 within_hours 内的 session_*.md

    解决 age_s > 3600 单文件 gate 导致 daily 启动漏 ingest 的问题.
    """
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return []
    cutoff = time.time() - within_hours * 3600
    out = []
    for proj in projects_dir.iterdir():
        if not (proj / "memory").exists():
            continue
        for f in (proj / "memory").glob("session_*.md"):
            try:
                if f.stat().st_mtime >= cutoff:
                    out.append(f)
            except Exception:
                pass
    out.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return out


def _drift_check_via_daemon(query: str, project: str,
                            timeout: float = DRIFT_TIMEOUT_S) -> dict | None:
    """v1.5.3 #1 · TCP 9876 直调 daemon · 不依赖 compass_http 8765 · fail-soft.

    Returns daemon's `drift` payload dict, or None on any failure.
    Daemon protocol (see daemon.py:7-9):
        req:  {"action":"drift","query":"...","project":"..."}
        resp: {"ok":true,"drift":{"score":..,"alignment":..,"deviation":..,
               "should_alert":..,"top_neg_hits":[..],"n_pos":..,"n_neg":..}}
    """
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((DAEMON_HOST, DAEMON_PORT))
        req = {"action": "drift", "query": query[:1500], "project": project}
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        deadline = time.time() + timeout
        while True:
            if time.time() > deadline:
                return None
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n"):
                break
        resp = json.loads(buf.decode("utf-8"))
        return resp.get("drift") if resp.get("ok") else None
    except Exception:
        return None
    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass


def _drift_already_scored(session_name: str) -> bool:
    """v1.5.3 #1 · idempotent · 防 stop_hook 重跑写重复行."""
    if not DRIFT_SIDECAR.exists():
        return False
    try:
        with open(DRIFT_SIDECAR, encoding="utf-8") as f:
            for line in f:
                try:
                    if json.loads(line).get("session_file") == session_name:
                        return True
                except Exception:
                    continue
    except Exception:
        pass
    return False


def _write_drift_sidecar(session_path: Path, drift: dict) -> None:
    """v1.5.3 #1 · 写一行 jsonl · 一次 session 一条 · 绕 frontmatter 直接落盘."""
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_file": session_path.name,
        "score": drift.get("score"),
        "alignment": drift.get("alignment"),
        "deviation": drift.get("deviation"),
        "should_alert": drift.get("should_alert"),
        "top_neg_hits": drift.get("top_neg_hits", []),
        "n_pos": drift.get("n_pos"),
        "n_neg": drift.get("n_neg"),
    }
    DRIFT_SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    with open(DRIFT_SIDECAR, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def parse_session_summary(path: Path) -> str:
    """读 session memory · 提 description + body 前 1500 字."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end > 0:
            fm_block = text[4:end]
            body = text[end + 4:].strip()
            desc = ""
            for line in fm_block.split("\n"):
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                    break
            return f"{desc}\n{body[:1500]}"
    return text[:1500]


def main():
    sys.path.insert(0, str(PLUGIN_DIR))
    # Plan A (2026-05-30) · let repo-resident H.1 / D.fix / E.fix modules win
    # over plugin install when settings.json hook redirects Stop here. Script
    # dir goes in last → sits at sys.path[0] → Python finds drift/auto_ack.py
    # before plugin install's drift/ (which only has gate_act.py + routing.py).
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from strategy_store import StrategyStore

    # v0.8 · session_writer (替代 claude-mem 的 writer)
    # 先写本次 session memory · 再走 distill 链路接力
    try:
        from session_writer import main as _writer_main
        _writer_main()
    except Exception as _we:
        sys.stderr.write(f"[stop_hook] session_writer fail: {_we}\n")

    latest = find_latest_session_memory()
    if not latest:
        print("[stop_hook] no session memory found · skip")
        return 0

    # v1.5.2 #1 · numeric_claims ingest 24h glob · 不被 latest age_gate 吃掉
    # · 上线时 latest 可能 24h 老 · 但本周新 session 仍要 ingest
    try:
        from numeric_claims import ingest_session_file, already_ingested
        _nc_total = 0
        _nc_files = 0
        for f in recent_session_memories(within_hours=24.0):
            if already_ingested(str(f)):
                continue
            _nc_total += ingest_session_file(f)
            _nc_files += 1
        if _nc_total:
            print(f"[stop_hook] numeric_claims: ingested {_nc_total} claim(s) from {_nc_files} new session(s)")
    except Exception as _nce:
        sys.stderr.write(f"[stop_hook] numeric_claims ingest fail: {_nce}\n")

    # v1.5.3 #1 · drift_check via daemon TCP 9876 · 24h glob · idempotent ·
    # fail-soft · 5s timeout. 不被 age_gate 吃掉(类比 v1.5.2 numeric_claims 路径).
    # Sidecar 一行一 session · 绕 frontmatter · 不依赖 compass_http.
    try:
        _dr_total = 0
        _dr_alert = 0
        _dr_last = None
        for f in recent_session_memories(within_hours=24.0):
            if _drift_already_scored(f.name):
                continue
            summary_raw = parse_session_summary(f)
            if not summary_raw:
                continue
            project = f.parent.parent.name
            drift = _drift_check_via_daemon(summary_raw, project)
            if drift is None:
                # daemon down · stop trying for this run (avoid 5s × N stall)
                print("[stop_hook drift] daemon unreachable · skip rest (fail-soft)")
                break
            _write_drift_sidecar(f, drift)
            _dr_total += 1
            _dr_last = drift
            if drift.get("should_alert"):
                _dr_alert += 1
        if _dr_total:
            s = _dr_last or {}
            alert_tag = f" · {_dr_alert} ALERT" if _dr_alert else ""
            print(f"[stop_hook drift] scored {_dr_total} new session(s) · "
                  f"last score={s.get('score')} align={s.get('alignment')}"
                  f"{alert_tag} · sidecar: {DRIFT_SIDECAR.name}")
    except Exception as _de:
        sys.stderr.write(f"[stop_hook] drift_check fail: {_de}\n")

    # v1.6.0 · 用户 #1 真融合 phase 2 · cloud persistence backup
    # 反向 SSH tunnel 在时 V5/Kairos 已透过 -R 9876 看见本地 · 此处是 tunnel 死/重启时的持久化
    # SSH inline POST · idempotent via sidecar · fail-soft
    try:
        from cloud_ingest import ingest_session_to_cloud, _already_pushed
        _ci_pushed = 0
        _ci_skipped = 0
        for f in recent_session_memories(within_hours=24.0):
            if _already_pushed(f.name):
                _ci_skipped += 1
                continue
            result = ingest_session_to_cloud(f)
            if result and result.get("ok"):
                _ci_pushed += 1
            else:
                # SSH/cloud fail · skip remaining to avoid N×10s timeout
                break
        if _ci_pushed:
            print(f"[stop_hook cloud_ingest] pushed {_ci_pushed} session(s) · skipped {_ci_skipped} already-pushed")
    except Exception as _ce:
        sys.stderr.write(f"[stop_hook] cloud_ingest fail: {_ce}\n")

    # v1.7.0 · 方向 2 · cross-agent contract scanner (sprint D3-4 · 5/17-5/30)
    # 扫所有 7 项目 memory 168h glob · expired 没 alert 过的 fire alert
    # · 写 .cache/contract_alerts.jsonl · UserPromptSubmit hook 下次读它注入 prompt
    # · 度量: outstanding/consumed/expired 计数 · north-star close_loop time
    try:
        from contract import (
            scan_sessions_for_contracts, fire_alerts_for_expired,
            _default_memory_roots, _parse_iso,
        )
        from datetime import timezone
        # 5/31 reconcile: 168→720h · 兑现 D.fix-3 意图(历史 close-loop 文件 >7d 也 resolve)
        _scan = scan_sessions_for_contracts(_default_memory_roots(), within_hours=720.0)
        _fired = fire_alerts_for_expired(_scan["expired"])
        # Compute mean close_loop time for consumed contracts (north-star metric)
        _cl_times = []
        for c in _scan["consumed"]:
            iss = _parse_iso(c.issued_at)
            con = _parse_iso(c.consumed_at)
            if iss and con:
                _cl_times.append((con - iss).total_seconds() / 3600.0)
        _cl_mean = sum(_cl_times) / len(_cl_times) if _cl_times else None
        if _scan["outstanding"] or _scan["consumed"] or _scan["expired"]:
            _msg = (f"[stop_hook contracts] scanned {_scan['files_scanned']} files · "
                    f"outstanding={len(_scan['outstanding'])} "
                    f"consumed={len(_scan['consumed'])} "
                    f"expired={len(_scan['expired'])}")
            if _cl_mean is not None:
                _msg += f" · close_loop_mean={_cl_mean:.2f}h"
            if _fired:
                _msg += f" · {_fired} new EXPIRED alert(s)"
            print(_msg)
    except Exception as _coe:
        sys.stderr.write(f"[stop_hook] contract scan fail: {_coe}\n")

    # H.1 (2026-05-30) · agent self-ack auto-detection · closes the 5/27
    # drift loop's last unmeasured side. Reads the just-written latest session
    # memory body · scans for `a-XXXXXXXX` alert_id literals with nearby ack
    # signal (fp/tp/acknowledged) · writes acks to drift_mitigation_log via
    # log_drift_ack. Rule-based · no LLM · paragraph-bounded window prevents
    # cross-talk between distinct alerts. Idempotency: each session memory
    # processed at most once per stop_hook run · re-scans on subsequent runs
    # are harmless because log_drift_ack appends rather than dedups (act_on_rate
    # naturally dedups by alert_id on read).
    try:
        from drift.auto_ack import extract_acks_from_text, emit_acks_to_sidecar
        if latest and latest.exists():
            _body_text = latest.read_text(encoding="utf-8", errors="replace")
            _acks = extract_acks_from_text(_body_text)
            _n_emitted = emit_acks_to_sidecar(_acks, source="stop_hook_auto")
            if _n_emitted:
                _summary = ", ".join(f"{a['alert_id']}={a['status']}" for a in _acks[:5])
                print(f"[stop_hook auto_ack] emitted {_n_emitted} drift ack(s) · {_summary}")
    except Exception as _aae:
        sys.stderr.write(f"[stop_hook] auto_ack fail: {_aae}\n")

    age_s = time.time() - latest.stat().st_mtime
    if age_s > 3600:
        # 上次 session memory > 1h 旧 · 不是本次 session · strategy match 仍 skip
        # · numeric_claims + drift_check 已在上面跑完不受影响
        print(f"[stop_hook] latest session {latest.name} is {age_s/60:.1f} min old · skip strategy match")
        return 0

    # v1.7 #2 · numeric_claims ingest 已在 age_gate 前移到 24h glob 路径 (v1.5.2 #1)

    summary_raw = parse_session_summary(latest)
    summary = summary_raw.lower()
    if not summary:
        return 0

    store = StrategyStore()
    matched = []
    for s in store._strategies:
        if s.get("archived"):
            continue
        kws = s.get("trigger_keywords") or []
        if not kws:
            continue
        hits = [kw for kw in kws if kw.lower() in summary]
        if len(hits) >= max(1, len(kws) // 2):
            matched.append({
                "id": s["id"],
                "task": s.get("task_summary", "")[:60],
                "hit_keywords": hits,
            })
            # +1 evidence_count
            s["evidence_count"] = s.get("evidence_count", 1) + 1
            s["last_used_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # v1.1 · LLM 真蒸馏 (有 API key 时跑 · 自动加新 strategy)
    try:
        from llm_distill import distill_from_session_memory, get_api_key
        if get_api_key():
            distill_from_session_memory(latest, store)
    except Exception as _le:
        sys.stderr.write(f"[stop_hook] llm_distill fail: {_le}\n")

    # v1.6 · Ebbinghaus decay (无论 matched 与否都跑)
    decay = store.apply_ebbinghaus_decay()
    if decay["decayed"] > 0 or decay["archived"] > 0:
        print(f"[stop_hook decay] decayed={decay['decayed']} archived={decay['archived']}")

    if matched:
        store._rewrite()
        log_entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_memory": latest.name,
            "matched_strategies": matched,
        }
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"[stop_hook] {len(matched)} strategies +ev · log: {LOG_FILE.name}")
        for m in matched:
            print(f"  · {m['id']} '{m['task']}' hits={m['hit_keywords']}")
    return 0


# ============================================================================
# v1.7.1 · agentmemory fuse · 9 lifecycle hooks (Phase 2 partial · plan §4)
#
# Emit declaration_field-schema'd entries to .cache/hook_events.jsonl for each
# agent runtime hook. Pure deterministic · no LLM. Future-ready for Claude Code
# hook registration via settings.json `--hook <name>` CLI dispatch.
#
# Verbatim 9 hook names from agentmemory README (rohitg00 · 15.3K stars).
# See paper/LLM_WIKI2_FUSE_DESIGN.md §3 for tier/promote_after schema rationale.
# ============================================================================

HOOK_EVENTS_FILE = CACHE_DIR / "hook_events.jsonl"

_TIER_DEFAULT_PROMOTE = {
    "working": "1_access",
    "episodic": "5_access",
    "semantic": "20_access",
    "procedural": None,
}


def _emit_lifecycle_event(hook_name: str, payload: dict,
                          tier: str = "working",
                          promote_after: str | None = None,
                          drift: str = "green") -> dict:
    """v1.7.1 · emit declaration_field-schema'd lifecycle event entry.

    Returns dict with frontmatter fields. Caller appends to .jsonl sidecar
    or passes to compass MCP ingest_obs. No LLM. Deterministic.
    """
    ts = datetime.now(timezone.utc).isoformat()
    summary = ""
    if isinstance(payload, dict):
        summary = (payload.get("summary") or payload.get("text")
                   or payload.get("description") or "")
    return {
        "hook": hook_name,
        "ts": ts,
        "name": f"hook-{hook_name.lower()}-{ts[:19]}",
        "type": "discovery",
        "concept": "how-it-works",
        "drift": drift,
        "tier": tier,
        "decay_rate": 0.5,
        "promote_after": promote_after or _TIER_DEFAULT_PROMOTE.get(tier),
        "reinforce_count": 0,
        "agent_type": (payload.get("agent_type") if isinstance(payload, dict) else "") or "claude-code",
        "thread_id": (payload.get("thread_id") if isinstance(payload, dict) else "") or "",
        "thread_role": "self_note",
        "declaration_type": "none",
        "payload_summary": str(summary)[:200],
    }


def hook_session_start(payload: dict) -> dict:
    """SessionStart · capture project path, session ID. tier=working."""
    return _emit_lifecycle_event("SessionStart", payload, tier="working")


def hook_user_prompt_submit(payload: dict) -> dict:
    """UserPromptSubmit · user input recorded (privacy-filtered)."""
    return _emit_lifecycle_event("UserPromptSubmit", payload, tier="working")


def hook_pre_tool_use(payload: dict) -> dict:
    """PreToolUse · before tool executes · capture file access pattern."""
    return _emit_lifecycle_event("PreToolUse", payload, tier="working")


def hook_post_tool_use(payload: dict) -> dict:
    """PostToolUse · after tool completes · log tool name, input, output."""
    return _emit_lifecycle_event("PostToolUse", payload, tier="working")


def hook_post_tool_use_failure(payload: dict) -> dict:
    """PostToolUseFailure · tool errors · drift=yellow (failure signal)."""
    return _emit_lifecycle_event("PostToolUseFailure", payload, tier="working", drift="yellow")


def hook_pre_compact(payload: dict) -> dict:
    """PreCompact · before compaction · re-inject memory. tier=episodic."""
    return _emit_lifecycle_event("PreCompact", payload, tier="episodic")


def hook_subagent_start(payload: dict) -> dict:
    """SubagentStart · sub-agent lifecycle · track delegation."""
    return _emit_lifecycle_event("SubagentStart", payload, tier="working")


def hook_subagent_stop(payload: dict) -> dict:
    """SubagentStop · sub-agent stop · episodic promotion candidate."""
    return _emit_lifecycle_event("SubagentStop", payload, tier="episodic")


def hook_session_end(payload: dict) -> dict:
    """SessionEnd · session complete · mark completion + trigger self_evolve.

    v2.0.0 · #2 · trigger Layer 2 L1 auto-build when ungrouped sessions
    accumulate past DEFAULT_L1_TRIGGER_THRESHOLD (3). Graceful · errors
    don't block hook return (the lifecycle event still emits).
    """
    event = _emit_lifecycle_event("SessionEnd", payload, tier="episodic")
    # OV-paradigm self-evolve · build L1 collapse layer + entity link scan
    try:
        from storage.self_evolve import evolve_at_session_end
        # Find active project memory dir · same convention as recall.py
        from recall import find_active_project_memory_dir
        mem_dir = find_active_project_memory_dir()
        if mem_dir is not None:
            result = evolve_at_session_end(mem_dir)
            if result.get("l1_triggered", {}).get("triggered"):
                # Attach summary into the hook event for observability
                event.setdefault("self_evolve", {})["l1"] = result["l1_triggered"]
    except Exception as e:
        # Fail-soft · don't break SessionEnd hook
        event.setdefault("self_evolve_error", str(e))
    return event


def _write_hook_event(event: dict) -> None:
    """Append event to .cache/hook_events.jsonl sidecar."""
    HOOK_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HOOK_EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


HOOK_DISPATCH = {
    "SessionStart": hook_session_start,
    "UserPromptSubmit": hook_user_prompt_submit,
    "PreToolUse": hook_pre_tool_use,
    "PostToolUse": hook_post_tool_use,
    "PostToolUseFailure": hook_post_tool_use_failure,
    "PreCompact": hook_pre_compact,
    "SubagentStart": hook_subagent_start,
    "SubagentStop": hook_subagent_stop,
    "SessionEnd": hook_session_end,
}


def dispatch_hook(hook_name: str, payload: dict | None = None) -> int:
    """v1.7.1 · CLI dispatch for non-Stop hooks. Returns exit code 0 on success."""
    handler = HOOK_DISPATCH.get(hook_name)
    if handler is None:
        sys.stderr.write(f"unknown hook: {hook_name}\n")
        return 0  # fail-soft · unknown hook never blocks Claude Code
    payload = payload or {}
    event = handler(payload)
    if event:
        _write_hook_event(event)
    return 0


if __name__ == "__main__":
    # v1.7.1 · dispatch by --hook <name> CLI flag · backward-compat: no flag → Stop
    hook_name = "Stop"
    payload: dict = {}
    if len(sys.argv) >= 3 and sys.argv[1] == "--hook":
        hook_name = sys.argv[2]
        # Optional payload from stdin (JSON)
        if not sys.stdin.isatty():
            try:
                raw = sys.stdin.read()
                if raw.strip():
                    payload = json.loads(raw)
            except Exception:
                payload = {}
    try:
        if hook_name == "Stop":
            sys.exit(main())
        else:
            sys.exit(dispatch_hook(hook_name, payload))
    except Exception as e:
        sys.stderr.write(f"stop_hook fail: {e}\n")
        sys.exit(0)

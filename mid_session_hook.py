#!/usr/bin/env python3
"""nautilus-compass v0.7 · PostToolUse hook · mid-session refresh.

问题: session 长跑 + 自动压缩后 · nautilus-compass 状态丢失
      用户在 session 中段心智已变 · 但 hook 只在 session 开头跑
解法: 每 N tool calls 跑一次轻量召回 · 把"session 期间"心智注入

设计:
  · 静默工作 · 多数情况不输出 (避免噪音)
  · 仅当: a) 距上次 refresh > 20 min  AND  b) tool 调用数 % 30 == 0
    才触发一次 BGE refresh (走 daemon)
  · 失败完全静默
"""
import json
import socket
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
    sys.stderr.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

_PLUGIN_USER = Path.home() / ".claude" / "plugins" / "nautilus-compass"
# CI / pip-install fallback · use the script's own dir when user-level path absent
PLUGIN_DIR = _PLUGIN_USER if _PLUGIN_USER.exists() else Path(__file__).resolve().parent
CACHE_DIR = PLUGIN_DIR / ".cache"
STATE_FILE = CACHE_DIR / "mid_session_state.json"
REFRESH_INTERVAL_S = 1200    # 20 min · 中段刷新阈值
TOOL_CALL_TRIGGER = 30       # 每 30 个 tool 检查一次


def read_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_refresh_ts": 0, "tool_count": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_refresh_ts": 0, "tool_count": 0}


def write_state(s: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(s), encoding="utf-8")
    except Exception:
        pass


def daemon_alive() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            s.connect(("127.0.0.1", 9876))
            s.sendall(b'{"action":"ping"}\n')
            return b'"pong"' in s.recv(1024)
    except Exception:
        return False


def read_tool_input() -> tuple[str, dict]:
    """v0.7.1 · 读 Claude Code PostToolUse hook stdin · 拿 tool_name + tool_input."""
    if sys.stdin.isatty():
        return "", {}
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        return data.get("tool_name", ""), data.get("tool_input", {})
    except Exception:
        return "", {}


def tool_to_signature(tool_name: str, tool_input: dict) -> str:
    """把 tool_call 渲染成 behavior signature string · 给 drift detection 看.

    例:
      Bash(taskkill /F /IM node.exe)        → 'Bash: taskkill /F /IM node.exe'
      Edit(secrets.py, OPENAI_KEY="sk-...") → 'Edit: secrets.py · OPENAI_KEY=sk-...'
    """
    if not tool_name:
        return ""
    parts = [tool_name + ":"]
    if tool_name == "Bash":
        parts.append(str(tool_input.get("command", ""))[:300])
    elif tool_name in ("Edit", "Write"):
        path = str(tool_input.get("file_path", ""))
        # only the new content head · 检测是否 hardcode key/dangerous content
        new_str = str(tool_input.get("new_string", "") or tool_input.get("content", ""))[:200]
        parts.append(f"{path} · {new_str}")
    elif tool_name == "TaskCreate":
        parts.append(str(tool_input.get("subject", ""))[:200])
    else:
        # Generic
        parts.append(json.dumps(tool_input, ensure_ascii=False)[:300])
    return " ".join(parts)


def check_tool_drift(signature: str) -> tuple[float, str] | None:
    """v0.7.1 · 用 daemon 算 signature 的 drift · 高于 NEG_HIT 触发 stderr 警告.

    Returns (max_neg_cos, anchor_text) if alert, else None.
    """
    if not signature or not daemon_alive():
        return None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(("127.0.0.1", 9876))
            req = {"action": "drift", "query": signature[:500],
                   "project": "C--Users-chunx", "top_k": 0}
            try:  # v3.0.10 · daemon 9876 token auth
                req["token"] = (Path.home() / ".claude" / ".cache"
                                / "compass_daemon_token").read_text(encoding="utf-8").strip()
            except OSError:
                pass
            s.sendall(json.dumps(req, ensure_ascii=False).encode("utf-8") + b"\n")
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk: break
                buf += chunk
        data = json.loads(buf.decode("utf-8").split("\n")[0])
        d = data.get("drift") or {}
        hits = d.get("top_neg_hits") or []
        if hits and hits[0][0] >= 0.55:   # tool drift 严格阈值 (vs prompt 0.538)
            return hits[0][0], hits[0][1]
    except Exception:
        pass
    return None


def main():
    state = read_state()
    state["tool_count"] = state.get("tool_count", 0) + 1
    now = time.time()
    elapsed = now - state.get("last_refresh_ts", 0)

    # v0.7.1 · 每个 tool call 都跑 drift check (但 daemon dead 时 0 cost)
    tool_name, tool_input = read_tool_input()
    if tool_name:
        sig = tool_to_signature(tool_name, tool_input)
        alert = check_tool_drift(sig)
        if alert:
            cos, anchor = alert
            sys.stderr.write(
                f"[nautilus-compass tool-drift] ⚠️ {tool_name} cos={cos:.3f} → '{anchor[:80]}'\n"
                f"  signature: {sig[:100]}\n"
            )
            # log_usage equivalent
            try:
                log_path = CACHE_DIR / "tool_drift_log.jsonl"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "tool": tool_name, "cos": round(cos, 3),
                        "anchor": anchor[:100], "signature": sig[:200],
                    }, ensure_ascii=False) + "\n")
            except Exception:
                pass

    # v0.7.1 · auto-retrain trigger: 累计 ≥10 feedback 自动跑 retrain
    if state["tool_count"] % 50 == 0:   # 每 50 tool 检查一次
        try:
            fb_path = CACHE_DIR / "feedback.jsonl"
            if fb_path.exists():
                fb_count = sum(1 for _ in open(fb_path, encoding="utf-8"))
                last_retrain = state.get("last_auto_retrain_count", 0)
                if fb_count - last_retrain >= 10:
                    sys.stderr.write(
                        f"[nautilus-compass auto-retrain] 累计 {fb_count} feedback (Δ {fb_count - last_retrain})\n"
                        f"  建议: python {PLUGIN_DIR}/feedback.py retrain\n"
                    )
                    state["last_auto_retrain_count"] = fb_count
        except Exception:
            pass

    should_refresh = (
        state["tool_count"] % TOOL_CALL_TRIGGER == 0
        and elapsed > REFRESH_INTERVAL_S
        and daemon_alive()
    )

    if should_refresh:
        # 输出 mid-session 提醒 · 让 LLM 知道时间过去了 · 该重新校准
        elapsed_min = int(elapsed / 60)
        sys.stderr.write(
            f"[nautilus-compass mid-session] {elapsed_min} min 已过 · {state['tool_count']} 次 tool · "
            f"建议主动跑: python3 ~/.claude/plugins/nautilus-compass/recall.py --bge --query \"<当前任务关键词>\"\n"
        )
        state["last_refresh_ts"] = now

    # v1.0+ · v2 · check recall consumption every 25 tool calls (cheap, 5KB tail read)
    # Trigger when ratio drops below 0.3 (most surfaced files unread) · only stderr-print
    if state["tool_count"] % 25 == 0:
        try:
            sys.path.insert(0, str(PLUGIN_DIR))
            from recall_consumption import audit_consumption, render_consumption_warning
            rep = audit_consumption(window_user_turns=5)
            unc = rep.get("unconsumed_paths") or []
            seen = rep.get("recall_paths_seen") or []
            # Only nag if there's signal · ≥3 unconsumed AND ratio < 0.3
            if len(unc) >= 3 and rep.get("ratio", 1.0) < 0.3:
                warn = render_consumption_warning(rep)
                if warn:
                    sys.stderr.write(f"[nautilus-compass recall-consumption]\n{warn}\n")
                    state["last_consumption_warn_ts"] = now
        except Exception:
            pass

    write_state(state)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)

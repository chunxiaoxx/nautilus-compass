#!/usr/bin/env python3
"""Local-only Compass value loop.

The retired Claude loop starts an external model before it can evaluate the
round stop gate. This runner performs the small read-only probe set itself,
then uses the local Qwen3.5-9B service for bounded tool planning and a Chinese
summary. It never sends mail, posts to GitHub, changes platform state, or calls
an external model.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOOP_DIR = ROOT / "runtime" / "loop"
STATE_PATH = LOOP_DIR / "local_state.json"
RECEIPT_PATH = LOOP_DIR / "local_round_receipt.json"
LOG_PATH = LOOP_DIR / "local_rounds.log"
LOCK_PATH = LOOP_DIR / ".local-loop.lock"
LOCAL_LLM_URL = os.environ.get(
    "LOCAL_LLM_URL", "http://127.0.0.1:11435/v1/chat/completions"
)
LOCAL_LLM_MODEL = os.environ.get("LOCAL_LLM_MODEL_ID", "Qwen3.5-9B-4bit")


def _short(value: str, limit: int = 900) -> str:
    value = re.sub(r"(?i)(bearer\s+)[^\s]+", r"\1<redacted>", value)
    value = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=<redacted>", value)
    value = value.strip()
    return value if len(value) <= limit else value[:limit] + "…"


def _run(name: str, argv: list[str], timeout: int = 20) -> dict[str, Any]:
    started = time.monotonic()
    try:
        p = subprocess.run(
            argv,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return {
            "name": name,
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "elapsed_s": round(time.monotonic() - started, 3),
            "stdout": _short(p.stdout),
            "stderr": _short(p.stderr, 500),
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "ok": False,
            "returncode": None,
            "elapsed_s": round(time.monotonic() - started, 3),
            "stdout": "",
            "stderr": "timeout",
        }
    except Exception as exc:
        return {
            "name": name,
            "ok": False,
            "returncode": None,
            "elapsed_s": round(time.monotonic() - started, 3),
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def _socket_probe() -> dict[str, Any]:
    started = time.monotonic()
    sock = socket.socket()
    sock.settimeout(5)
    try:
        sock.connect(("127.0.0.1", 9876))
        return {"name": "compass_daemon_9876", "ok": True, "elapsed_s": round(time.monotonic() - started, 3)}
    except Exception as exc:
        return {"name": "compass_daemon_9876", "ok": False, "elapsed_s": round(time.monotonic() - started, 3), "error": f"{type(exc).__name__}: {exc}"}
    finally:
        sock.close()


def _local_llm_health() -> dict[str, Any]:
    req = urllib.request.Request("http://127.0.0.1:11435/health", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {"name": "local_llm_11435", "ok": data.get("status") == "ok", "health": data}
    except Exception as exc:
        return {"name": "local_llm_11435", "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _gmail_probe() -> dict[str, Any]:
    token_path = Path.home() / ".gmail-mcp" / "access_token.txt"
    if not token_path.exists():
        return {"name": "gmail_inbox_probe", "ok": False, "error": "access_token_missing"}
    token = token_path.read_text(encoding="utf-8").strip()
    result = _run(
        "gmail_inbox_probe",
        [
            "curl",
            "-sS",
            "-m",
            "15",
            "-H",
            f"Authorization: Bearer {token}",
            "https://gmail.googleapis.com/gmail/v1/users/me/labels/INBOX",
        ],
        timeout=20,
    )
    result["stdout"] = "HTTP probe completed" if result["ok"] else result["stderr"]
    return result


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"round": 0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"round": 0, "state_error": "invalid local_state.json"}


def _save_state(state: dict[str, Any]) -> None:
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def _call_local_llm(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = {
        "role": "user",
        "content": (
            "根据下面的本地值守探针结果，用通俗中文写一个不超过 180 字的运行摘要。"
            "只输出 JSON，字段必须是 status、findings、next_action。"
            "status 只能取 healthy、degraded、blocked。不要执行命令，不要建议发送邮件或发帖。\n"
            + json.dumps(evidence, ensure_ascii=False)
        ),
    }
    body = {
        "model": LOCAL_LLM_MODEL,
        "messages": [
            {"role": "system", "content": "你是 Compass 的本地值守摘要器。先看证据，再给短结论。"},
            prompt,
        ],
        "max_tokens": 256,
        "temperature": 0,
        "enable_thinking": False,
    }
    request = urllib.request.Request(
        LOCAL_LLM_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return {"ok": True, "model": payload.get("model", LOCAL_LLM_MODEL), "summary": parsed}
        except json.JSONDecodeError:
            pass
        return {"ok": True, "model": payload.get("model", LOCAL_LLM_MODEL), "summary": {"status": "degraded", "findings": _short(content, 500), "next_action": "检查本地模型输出格式"}}
    except Exception as exc:
        return {"ok": False, "model": LOCAL_LLM_MODEL, "error": f"{type(exc).__name__}: {exc}"}


def _run_local_agent_round() -> dict[str, Any]:
    """Use the bounded 9B tool runtime for one read-only capability pass."""
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.local_agent_runtime import run_task

        event = run_task(
            "本轮只读核对本地 9B、Compass daemon 和语义记忆。"
            "必须按顺序调用 local_health、compass_daemon_probe、compass_recall，"
            "compass_recall 的 query 固定为‘本地 9B、Compass 记忆服务和组织连续性当前状态’，top_k=3，metadata_only=true。"
            "完成这三个工具后，必须调用 evidence_gate，用工具回执中的 source 或 path 和 status 或 fact_status 逐条组成证据。"
            "不要把 recall 返回的历史命中内容当作当前服务状态，尤其不要根据历史描述推断 daemon 当前停用。"
            "不要调用 memory_search 或 org_continuity_read，不要写草稿，不要发送邮件、GitHub 评论、部署或执行任意 shell。",
            max_steps=4,
        )
        return {
            "ok": not event.get("contract_violations"),
            "model": event.get("model", LOCAL_LLM_MODEL),
            "final": event.get("final", ""),
            "step_count": len(event.get("steps") or []),
            "external_model_used": bool(event.get("external_model_used")),
            "external_send": bool(event.get("external_send")),
        }
    except Exception as exc:
        return {
            "ok": False,
            "model": LOCAL_LLM_MODEL,
            "error": f"{type(exc).__name__}: {exc}",
            "external_model_used": False,
            "external_send": False,
        }


def main() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from runtime.loop.stop_gate import inspect_stop_gate

    initial_gate = inspect_stop_gate(ROOT)
    if initial_gate["blocked"]:
        print(f"local loop stopped by shared stop gate: {initial_gate['reasons']}")
        return 0

    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("local loop already running")
            return 0

        gate = inspect_stop_gate(ROOT)
        if gate["blocked"]:
            print(f"local loop stopped by shared stop gate: {gate['reasons']}")
            return 0

        state = _load_state()

        state["round"] = int(state.get("round", 0)) + 1
        round_id = state["round"]
        state["last_started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        _save_state(state)

        evidence = [
            _local_llm_health(),
            _socket_probe(),
            _run("platform_mail_read", [sys.executable, "scripts/platform_mail.py", "check", "--to", "compass"]),
            _run("github_mentions_read", ["/opt/homebrew/bin/gh", "search", "issues", "mentions:chunxiaoxx", "--sort", "updated", "--limit", "5"]),
            _gmail_probe(),
            _run("injection_sentinel", ["bash", "scripts/injection_sentinel.sh"]),
        ]
        local_agent = _run_local_agent_round()
        summary_evidence = evidence + [{
            "name": "local_agent_runtime",
            "ok": local_agent.get("ok", False),
            "model": local_agent.get("model", LOCAL_LLM_MODEL),
            "final": local_agent.get("final", ""),
            "external_model_used": local_agent.get("external_model_used", False),
            "external_send": local_agent.get("external_send", False),
        }]
        local_summary = _call_local_llm(summary_evidence)
        if not local_agent.get("ok", False):
            local_summary = {
                "ok": False,
                "model": local_summary.get("model", LOCAL_LLM_MODEL),
                "summary": {
                    "status": "degraded",
                    "findings": "本地 agent 能力层没有取得完整成功回执，未把值守轮判为健康。",
                    "next_action": "检查 local_agent_runtime 的失败步骤后再继续值守。",
                },
            }
        receipt = {
            "round": round_id,
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "external_model_used": False,
            "local_model": LOCAL_LLM_MODEL,
            "checks": evidence,
            "local_agent": local_agent,
            "summary": local_summary,
        }
        tmp = RECEIPT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(RECEIPT_PATH)
        with LOG_PATH.open("a", encoding="utf-8") as log:
            log.write(json.dumps({"round": round_id, "external_model_used": False, "summary": local_summary}, ensure_ascii=False) + "\n")
        print(json.dumps(receipt, ensure_ascii=False))
        return 0 if local_summary.get("ok") and local_agent.get("ok", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())

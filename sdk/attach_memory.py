"""compass · one-line Nautilus platform memory integration · #3 runtime injection.

把 compass 接入任何 Nautilus agent · 1 行代码:

    from nautilus_compass.sdk.attach_memory import attach_memory
    agent = NautilusAgent(role="strategy", user_id="u_xxx")
    attach_memory(agent)   # ← 这一行

之后 agent 自动:
  · 注册到 compass (agent_id 持久化 · 同 role+device 同 id)
  · 完成 task → ingest_obs (drift 自审)
  · 调 action 前 → recall 相关 memory 注入 prompt
  · 检测 drift=red → 触发 stake_penalty (#4 economic coupling)
  · 跨 agent 历史自动可见

抽象原则 (PLATFORM_FUSION 风险章):
  · 不强依赖 nautilus-agent SDK 具体 API · 用 duck typing
  · 任何 attribute 缺失 = 跳过该 hook · 不报错
  · compass 不在线 → 走 offline_buffer · 不阻塞 agent
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compass_client import CompassClient


def _resolve_user_id(user_id: Optional[str], agent: Any) -> str:
    if user_id:
        return user_id
    for attr in ("user_id", "owner_id", "principal"):
        v = getattr(agent, attr, None)
        if isinstance(v, str) and v:
            return v
    for env in ("COMPASS_USER_ID", "NAUTILUS_USER_ID"):
        v = os.environ.get(env)
        if v:
            return v
    return "u_local"


def _resolve_agent_type(agent_type: Optional[str], agent: Any) -> str:
    if agent_type:
        return agent_type
    for attr in ("agent_type", "role", "kind", "type"):
        v = getattr(agent, attr, None)
        if isinstance(v, str) and v:
            return v
    return "custom"


def _resolve_agent_id(agent: Any, agent_type: str) -> str:
    for attr in ("agent_id", "id", "name"):
        v = getattr(agent, attr, None)
        if isinstance(v, str) and v:
            return f"ag_{agent_type}_{v[:8].replace('-','_')}"
    return f"ag_{agent_type}_main"


def _safe_truncate(s: Any, n: int) -> str:
    if not isinstance(s, str):
        try:
            s = str(s)
        except Exception:
            return ""
    return s[:n]


def attach_memory(
    agent: Any,
    user_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    encrypt: bool = False,
    auto_recall: bool = True,
    auto_ingest: bool = True,
    stake_coupling: bool = False,
    base_url: Optional[str] = None,
) -> Any:
    """One-line attach · returns the same agent with .compass set."""
    user_id = _resolve_user_id(user_id, agent)
    agent_type = _resolve_agent_type(agent_type, agent)
    agent_id = _resolve_agent_id(agent, agent_type)

    client_kwargs = dict(
        user_id=user_id, agent_id=agent_id, agent_type=agent_type,
        encrypt_payload=encrypt,
    )
    if base_url:
        client_kwargs["base_url"] = base_url
    client = CompassClient(**client_kwargs)
    agent.compass = client

    # ---- on_action: pre-action recall (inject memory) ----
    if auto_recall and hasattr(agent, "on_action"):
        original_on_action = agent.on_action

        def _wrapped_on_action(prompt, **kw):
            try:
                hits = client.recall(query=str(prompt)[:200], top_k=3, cross_agent=True)
                if isinstance(hits, dict) and hits.get("hits"):
                    notes = "Relevant memory (cross-agent · compass):\n"
                    for h in hits["hits"][:3]:
                        name = h.get("name") or h.get("path", "?")
                        notes += f"  · {name}\n"
                    if "context" in kw and isinstance(kw["context"], str):
                        kw["context"] += "\n\n" + notes
                    else:
                        kw.setdefault("context", notes)
            except Exception:
                pass  # 不阻塞 agent 主流程
            return original_on_action(prompt, **kw)

        agent.on_action = _wrapped_on_action

    # ---- on_task_complete: ingest obs ----
    if auto_ingest and hasattr(agent, "on_task_complete"):
        original_on_complete = agent.on_task_complete

        def _wrapped_on_complete(task, outcome, **kw):
            result = original_on_complete(task, outcome, **kw)
            try:
                drift = "green"
                drift_signals = []
                if isinstance(outcome, dict):
                    if outcome.get("error"):
                        drift = "red"
                        drift_signals = [_safe_truncate(outcome["error"], 100)]
                    elif outcome.get("retried"):
                        drift = "yellow"
                client.ingest_obs(
                    name=f"{agent_type} · {_safe_truncate(task, 30)}",
                    description=_safe_truncate(outcome, 200),
                    body=_safe_truncate(outcome, 2000),
                    type_="bugfix" if drift == "red" else "feature",
                    drift=drift,
                    drift_signals=drift_signals,
                    extra_meta={"task": _safe_truncate(task, 100)},
                )
                if stake_coupling and drift == "red":
                    _trigger_stake_penalty(agent_id, user_id, drift_signals)
            except Exception as e:
                sys.stderr.write(f"[attach_memory] on_complete ingest fail: {e}\n")
            return result

        agent.on_task_complete = _wrapped_on_complete

    # ---- on_drift_signal: 显式漂移上报 ----
    def report_drift(severity: str, signal: str, context: str = ""):
        client.ingest_obs(
            name=f"⚠️ {agent_type} drift · {_safe_truncate(signal, 30)}",
            description=f"drift={severity} signal={signal}",
            body=context,
            type_="discovery",
            concept="gotcha",
            drift=severity,
            drift_signals=[signal],
        )
        if stake_coupling and severity == "red":
            _trigger_stake_penalty(agent_id, user_id, [signal])

    agent.report_drift = report_drift

    return agent


def _trigger_stake_penalty(agent_id: str, user_id: str, signals: list):
    """v0.9.5 · stake module 联动 · 暂存到 buffer · stake service 来 poll."""
    try:
        import json
        from datetime import datetime, timezone
        buf_dir = Path.home() / ".compass" / "stake_events"
        buf_dir.mkdir(parents=True, exist_ok=True)
        ev = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "drift_red",
            "agent_id": agent_id,
            "user_id": user_id,
            "signals": signals,
            "suggested_penalty_pct": 1.0,  # 1% locked stake
        }
        out = buf_dir / f"{int(datetime.now().timestamp())}.json"
        out.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[attach_memory] stake penalty buffer fail: {e}\n")


# ---- demo ----

class _DemoAgent:
    """duck-typed minimal agent · for selftest."""
    def __init__(self, role: str, user_id: str):
        self.role = role
        self.user_id = user_id
        self.id = f"demo_{role}"
    def on_action(self, prompt, **kw):
        return {"action": "demo_action", "prompt": prompt[:50], "ctx": kw.get("context","")}
    def on_task_complete(self, task, outcome, **kw):
        return {"completed": True, "task": task, "outcome": outcome}


def selftest():
    agent = _DemoAgent(role="strategy", user_id="u_demo")
    attach_memory(agent, base_url="https://compass.nautilus.social")

    # 模拟 action (会 inject memory)
    print("=== test 1: on_action with auto-recall ===")
    r = agent.on_action("V5 飞轮真转吗")
    print(r)

    # 模拟 task complete (会 ingest obs)
    print("\n=== test 2: on_task_complete with auto-ingest ===")
    r = agent.on_task_complete("评估飞轮", "结论: 60% 转 · 主要瓶颈在 fulfilled 比例")
    print(r)

    # 显式 drift report
    print("\n=== test 3: explicit drift report ===")
    agent.report_drift(severity="yellow", signal="第 2 次重做同一任务", context="第 1 次没看 anchor")
    print("drift reported")

    print("\n=== summary ===")
    print(f"agent.compass = {agent.compass}")
    print(f"compass user_id = {agent.compass.user_id}")
    print(f"compass agent_id = {agent.compass.agent_id}")


if __name__ == "__main__":
    selftest()

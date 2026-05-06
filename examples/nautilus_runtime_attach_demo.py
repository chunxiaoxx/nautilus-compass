"""compass × Nautilus agent runtime · #3 fusion · one-line attach demo.

完整 demo · 模拟一个 Nautilus agent 的 lifecycle:
  1. 创建 agent (duck-typed · 不需要真 nautilus-agent SDK)
  2. attach_memory(agent) · 一行接入
  3. agent 执行 task · on_action 自动 recall · on_task_complete 自动 ingest
  4. 验证: cross-agent memory federation 工作 (用 compass.recall 验证)
  5. drift 自审: agent 报错时自动写 drift=red obs

Run:
  python examples/nautilus_runtime_attach_demo.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))
from attach_memory import attach_memory


# ---- 模拟 Nautilus agent (duck-typed) ----

class MockNautilusAgent:
    """Mock of nautilus-agent SDK Agent · duck-typed for attach_memory.

    Real nautilus-agent (when SDK ships) will have richer interface;
    duck-typing means attach_memory works regardless.
    """

    def __init__(self, role: str, user_id: str, agent_id: str | None = None):
        self.role = role
        self.user_id = user_id
        self.id = agent_id or f"{role}_main"
        self._actions_taken = []

    def on_action(self, prompt: str, **kw) -> dict:
        """Called before each LLM action · prompt is the user input."""
        self._actions_taken.append(prompt)
        ctx = kw.get("context", "")
        # 真实 LLM call would go here · we just simulate
        if ctx:
            print(f"    [mock LLM with context] prompt={prompt[:30]} · ctx_len={len(ctx)}")
        return {"action": "simulated", "ctx_present": bool(ctx)}

    def on_task_complete(self, task: str, outcome, **kw) -> dict:
        """Called when agent finishes a task."""
        return {"completed": True, "task": task, "outcome": outcome}


def demo_agent_writes(role: str, user_id: str, n_tasks: int = 3):
    """Single-agent demo: create + attach + run n tasks · obs auto-write."""
    print(f"\n{'=' * 60}")
    print(f"Demo: agent role={role} · user={user_id}")
    print(f"{'=' * 60}")

    agent = MockNautilusAgent(role=role, user_id=user_id)
    attach_memory(
        agent,
        base_url="https://compass.nautilus.social",
        auto_recall=True,
        auto_ingest=True,
        stake_coupling=False,  # demo only · don't trigger real penalty
    )

    print(f"[1] Agent attached · compass={agent.compass.user_id}/{agent.compass.agent_id}")

    # Run tasks
    for i in range(n_tasks):
        prompt = f"task {i+1}: 分析 {role} 在第 {i+1} 步该做什么"
        print(f"\n[{i+2}] on_action: {prompt[:50]}")
        result_a = agent.on_action(prompt)

        # simulate doing the work
        outcome = f"完成 task {i+1} · 结果: 假设 OK"
        if i == 1:  # second task fails (demo drift=red path)
            outcome = {"error": "fake error · 模拟失败", "retried": True}

        print(f"    on_task_complete: outcome={str(outcome)[:60]}")
        result_b = agent.on_task_complete(prompt, outcome)

    print(f"\n[*] {role} agent did {len(agent._actions_taken)} actions")
    print(f"    compass.compass.replay_buffer would flush any buffered obs:")
    rb = agent.compass.replay_buffer()
    print(f"    {rb}")

    return agent


def demo_drift_report():
    """Demo of explicit drift report (agent self-audit)."""
    print(f"\n{'=' * 60}")
    print("Demo: explicit drift_report (agent admits a mistake)")
    print(f"{'=' * 60}")

    agent = MockNautilusAgent(role="critic", user_id="u_demo_chunx_2026")
    attach_memory(agent, stake_coupling=True)

    print("[*] Agent self-reports a drift signal:")
    agent.report_drift(
        severity="red",
        signal="第 3 次重做同一任务 · 没改方法",
        context="task=task_xyz · 第 1 次失败因为 missing field · 我没读 doc 直接重试",
    )
    print("    → buffer 写到 ~/.compass/stake_events/ (consumer 来 poll · 看 stake_drift_event_consumer.py)")

    return agent


def demo_cross_agent_query():
    """Verify federation: query compass · should see writes from multiple agents."""
    print(f"\n{'=' * 60}")
    print("Demo: cross-agent recall (verify federation works)")
    print(f"{'=' * 60}")

    # Use any of the previously attached agents · they all share user_id
    from compass_client import CompassClient
    client = CompassClient(
        user_id="u_demo_chunx_2026",
        agent_id="ag_query_only_session",
        agent_type="custom",
        base_url="https://compass.nautilus.social",
    )

    queries = [
        ("strategy", "OpenClaw 战略评估"),
        ("any agent", "task 完成"),
        ("drift", "red drift"),
        ("hermes", "loop 决策"),
    ]
    for label, q in queries:
        result = client.recall(query=q, top_k=3, cross_agent=True)
        hits = result.get("hits", [])
        print(f"  [{label}] q={q!r} · {len(hits)} hits")
        for h in hits[:2]:
            print(f"      score={h.get('score', '?')} · {h.get('name', h.get('path', '?'))}")

    print("\n[*] If federation works · queries return obs from all 3 agents (strategy · critic · etc)")
    print("[*] Same user_id · server side aggregates seamlessly · UI shows 'unified you'")


def main():
    print("compass × Nautilus runtime attach demo · #3 fusion")
    print(f"target: compass.nautilus.social · user: u_demo_chunx_2026")
    print(f"prerequisite: server has /v1/observations endpoint (v0.9.0+)")
    print()

    SHARED_USER = "u_demo_chunx_2026"

    # 3 agents · all sharing same user_id · auto-federate
    a1 = demo_agent_writes(role="strategy", user_id=SHARED_USER, n_tasks=3)
    a2 = demo_agent_writes(role="explorer", user_id=SHARED_USER, n_tasks=2)
    demo_drift_report()
    time.sleep(2)  # allow server to index
    demo_cross_agent_query()

    print(f"\n{'=' * 60}")
    print("Done. Real Nautilus agents would do this loop continuously · we showed 1 round.")
    print("Next step: see paper/STAKE_DRIFT_COUPLING.md for #4 fusion (economy-level).")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

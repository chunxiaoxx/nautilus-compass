"""Hermes → compass 接入示例.

Hermes 是开源 agent loop 框架 · 用户在使用 · 跑在 cloud server 上.
接入 compass 让 Hermes 每次决策/loop 行为可追溯 · 跨 agent 融合.

接入方式 (3 选 1 · 推荐 #1):
  1. MCP server (Hermes 通过 MCP 调 compass · 标准协议)
  2. A2A protocol (Hermes 作为 A2A agent · compass 作为 memory agent)
  3. Direct SDK (本文件)

实际位置:
  ~/hermes-agent/   ← Hermes 主代码 (开源)

集成点 (在 Hermes 每次循环结束):
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

from compass_client import CompassClient


def report_loop_iteration(
    client: CompassClient,
    iteration_id: str,
    goal: str,
    actions_taken: list[str],
    outcome: str,
    success: bool,
    error: str | None = None,
) -> dict:
    """Hermes 完成一次 loop iteration 后写入 compass."""
    drift = "green" if success else ("red" if error else "yellow")
    drift_signals = [error] if error else []
    name = f"Hermes loop · {goal[:30]}"
    description = f"iter {iteration_id} · goal『{goal[:50]}』· {len(actions_taken)} 动作 · {'success' if success else 'failed'}"
    body = f"""
## Goal
{goal}

## Actions
{chr(10).join(f"- {a}" for a in actions_taken)}

## Outcome
{outcome}
""".strip()
    if error:
        body += f"\n\n## Error\n{error}"
    return client.ingest_obs(
        name=name,
        description=description,
        body=body,
        type_="bugfix" if error else "feature",
        concept="problem-solution" if error else "how-it-works",
        drift=drift,
        drift_signals=drift_signals,
        extra_meta={
            "iteration_id": iteration_id,
            "n_actions": len(actions_taken),
            "success": success,
        },
    )


def report_drift_signal(
    client: CompassClient,
    detected_pattern: str,
    severity: str = "yellow",
    context: str = "",
) -> dict:
    """Hermes 检测到 anti-pattern (例如重复无效操作) 时主动告警."""
    return client.ingest_obs(
        name=f"⚠️ Hermes drift · {detected_pattern}",
        description=f"Hermes 自检测到 anti-pattern: {detected_pattern}",
        body=context,
        type_="discovery",
        concept="gotcha",
        drift=severity,
        drift_signals=[detected_pattern],
    )


def example_run():
    client = CompassClient(
        user_id="u_chunx",
        agent_id="ag_hermes_main_cloud",
        agent_type="hermes",
    )
    r1 = report_loop_iteration(
        client=client,
        iteration_id="2026-05-05-001",
        goal="检查 agent 改进队列 · 处理 P0 issue",
        actions_taken=[
            "fetch issue queue",
            "rank by stake_locked desc",
            "dispatch top-3 to executor",
            "wait for ack",
        ],
        outcome="3 个 P0 issue 派发 · 2 个完成 · 1 个 timeout",
        success=True,
    )
    print(r1)
    r2 = report_drift_signal(
        client=client,
        detected_pattern="同一 issue 第 3 次 dispatch · 上次失败原因未记录",
        severity="red",
        context="issue_id=hi-2331 · 5/3 5/4 5/5 各派发一次 · 都 timeout",
    )
    print(r2)


if __name__ == "__main__":
    example_run()

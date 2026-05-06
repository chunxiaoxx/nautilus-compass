"""OpenClaw → compass 接入示例.

OpenClaw 是开源战略分析 agent · 用户在使用.
接入 compass 让 OpenClaw 的所有评估结果跨 session/跨 agent 可被召回.

接入方式 (3 选 1 · 推荐 #1):
  1. MCP server (compass 当 OpenClaw 的 memory MCP · 见 sdk/mcp_adapter.py)
  2. A2A protocol (compass 作为 A2A memory agent · 见 sdk/a2a_adapter.py)
  3. Direct SDK (本文件 · 显式调 ingest_obs · 适合 fork 改造)

实际位置 (用户机器):
  ~/.openclaw/workspace/knowledge-base/   ← 知识库
  ~/openclaw/                              ← OpenClaw 主代码 (开源)

集成点 (在 OpenClaw 战略评估完成后调一次):
"""
import sys
from pathlib import Path

# 让示例独立可跑 · 加 sdk 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

from compass_client import CompassClient


def report_strategy_eval(
    client: CompassClient,
    project_name: str,
    eval_question: str,
    score_dimensions: dict[str, float],
    conclusion: str,
    drift: str = "green",
) -> dict:
    """OpenClaw 完成一次战略评估后 · 把结果写入 compass."""
    name = f"OpenClaw 战略评估 · {project_name}"
    description = f"用户问『{eval_question}』· OpenClaw 6 维评分 · 结论: {conclusion[:60]}"
    body = f"""
## 评估问题
{eval_question}

## 6 维评分
{chr(10).join(f"- {k}: {v:.2f}" for k, v in score_dimensions.items())}

## 结论
{conclusion}
""".strip()
    return client.ingest_obs(
        name=name,
        description=description,
        body=body,
        type_="decision",
        concept="trade-off",
        drift=drift,
        extra_meta={
            "project": project_name,
            "score_dimensions": score_dimensions,
        },
    )


def example_run():
    client = CompassClient(
        user_id="u_chunx",
        agent_id="ag_openclaw_strategy",
        agent_type="openclaw",
    )
    r = report_strategy_eval(
        client=client,
        project_name="Nautilus V5",
        eval_question="V5 飞轮真转吗",
        score_dimensions={
            "蓝图实现度": 0.65,
            "stake 真消耗": 0.72,
            "宪法 3 Yes": 0.83,
            "agent 主动率": 0.58,
            "fulfilled 比例": 0.41,
            "经济闭环": 0.55,
        },
        conclusion="飞轮 60% 转 · 主要瓶颈在 fulfilled 比例 (41%) · 建议 P0 修 stake 经济",
        drift="green",
    )
    print(r)


def example_recall_history():
    """召回 OpenClaw 历史评估 · 跨 agent 看用户其他 agent 的相关上下文."""
    client = CompassClient(
        user_id="u_chunx",
        agent_id="ag_openclaw_strategy",
        agent_type="openclaw",
    )
    hits = client.recall(
        query="V5 飞轮 stake fulfilled",
        cross_agent=True,  # ← 跨 agent · 也召回 Claude Code 写的相关 obs
    )
    print(hits)


if __name__ == "__main__":
    example_run()
    print("---")
    example_recall_history()

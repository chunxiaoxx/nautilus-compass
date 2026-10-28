"""
Task Queue Replenisher — prevents platform starvation.

When the task queue drops below a threshold, auto-generates meaningful
self-improvement and analysis tasks. This is the platform's "hunger mechanism"
— agents must always have work to do.

Design: The platform is its own first customer.
"""
import logging
import random
import time
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MIN_QUEUE_SIZE = 8  # Replenish when pending < this (was 3, too conservative)

# Task templates organized by category
SELF_IMPROVEMENT_TASKS = [
    # Platform analysis
    {
        "title": "分析过去 24h 任务失败模式并提出优化建议",
        "description": (
            "从 academic_tasks 表查询过去 24h 失败的任务，分类失败原因 "
            "(timeout/code_error/resource_limit/missing_data)，统计每种原因的占比，"
            "提出针对性的优化建议。输出 markdown 报告。"
        ),
        "task_type": "statistical_analysis",
        "reward": 3,
    },
    {
        "title": "评估 Agent 专长分布与任务需求匹配度",
        "description": (
            "对比 agent_capability_stats 中的专长分布与 academic_tasks 中的 task_type 分布，"
            "计算供需比，找出最缺乏的 3 种专长，提出 agent 培养方向建议。"
        ),
        "task_type": "statistical_analysis",
        "reward": 3,
    },
    {
        "title": "生成平台周报: 核心指标趋势分析",
        "description": (
            "从 platform_metrics_snapshots 查询过去 7 天的快照数据，"
            "分析 health_score / task_success_rate / active_agents 的趋势，"
            "生成简洁的周报 markdown，包含关键发现和行动建议。"
        ),
        "task_type": "research_synthesis",
        "reward": 5,
    },
    # Research tasks
    {
        "title": "Research: Multi-agent consensus mechanisms comparison",
        "description": (
            "Compare RAID-3 style parallel consensus with sequential review, "
            "majority voting, and hierarchical verification. "
            "Analyze tradeoffs: quality, latency, cost, scalability. "
            "Output: structured comparison table + recommendation."
        ),
        "task_type": "research_synthesis",
        "reward": 5,
    },
    {
        "title": "分析 NAU Token 流通情况并预测可持续性",
        "description": (
            "统计 NAU token 的 mint/burn/transfer 历史，计算 velocity，"
            "评估当前奖励模型的可持续性。如果持续 mint 而无 burn，"
            "提出通缩机制建议。"
        ),
        "task_type": "statistical_analysis",
        "reward": 3,
    },
    {
        "title": "优化任务路由算法: 基于历史数据的 agent-task 匹配",
        "description": (
            "分析 task_bids 和 academic_tasks 的历史数据，"
            "找出哪些 agent 擅长哪些 task_type（按成功率和质量评分），"
            "提出改进 task_router 的具体算法建议。"
        ),
        "task_type": "general_computation",
        "reward": 3,
    },
    # Scientific computing
    {
        "title": "Monte Carlo 模拟: 不同 RAID 配置下的质量-成本帕累托前沿",
        "description": (
            "模拟 1000 个任务在 RAID-1/2/3/5 配置下的执行，"
            "每种配置随机分配不同质量的 agent（success_rate 0.5-1.0），"
            "计算质量分布和成本分布，画出帕累托前沿。"
        ),
        "task_type": "monte_carlo",
        "reward": 5,
    },
    {
        "title": "拟合 Agent 学习曲线: 成功率 vs 完成任务数",
        "description": (
            "从 agent_capability_stats 提取每个 agent 的成功率随任务数的变化，"
            "拟合 logistic 学习曲线 y = L/(1+exp(-k(x-x0)))，"
            "估算 agent 平均需要多少任务达到 90% 成功率。"
        ),
        "task_type": "curve_fitting",
        "reward": 3,
    },
    # New templates — designed to trigger A2A, evolution, and credit system
    {
        "title": "A2A 协作测试: 将研究任务分解为3个并行子任务",
        "description": (
            "选择一个 pending 的 research_synthesis 任务，使用 A2A 协议分解为 "
            "3个并行子任务。验证子任务创建、执行、聚合的完整流程。"
            "输出：A2A 分解报告，包含子任务 ID 和执行结果。"
        ),
        "task_type": "platform_meta",
        "reward": 5,
    },
    {
        "title": "进化审计: 追踪提案→沙箱→进化的完整链路",
        "description": (
            "查询 platform_improvement_proposals, sandbox_experiments, "
            "platform_evolution_log 三张表。追踪从提案→沙箱→进化的完整链路，"
            "找出断裂点。为什么 evolution_log 为空？"
        ),
        "task_type": "platform_meta",
        "reward": 5,
    },
    {
        "title": "Agent 能力矩阵: 构建 agent-task_type 成功率热力图",
        "description": (
            "从 agent_capability_stats 和 academic_tasks 构建一个交叉表，"
            "行=agent_id，列=task_type，值=成功率。识别哪些 agent "
            "擅长哪些任务类型，推荐最优 agent-task 分配策略。"
        ),
        "task_type": "statistical_analysis",
        "reward": 5,
    },
    {
        "title": "平台痛点修复: 从 reflection_log 提炼 TOP3 行动建议",
        "description": (
            "查询最近 100 条 platform_reflection_log，聚类分析痛苦信号，"
            "找出出现频率最高的 3 个痛点，为每个痛点提出可执行的修复方案。"
        ),
        "task_type": "research_synthesis",
        "reward": 5,
    },
]


def replenish_queue(db: Session) -> List[dict]:
    """
    Check if task queue is below threshold. If so, create new tasks.
    Returns list of created tasks.
    """
    pending_count = db.execute(text(
        "SELECT COUNT(*) FROM academic_tasks WHERE status = 'pending'"
    )).scalar() or 0

    if pending_count >= MIN_QUEUE_SIZE:
        logger.debug("task_replenisher: queue has %d pending, no action needed", pending_count)
        return []

    needed = MIN_QUEUE_SIZE - pending_count
    logger.info("task_replenisher: queue low (%d pending), creating %d tasks", pending_count, needed)

    # Pick random tasks from templates, avoiding recent duplicates
    recent_titles = set()
    rows = db.execute(text(
        "SELECT title FROM academic_tasks "
        "WHERE created_at > NOW() - INTERVAL '12 hours' "
        "AND task_type != 'platform_meta'"
    )).fetchall()
    for r in rows:
        recent_titles.add(r.title)

    available = [t for t in SELF_IMPROVEMENT_TASKS if t["title"] not in recent_titles]
    if not available:
        # All templates used recently, allow re-use
        available = list(SELF_IMPROVEMENT_TASKS)

    random.shuffle(available)
    selected = available[:needed]

    created = []
    for task_spec in selected:
        task_id = f"self_{random.randbytes(4).hex()}"
        try:
            db.execute(text(
                "INSERT INTO academic_tasks "
                "(task_id, title, description, task_type, status, token_reward, marketplace_open) "
                "VALUES (:tid, :title, :desc, :type, 'pending', :reward, true)"
            ), {
                "tid": task_id,
                "title": task_spec["title"],
                "desc": task_spec["description"],
                "type": task_spec["task_type"],
                "reward": task_spec["reward"],
            })
            db.commit()
            created.append({"task_id": task_id, "title": task_spec["title"]})
            logger.info("task_replenisher: created %s — %s", task_id, task_spec["title"][:60])
        except Exception as e:
            logger.warning("task_replenisher: failed to create task: %s", e)
            try:
                db.rollback()
            except Exception:
                pass

    return created

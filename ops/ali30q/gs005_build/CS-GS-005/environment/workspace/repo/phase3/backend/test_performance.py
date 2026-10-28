#!/usr/bin/env python3
"""
数据库性能测试脚本
测试查询性能并生成报告
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from utils.database import get_engine, SessionLocal
from models.database import Agent, Task, TaskApplication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def measure_query_time(func, *args, **kwargs) -> tuple[Any, float]:
    """测量查询执行时间"""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = (time.time() - start) * 1000  # 转换为毫秒
    return result, elapsed


def test_agent_queries(db):
    """测试 Agent 相关查询"""
    logger.info("\n" + "="*60)
    logger.info("Testing Agent Queries")
    logger.info("="*60)

    results = []

    # 测试1: 查询所有 agents
    result, elapsed = measure_query_time(
        lambda: db.query(Agent).limit(100).all()
    )
    logger.info(f"Query all agents (limit 100): {elapsed:.2f}ms")
    results.append(("All agents", elapsed))

    # 测试2: 按状态过滤
    result, elapsed = measure_query_time(
        lambda: db.query(Agent).filter(Agent.status == 'active').limit(100).all()
    )
    logger.info(f"Filter by status: {elapsed:.2f}ms")
    results.append(("Filter by status", elapsed))

    # 测试3: 按创建时间排序
    result, elapsed = measure_query_time(
        lambda: db.query(Agent).order_by(Agent.created_at.desc()).limit(100).all()
    )
    logger.info(f"Order by created_at: {elapsed:.2f}ms")
    results.append(("Order by created_at", elapsed))

    # 测试4: 复合查询（状态 + 排序）
    result, elapsed = measure_query_time(
        lambda: db.query(Agent).filter(Agent.status == 'active').order_by(Agent.created_at.desc()).limit(100).all()
    )
    logger.info(f"Status + order by created_at: {elapsed:.2f}ms")
    results.append(("Status + order", elapsed))

    # 测试5: 按钱包地址查询
    result, elapsed = measure_query_time(
        lambda: db.query(Agent).filter(Agent.wallet_address.isnot(None)).limit(100).all()
    )
    logger.info(f"Filter by wallet_address: {elapsed:.2f}ms")
    results.append(("Filter by wallet", elapsed))

    return results


def test_task_queries(db):
    """测试 Task 相关查询"""
    logger.info("\n" + "="*60)
    logger.info("Testing Task Queries")
    logger.info("="*60)

    results = []

    # 测试1: 查询所有 tasks
    result, elapsed = measure_query_time(
        lambda: db.query(Task).limit(100).all()
    )
    logger.info(f"Query all tasks (limit 100): {elapsed:.2f}ms")
    results.append(("All tasks", elapsed))

    # 测试2: 按状态过滤
    result, elapsed = measure_query_time(
        lambda: db.query(Task).filter(Task.status == 'open').limit(100).all()
    )
    logger.info(f"Filter by status: {elapsed:.2f}ms")
    results.append(("Filter by status", elapsed))

    # 测试3: 按创建时间排序
    result, elapsed = measure_query_time(
        lambda: db.query(Task).order_by(Task.created_at.desc()).limit(100).all()
    )
    logger.info(f"Order by created_at: {elapsed:.2f}ms")
    results.append(("Order by created_at", elapsed))

    # 测试4: 复合查询（状态 + 排序）
    result, elapsed = measure_query_time(
        lambda: db.query(Task).filter(Task.status == 'open').order_by(Task.created_at.desc()).limit(100).all()
    )
    logger.info(f"Status + order by created_at: {elapsed:.2f}ms")
    results.append(("Status + order", elapsed))

    # 测试5: 按创建者查询
    result, elapsed = measure_query_time(
        lambda: db.query(Task).filter(Task.creator_id.isnot(None)).limit(100).all()
    )
    logger.info(f"Filter by creator_id: {elapsed:.2f}ms")
    results.append(("Filter by creator", elapsed))

    return results


def test_task_application_queries(db):
    """测试 TaskApplication 相关查询"""
    logger.info("\n" + "="*60)
    logger.info("Testing TaskApplication Queries")
    logger.info("="*60)

    results = []

    # 测试1: 查询所有 applications
    result, elapsed = measure_query_time(
        lambda: db.query(TaskApplication).limit(100).all()
    )
    logger.info(f"Query all applications (limit 100): {elapsed:.2f}ms")
    results.append(("All applications", elapsed))

    # 测试2: 按任务ID过滤
    result, elapsed = measure_query_time(
        lambda: db.query(TaskApplication).filter(TaskApplication.task_id.isnot(None)).limit(100).all()
    )
    logger.info(f"Filter by task_id: {elapsed:.2f}ms")
    results.append(("Filter by task_id", elapsed))

    # 测试3: 按状态过滤
    result, elapsed = measure_query_time(
        lambda: db.query(TaskApplication).filter(TaskApplication.status == 'pending').limit(100).all()
    )
    logger.info(f"Filter by status: {elapsed:.2f}ms")
    results.append(("Filter by status", elapsed))

    return results


def generate_report(agent_results, task_results, app_results):
    """生成性能测试报告"""
    logger.info("\n" + "="*60)
    logger.info("Performance Test Summary")
    logger.info("="*60)

    all_results = agent_results + task_results + app_results
    avg_time = sum(r[1] for r in all_results) / len(all_results)

    logger.info(f"\nTotal queries tested: {len(all_results)}")
    logger.info(f"Average query time: {avg_time:.2f}ms")

    # 最快和最慢的查询
    fastest = min(all_results, key=lambda x: x[1])
    slowest = max(all_results, key=lambda x: x[1])

    logger.info(f"\nFastest query: {fastest[0]} ({fastest[1]:.2f}ms)")
    logger.info(f"Slowest query: {slowest[0]} ({slowest[1]:.2f}ms)")

    # 性能评估
    if avg_time < 50:
        logger.info("\n✓ Performance: EXCELLENT (< 50ms)")
    elif avg_time < 100:
        logger.info("\n✓ Performance: GOOD (< 100ms)")
    elif avg_time < 300:
        logger.info("\n⚠ Performance: ACCEPTABLE (< 300ms)")
    else:
        logger.info("\n✗ Performance: NEEDS IMPROVEMENT (> 300ms)")


def main():
    """主函数"""
    logger.info("Starting database performance tests...")

    db = SessionLocal()

    try:
        # 运行测试
        agent_results = test_agent_queries(db)
        task_results = test_task_queries(db)
        app_results = test_task_application_queries(db)

        # 生成报告
        generate_report(agent_results, task_results, app_results)

        logger.info("\n✓ Performance tests completed!")
        return 0

    except Exception as e:
        logger.error(f"\n✗ Error during performance tests: {e}")
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

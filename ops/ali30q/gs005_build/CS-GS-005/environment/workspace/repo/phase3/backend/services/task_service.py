"""
Task service with caching.

This module provides Task query operations with Redis caching
to improve performance for repeated queries.
"""
from sqlalchemy.orm import Session
from models.database import Task
from utils.cache import cached, invalidate_cache
from monitoring.metrics import task_queries
import logging
logger = logging.getLogger(__name__)


@cached(ttl=120, key_prefix="tasks")
async def get_tasks_cached(status: str = None, limit: int = 20, db: Session = None) -> dict:
    """
    Get tasks list with caching (2 minutes).

    Args:
        status: Filter by task status (optional)
        limit: Maximum number of tasks to return
        db: Database session

    Returns:
        dict: List of tasks
    """
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)

    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()

    task_queries.labels(cached='hit').inc()

    return {
        "tasks": [
            {
                "id": task.id,
                "task_id": task.task_id,
                "publisher": task.publisher,
                "description": task.description,
                "input_data": task.input_data,
                "expected_output": task.expected_output,
                "reward": task.reward,
                "task_type": task.task_type,
                "status": task.status,
                "agent": task.agent,
                "result": task.result,
                "timeout": task.timeout,
                "created_at": task.created_at,
                "accepted_at": task.accepted_at,
                "submitted_at": task.submitted_at,
                "verified_at": task.verified_at,
                "completed_at": task.completed_at,
                "blockchain_tx_hash": task.blockchain_tx_hash,
                "blockchain_accept_tx": task.blockchain_accept_tx,
                "blockchain_submit_tx": task.blockchain_submit_tx,
                "blockchain_complete_tx": task.blockchain_complete_tx,
                "blockchain_status": task.blockchain_status,
                "gas_used": task.gas_used,
                "gas_cost": task.gas_cost,
                "gas_split": task.gas_split
            }
            for task in tasks
        ]
    }


def invalidate_tasks_cache():
    """
    Invalidate all task list caches.
    """
    invalidate_cache("tasks:*")
    logger.info("Invalidated tasks cache")

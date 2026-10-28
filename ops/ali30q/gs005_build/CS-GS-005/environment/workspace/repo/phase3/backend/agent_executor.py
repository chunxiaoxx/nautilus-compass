"""
Agent Executor - Integrates agent-engine with backend API.

This module bridges the gap between the FastAPI backend and the agent-engine,
enabling automatic task execution by agents.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.database import Task, Agent, TaskStatus
from agent_engine.core.engine import AgentEngine, AgentState
from agent_engine.executors.code_executor import CodeExecutor
from agent_engine.executors.data_executor import DataExecutor
from agent_engine.executors.compute_executor import ComputeExecutor
from blockchain import get_blockchain_service
from automation_metrics import (
    record_task_execution_start,
    record_task_execution_complete,
    record_task_execution_failed
)
from websocket_server import emit_task_executing, emit_task_execution_complete

logger = logging.getLogger(__name__)

# Global agent engines cache
_agent_engines: Dict[int, AgentEngine] = {}


def get_agent_engine(agent_id: int) -> AgentEngine:
    """
    Get or create agent engine for given agent ID.

    Args:
        agent_id: Agent ID

    Returns:
        AgentEngine instance
    """
    if agent_id not in _agent_engines:
        _agent_engines[agent_id] = AgentEngine(
            agent_id=agent_id,
            max_concurrent_tasks=3
        )
        logger.info(f"Created new AgentEngine for agent {agent_id}")

    return _agent_engines[agent_id]


async def execute_task_by_agent(
    task_id: int,
    agent_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Execute task using agent engine.

    This is the main entry point for agent task execution.

    Args:
        task_id: Task ID
        agent_id: Agent ID
        db: Database session

    Returns:
        Execution result

    Raises:
        RuntimeError: If execution fails
    """
    logger.info(f"Agent {agent_id} starting execution of task {task_id}")

    # Get task and agent from database
    # Note: SQLAlchemy sessions are NOT thread-safe, so we keep these synchronous
    # The queries are fast (~5ms each), so parallel execution provides minimal benefit
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    # Verify task is in ACCEPTED state
    if task.status != TaskStatus.ACCEPTED:
        raise ValueError(f"Task {task_id} is not in ACCEPTED state")

    # Get agent engine
    engine = get_agent_engine(agent_id)

    # Prepare task data for agent engine
    task_data = {
        "task_id": task.id,
        "task_type": task.task_type or "CODE",  # Default to CODE
        "description": task.description,
        "input_data": task.requirements,  # Use requirements as input
        "expected_output": None  # No expected output for real tasks
    }

    try:
        # Record execution start
        record_task_execution_start(agent_id)

        # Emit WebSocket event
        try:
            await emit_task_executing({
                'task_id': task.id,
                'agent': str(agent_id),
                'status': 'executing'
            })
        except Exception:
            pass  # WebSocket is non-critical

        # Execute task using agent engine
        start_time = datetime.now(timezone.utc)

        # Create agent state
        state = AgentState(**task_data, started_at=start_time)

        # Run through execution graph
        result_state = await engine.graph.ainvoke(state)

        end_time = datetime.now(timezone.utc)
        execution_time = (end_time - start_time).total_seconds()

        # Check if execution was successful
        if result_state.error:
            logger.error(f"Task {task_id} execution failed: {result_state.error}")

            # Record failure metrics
            task_type_str = task_data["task_type"]
            record_task_execution_failed(agent_id, task_type_str, "execution_error")

            # Update task status to FAILED
            task.status = TaskStatus.FAILED
            task.result = result_state.error
            db.commit()

            # Update agent statistics
            agent.failed_tasks += 1
            db.commit()

            return {
                "success": False,
                "error": result_state.error,
                "execution_time": execution_time
            }

        # Execution successful
        logger.info(f"Task {task_id} execution completed successfully")

        # Record success metrics
        task_type_str = task_data["task_type"]
        record_task_execution_complete(agent_id, task_type_str, execution_time)

        # Submit result to blockchain
        blockchain_service = get_blockchain_service()
        try:
            tx_hash = await blockchain_service.submit_task_result(
                task_id=task.id,
                result_hash=result_state.result[:64] if result_state.result else "0" * 64
            )

            # Update task status to SUBMITTED
            task.status = TaskStatus.SUBMITTED
            task.result = result_state.result
            task.blockchain_submit_tx = tx_hash
            task.submitted_at = end_time
            db.commit()

            logger.info(f"Task {task_id} result submitted to blockchain: {tx_hash}")

        except Exception as e:
            logger.error(f"Failed to submit result to blockchain: {e}")
            # Still mark as completed locally
            task.status = TaskStatus.SUBMITTED
            task.result = result_state.result
            task.submitted_at = end_time
            db.commit()

        # Update agent statistics
        agent.completed_tasks += 1
        agent.current_tasks = max(0, agent.current_tasks - 1)
        db.commit()

        # Emit execution complete event
        try:
            await emit_task_execution_complete({
                'task_id': task.id,
                'agent': str(agent_id),
                'success': True,
                'execution_time': execution_time
            })
        except Exception:
            pass

        return {
            "success": True,
            "result": result_state.result,
            "execution_time": execution_time,
            "blockchain_tx": task.blockchain_submit_tx,
            "logs": result_state.logs
        }

    except Exception as e:
        logger.error(f"Task {task_id} execution error: {e}", exc_info=True)

        # Update task status to FAILED
        task.status = TaskStatus.FAILED
        task.result = str(e)
        db.commit()

        # Update agent statistics
        agent.failed_tasks += 1
        agent.current_tasks = max(0, agent.current_tasks - 1)
        db.commit()

        # Emit execution failure event
        try:
            await emit_task_execution_complete({
                'task_id': task.id,
                'agent': str(agent_id),
                'success': False,
                'error': str(e)
            })
        except Exception:
            pass

        raise RuntimeError(f"Task execution failed: {str(e)}")


async def submit_task_to_queue(
    task_id: int,
    agent_id: int,
    db: Session
) -> str:
    """
    Submit task to execution queue.

    This creates a background task that will execute the task asynchronously.

    Args:
        task_id: Task ID
        agent_id: Agent ID
        db: Database session

    Returns:
        Task queue ID
    """
    logger.info(f"Submitting task {task_id} to execution queue for agent {agent_id}")

    # Create background task
    asyncio.create_task(execute_task_by_agent(task_id, agent_id, db))

    return f"task_{task_id}_agent_{agent_id}"


async def get_agent_status(agent_id: int) -> Dict[str, Any]:
    """
    Get agent execution status.

    Args:
        agent_id: Agent ID

    Returns:
        Agent status information
    """
    if agent_id not in _agent_engines:
        return {
            "agent_id": agent_id,
            "status": "idle",
            "current_tasks": 0,
            "max_concurrent_tasks": 3,
            "available_capacity": 3
        }

    engine = _agent_engines[agent_id]
    current_tasks = len(engine.current_tasks)

    return {
        "agent_id": agent_id,
        "status": "active" if current_tasks > 0 else "idle",
        "current_tasks": current_tasks,
        "max_concurrent_tasks": engine.max_concurrent_tasks,
        "available_capacity": engine.max_concurrent_tasks - current_tasks
    }


def cleanup_agent_engine(agent_id: int):
    """
    Cleanup agent engine resources.

    Args:
        agent_id: Agent ID
    """
    if agent_id in _agent_engines:
        del _agent_engines[agent_id]
        logger.info(f"Cleaned up AgentEngine for agent {agent_id}")

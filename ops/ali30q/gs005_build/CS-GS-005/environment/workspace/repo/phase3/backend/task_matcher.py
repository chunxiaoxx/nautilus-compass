"""
Task Matcher - Intelligent task matching and auto-assignment.

Matches tasks to suitable agents based on:
- Agent specialties
- Agent reputation
- Agent availability
- Task requirements
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.database import Task, Agent, TaskStatus, TaskType
from agent_executor import submit_task_to_queue
from automation_metrics import (
    record_task_auto_assigned,
    record_task_assignment_failed
)

logger = logging.getLogger(__name__)


async def match_task_to_agents(
    task_id: int,
    db: Session,
    max_matches: int = 5
) -> List[Dict[str, Any]]:
    """
    Match task to suitable agents.

    Args:
        task_id: Task ID
        db: Database session
        max_matches: Maximum number of agents to return

    Returns:
        List of matched agents with scores
    """
    logger.info(f"Matching task {task_id} to agents...")

    # Get task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        logger.error(f"Task {task_id} not found")
        return []

    # Get all available agents
    agents = db.query(Agent).filter(
        Agent.current_tasks < 3  # Has capacity
    ).all()

    if not agents:
        logger.warning("No available agents found")
        return []

    # Score each agent
    scored_agents = []
    for agent in agents:
        score = calculate_agent_score(task, agent)
        scored_agents.append({
            "agent_id": agent.agent_id,
            "agent": agent,
            "score": score,
            "reputation": agent.reputation,
            "current_tasks": agent.current_tasks,
            "completed_tasks": agent.completed_tasks,
            "specialties": agent.specialties
        })

    # Sort by score (descending)
    scored_agents.sort(key=lambda x: x["score"], reverse=True)

    # Return top matches
    top_matches = scored_agents[:max_matches]

    logger.info(f"Found {len(top_matches)} matching agents for task {task_id}")
    for match in top_matches:
        logger.info(f"  Agent {match['agent_id']}: score={match['score']:.2f}, "
                   f"reputation={match['reputation']}, "
                   f"current_tasks={match['current_tasks']}")

    return top_matches


def calculate_agent_score(task: Task, agent: Agent) -> float:
    """
    Calculate matching score between task and agent.

    Scoring factors:
    - Specialty match: 0-40 points
    - Reputation: 0-30 points
    - Availability: 0-20 points
    - Success rate: 0-10 points

    Args:
        task: Task object
        agent: Agent object

    Returns:
        Score (0-100)
    """
    score = 0.0

    # 1. Specialty match (0-40 points)
    if agent.specialties:
        agent_specialties = set(agent.specialties.split(","))
        task_type = task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type)

        if task_type in agent_specialties:
            score += 40  # Perfect match
        elif "ALL" in agent_specialties:
            score += 20  # General agent
        else:
            # Partial match for related types
            related_types = {
                "CODE": ["DATA", "COMPUTE"],
                "DATA": ["CODE", "COMPUTE"],
                "COMPUTE": ["CODE", "DATA"]
            }
            if task_type in related_types:
                for related in related_types[task_type]:
                    if related in agent_specialties:
                        score += 10
                        break

    # 2. Reputation (0-30 points)
    # Normalize reputation (assume max 1000)
    reputation_score = min(agent.reputation / 1000.0 * 30, 30)
    score += reputation_score

    # 3. Availability (0-20 points)
    # Fewer current tasks = higher score
    availability_score = (3 - agent.current_tasks) / 3.0 * 20
    score += availability_score

    # 4. Success rate (0-10 points)
    # Defensive: completed_tasks / failed_tasks may be None for freshly-registered agents
    completed = agent.completed_tasks or 0
    failed = agent.failed_tasks or 0
    total_tasks = completed + failed
    if total_tasks > 0:
        success_rate = completed / total_tasks
        score += success_rate * 10

    return score


async def auto_assign_task(
    task_id: int,
    db: Session,
    min_score: float = 50.0
) -> Optional[int]:
    """
    Automatically assign task to best matching agent.

    Args:
        task_id: Task ID
        db: Database session
        min_score: Minimum score required for assignment

    Returns:
        Agent ID if assigned, None otherwise
    """
    logger.info(f"Auto-assigning task {task_id}...")

    # Get task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        logger.error(f"Task {task_id} not found")
        return None

    # Check if task is open
    if task.status != TaskStatus.OPEN:
        logger.warning(f"Task {task_id} is not open (status: {task.status})")
        return None

    # Match agents
    matches = await match_task_to_agents(task_id, db, max_matches=1)

    if not matches:
        logger.warning(f"No matching agents found for task {task_id}")
        record_task_assignment_failed("no_agents_available")
        return None

    best_match = matches[0]

    # Check minimum score
    if best_match["score"] < min_score:
        logger.warning(f"Best match score {best_match['score']:.2f} below minimum {min_score}")
        record_task_assignment_failed("score_too_low")
        return None

    agent = best_match["agent"]

    try:
        # Update task status
        task.status = TaskStatus.ACCEPTED
        task.agent = agent.owner
        db.commit()

        logger.info(f"✅ Task {task_id} auto-assigned to agent {agent.agent_id} "
                   f"(score: {best_match['score']:.2f})")

        # Record success metrics
        task_type_str = task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type)
        record_task_auto_assigned(task_type_str, best_match["score"])

        # Submit to execution queue
        queue_id = await submit_task_to_queue(task.id, agent.agent_id, db)
        logger.info(f"🚀 Task {task.id} submitted to execution queue: {queue_id}")

        # Update agent current tasks
        agent.current_tasks += 1
        db.commit()

        return agent.agent_id

    except Exception as e:
        logger.error(f"❌ Failed to auto-assign task {task_id}: {e}", exc_info=True)
        db.rollback()
        return None


async def check_and_assign_tasks(db: Session):
    """
    Check for unassigned tasks and auto-assign them.

    This function is called periodically by the scheduler.

    Args:
        db: Database session
    """
    logger.info("Checking for unassigned tasks...")

    try:
        # Get all open tasks
        open_tasks = db.query(Task).filter(
            Task.status == TaskStatus.OPEN
        ).all()

        if not open_tasks:
            logger.info("No open tasks found")
            return

        logger.info(f"Found {len(open_tasks)} open tasks")

        # Try to assign each task
        assigned_count = 0
        for task in open_tasks:
            agent_id = await auto_assign_task(task.id, db)
            if agent_id:
                assigned_count += 1

        logger.info(f"✅ Auto-assigned {assigned_count}/{len(open_tasks)} tasks")

    except Exception as e:
        logger.error(f"❌ Error in check_and_assign_tasks: {e}", exc_info=True)


async def get_agent_recommendations(
    task_id: int,
    db: Session,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get agent recommendations for a task.

    This is used by the frontend to show recommended agents.

    Args:
        task_id: Task ID
        db: Database session
        limit: Maximum number of recommendations

    Returns:
        List of recommended agents with details
    """
    matches = await match_task_to_agents(task_id, db, max_matches=limit)

    recommendations = []
    for match in matches:
        agent = match["agent"]
        recommendations.append({
            "agent_id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
            "reputation": agent.reputation,
            "specialties": agent.specialties,
            "completed_tasks": agent.completed_tasks,
            "failed_tasks": agent.failed_tasks,
            "current_tasks": agent.current_tasks,
            "match_score": match["score"],
            "available": agent.current_tasks < 3
        })

    return recommendations

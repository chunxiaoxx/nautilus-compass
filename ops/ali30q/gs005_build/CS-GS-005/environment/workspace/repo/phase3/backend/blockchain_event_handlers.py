"""
Blockchain Event Handlers

Handles events from blockchain smart contracts.
"""
import logging
import time
from typing import Dict, Any
from sqlalchemy.orm import Session

from models.database import Task, Agent, Reward, TaskStatus
from utils.database import get_db
from agent_executor import submit_task_to_queue
from automation_metrics import record_blockchain_event

logger = logging.getLogger(__name__)


async def handle_task_published(event: Dict[str, Any]):
    """
    Handle TaskPublished event from blockchain.

    Event data:
    - taskId: Task ID on blockchain
    - publisher: Publisher address
    - reward: Reward amount in Wei
    - timestamp: Block timestamp

    Args:
        event: Event data from blockchain
    """
    start_time = time.time()
    success = False
    error_type = None

    logger.info(f"📢 TaskPublished event received: {event}")

    try:
        task_id = event.get("taskId")
        publisher = event.get("publisher")
        reward = event.get("reward")

        # Get database session
        db = next(get_db())

        # Find task in database by blockchain task ID
        task = db.query(Task).filter(Task.task_id == task_id).first()

        if task:
            # Update task with blockchain confirmation
            task.blockchain_status = "published"
            db.commit()
            logger.info(f"✅ Task {task_id} marked as published on blockchain")
            success = True
        else:
            logger.warning(f"⚠️  Task {task_id} not found in database")
            error_type = "task_not_found"

        db.close()

    except Exception as e:
        logger.error(f"❌ Error handling TaskPublished event: {e}", exc_info=True)
        error_type = "exception"
    finally:
        duration = time.time() - start_time
        record_blockchain_event("TaskPublished", success, duration, error_type)


async def handle_task_accepted(event: Dict[str, Any]):
    """
    Handle TaskAccepted event from blockchain.

    Event data:
    - taskId: Task ID on blockchain
    - agent: Agent address
    - timestamp: Block timestamp

    This event triggers automatic task execution.

    Args:
        event: Event data from blockchain
    """
    logger.info(f"📢 TaskAccepted event received: {event}")

    try:
        task_id = event.get("taskId")
        agent_address = event.get("agent")

        # Get database session
        db = next(get_db())

        # Find task in database
        task = db.query(Task).filter(Task.task_id == task_id).first()

        if not task:
            logger.warning(f"⚠️  Task {task_id} not found in database")
            db.close()
            return

        # Find agent by address
        agent = db.query(Agent).filter(Agent.owner == agent_address).first()

        if not agent:
            logger.warning(f"⚠️  Agent {agent_address} not found in database")
            db.close()
            return

        # Update task status if not already accepted
        if task.status == TaskStatus.OPEN:
            task.status = TaskStatus.ACCEPTED
            task.agent = agent_address
            db.commit()
            logger.info(f"✅ Task {task_id} marked as accepted by agent {agent.agent_id}")

            # Trigger automatic execution
            try:
                queue_id = await submit_task_to_queue(task.id, agent.agent_id, db)
                logger.info(f"🚀 Task {task.id} submitted to execution queue: {queue_id}")

                # Update agent current tasks
                agent.current_tasks += 1
                db.commit()

            except Exception as e:
                logger.error(f"❌ Failed to submit task {task.id} to execution queue: {e}")

        db.close()

    except Exception as e:
        logger.error(f"❌ Error handling TaskAccepted event: {e}", exc_info=True)


async def handle_task_completed(event: Dict[str, Any]):
    """
    Handle TaskCompleted event from blockchain.

    Event data:
    - taskId: Task ID on blockchain
    - agent: Agent address
    - reward: Reward amount distributed
    - timestamp: Block timestamp

    This event triggers reward distribution.

    Args:
        event: Event data from blockchain
    """
    logger.info(f"📢 TaskCompleted event received: {event}")

    try:
        task_id = event.get("taskId")
        agent_address = event.get("agent")
        reward_amount = event.get("reward")

        # Get database session
        db = next(get_db())

        # Find task in database
        task = db.query(Task).filter(Task.task_id == task_id).first()

        if not task:
            logger.warning(f"⚠️  Task {task_id} not found in database")
            db.close()
            return

        # Find agent
        agent = db.query(Agent).filter(Agent.owner == agent_address).first()

        if not agent:
            logger.warning(f"⚠️  Agent {agent_address} not found in database")
            db.close()
            return

        # Update task status
        if task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.blockchain_status = "completed"
            db.commit()
            logger.info(f"✅ Task {task_id} marked as completed on blockchain")

        # Create or update reward record
        reward = db.query(Reward).filter(
            Reward.task_id == task.id,
            Reward.agent_id == agent.agent_id
        ).first()

        if not reward:
            reward = Reward(
                task_id=task.id,
                agent_id=agent.agent_id,
                amount=reward_amount,
                status="Distributed",
                blockchain_tx_hash=event.get("transactionHash")
            )
            db.add(reward)
            logger.info(f"💰 Reward created for agent {agent.agent_id}: {reward_amount} Wei")
        else:
            reward.status = "Distributed"
            reward.amount = reward_amount
            logger.info(f"💰 Reward updated for agent {agent.agent_id}: {reward_amount} Wei")

        # Update agent statistics
        agent.total_earnings += reward_amount
        agent.current_tasks = max(0, agent.current_tasks - 1)

        db.commit()
        db.close()

        logger.info(f"✅ Task {task_id} completed and reward distributed")

    except Exception as e:
        logger.error(f"❌ Error handling TaskCompleted event: {e}", exc_info=True)


# Additional event handlers can be added here

async def handle_task_disputed(event: Dict[str, Any]):
    """
    Handle TaskDisputed event from blockchain.

    Args:
        event: Event data from blockchain
    """
    logger.info(f"📢 TaskDisputed event received: {event}")

    try:
        task_id = event.get("taskId")
        reason = event.get("reason")

        db = next(get_db())

        task = db.query(Task).filter(Task.task_id == task_id).first()

        if task:
            task.status = TaskStatus.DISPUTED
            task.blockchain_status = "disputed"
            db.commit()
            logger.info(f"⚠️  Task {task_id} marked as disputed: {reason}")

        db.close()

    except Exception as e:
        logger.error(f"❌ Error handling TaskDisputed event: {e}", exc_info=True)


async def handle_agent_registered(event: Dict[str, Any]):
    """
    Handle AgentRegistered event from blockchain.

    Args:
        event: Event data from blockchain
    """
    logger.info(f"📢 AgentRegistered event received: {event}")

    try:
        agent_address = event.get("agent")
        agent_id = event.get("agentId")

        db = next(get_db())

        agent = db.query(Agent).filter(Agent.owner == agent_address).first()

        if agent:
            agent.blockchain_registered = True
            agent.blockchain_address = agent_address
            db.commit()
            logger.info(f"✅ Agent {agent_id} confirmed registered on blockchain")

        db.close()

    except Exception as e:
        logger.error(f"❌ Error handling AgentRegistered event: {e}", exc_info=True)

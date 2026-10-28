"""
Task API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import os

from models.database import Task, TaskType, TaskStatus, User, Agent
from utils.database import get_db
from utils.auth import get_current_user, get_current_agent, get_current_user_or_agent
from blockchain import get_blockchain_service
from agent_executor import submit_task_to_queue, execute_task_by_agent, get_agent_status
from utils.db_pool import get_db_pool
from memory.agent_memory import get_memory_system
from memory.reflection_system import get_reflection_system
from services.task_service import get_tasks_cached, invalidate_tasks_cache
from services.survival_service import SurvivalService
from services.anti_cheat_service import AntiCheatService

router = APIRouter()
logger = logging.getLogger(__name__)

# Check if we're in testing mode
TESTING = os.getenv("TESTING", "false").lower() == "true"

# Create limiter with disabled state for testing
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


class TaskCreate(BaseModel):
    """Task creation request."""
    description: str
    input_data: Optional[str] = None
    expected_output: Optional[str] = None
    reward: int  # Wei
    task_type: TaskType
    timeout: int  # Seconds

    class Config:
        json_schema_extra = {
            "example": {
                "description": "开发一个用户认证 REST API 端点",
                "input_data": "要求: JWT tokens, bcrypt 加密, PostgreSQL 数据库",
                "expected_output": "可工作的 API 端点及测试代码",
                "reward": 1000000000000000000,
                "task_type": "CODE",
                "timeout": 86400
            }
        }


class TaskResponse(BaseModel):
    """Task response."""
    id: int
    task_id: str
    publisher: str
    description: str
    input_data: Optional[str]
    expected_output: Optional[str]
    reward: int
    task_type: TaskType
    status: TaskStatus
    agent: Optional[str]
    result: Optional[str]
    timeout: int
    created_at: datetime
    accepted_at: Optional[datetime]
    submitted_at: Optional[datetime]
    verified_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Blockchain fields (Phase 2)
    blockchain_tx_hash: Optional[str] = None
    blockchain_accept_tx: Optional[str] = None
    blockchain_submit_tx: Optional[str] = None
    blockchain_complete_tx: Optional[str] = None
    blockchain_status: Optional[str] = None

    # Gas fee fields (Phase 3)
    gas_used: Optional[int] = None
    gas_cost: Optional[int] = None
    gas_split: Optional[int] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "task_id": "task_1709481234567",
                "publisher": "0x1234567890abcdef1234567890abcdef12345678",
                "description": "开发一个用户认证 REST API 端点",
                "input_data": "要求: JWT tokens, bcrypt 加密, PostgreSQL 数据库",
                "expected_output": "可工作的 API 端点及测试代码",
                "reward": 1000000000000000000,
                "task_type": "CODE",
                "status": "Open",
                "agent": None,
                "result": None,
                "timeout": 86400,
                "created_at": "2024-03-03T10:00:00Z",
                "blockchain_tx_hash": "0xabc123...",
                "blockchain_status": "published"
            }
        }


class TaskSubmit(BaseModel):
    """Task submission request."""
    result: str


class TaskDispute(BaseModel):
    """Task dispute request."""
    reason: str


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
async def create_task(
    request: Request,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new task and publish to blockchain.

    Creates a task in the database and publishes it to the blockchain for transparency
    and immutability. The task becomes available for agents to accept.

    **Authentication**: JWT token required

    **Rate Limit**: 100 requests per minute

    **Request Body**:
    - `description`: Task description (required)
    - `input_data`: Additional input information (optional)
    - `expected_output`: Expected result description (optional)
    - `reward`: Reward amount in Wei (required, 1 ETH = 10^18 Wei)
    - `task_type`: Task category - CODE, DATA, COMPUTE, RESEARCH, DESIGN, WRITING, OTHER
    - `timeout`: Task deadline in seconds (required)

    **Returns**: Complete task object including:
    - `task_id`: Unique task identifier
    - `blockchain_tx_hash`: Transaction hash of blockchain publication
    - `blockchain_status`: "published" if successful
    - `status`: "Open" (available for agents)

    **Blockchain Integration**:
    - Task is published to smart contract
    - Reward is escrowed on-chain
    - Transaction hash stored for verification

    **Gas Fees**:
    - Publisher pays gas for task publication
    - Agent pays gas for acceptance and submission
    - 50% of total gas cost deducted from agent's reward

    **Example**:
    ```json
    {
      "description": "Develop a REST API endpoint for user authentication",
      "input_data": "Requirements: JWT tokens, bcrypt hashing, PostgreSQL",
      "expected_output": "Working API endpoint with tests",
      "reward": 1000000000000000000,
      "task_type": "CODE",
      "timeout": 86400
    }
    ```
    """
    # Generate task ID
    task_id = f"task_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    # Create task in database first
    task = Task(
        task_id=task_id,
        publisher=current_user.wallet_address,
        description=task_data.description,
        input_data=task_data.input_data,
        expected_output=task_data.expected_output,
        reward=task_data.reward,
        task_type=task_data.task_type,
        status=TaskStatus.OPEN,
        timeout=task_data.timeout
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # Invalidate task cache after creation
    invalidate_tasks_cache()

    # Phase 2: Publish task to blockchain
    try:
        blockchain = get_blockchain_service()

        # Calculate deadline (current time + timeout)
        deadline = int(datetime.now(timezone.utc).timestamp()) + task_data.timeout

        # Publish to blockchain
        tx_hash = await blockchain.publish_task_on_chain(
            task_id=task_id,
            title=f"{task_data.task_type.value} Task",
            description=task_data.description,
            reward=task_data.reward,
            deadline=deadline
        )

        if tx_hash:
            # Save transaction hash
            task.blockchain_tx_hash = tx_hash
            task.blockchain_status = "published"
            db.commit()
            db.refresh(task)

            logger.info(f"Task {task_id} published to blockchain: {tx_hash}")
        else:
            logger.warning(f"Task {task_id} created in database but blockchain publish failed")

    except Exception as e:
        logger.error(f"Blockchain integration error for task {task_id}: {e}")
        # Task is still created in database, blockchain integration is optional for now
        # In production, you might want to handle this differently

    return task


@router.get("", response_model=List[TaskResponse])
@limiter.limit("100/minute")
async def list_tasks(
    request: Request,
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List tasks with optional filters and pagination.

    Returns a paginated list of tasks, optionally filtered by status and type.
    Tasks are sorted by creation date (newest first).

    **Authentication**: None required (public endpoint)

    **Rate Limit**: 100 requests per minute

    **Query Parameters**:
    - `status`: Filter by task status (Open, Accepted, Submitted, Completed, etc.)
    - `task_type`: Filter by task type (CODE, DATA, COMPUTE, etc.)
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 100, max: 100)

    **Task Status Values**:
    - `Open`: Available for agents to accept
    - `Accepted`: Assigned to an agent
    - `Submitted`: Result submitted, awaiting verification
    - `Verified`: Result verified
    - `Completed`: Task completed, reward distributed
    - `Failed`: Task failed verification
    - `Disputed`: Under dispute resolution

    **Task Types**:
    - `CODE`: Software development tasks
    - `DATA`: Data processing/analysis
    - `COMPUTE`: Computational tasks
    - `RESEARCH`: Research tasks
    - `DESIGN`: Design work
    - `WRITING`: Content writing
    - `OTHER`: Other task types

    **Performance**:
    - Uses indexed columns for efficient filtering
    - Query performance monitored (warning if > 500ms)

    **Example**: `GET /api/tasks?status=Open&task_type=CODE&limit=10`
    """
    # Use cached task list query
    result = await get_tasks_cached(status=status.value if status else None, limit=limit, db=db)
    return result["tasks"]


@router.get("/{task_id}", response_model=TaskResponse)
@limiter.limit("100/minute")
async def get_task(request: Request, task_id: int, db: Session = Depends(get_db)):
    """
    Get task details.

    Public endpoint.
    Rate limited to 100 requests per minute.
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.post("/{task_id}/accept", response_model=TaskResponse)
@limiter.limit("100/minute")
async def accept_task(
    request: Request,
    task_id: int,
    auth: tuple = Depends(get_current_user_or_agent),
    db: Session = Depends(get_db)
):
    """
    Accept a task as an agent.

    Assigns the task to the authenticated agent and records the acceptance on blockchain.
    Once accepted, only the assigned agent can submit results.

    **Authentication**: JWT token or API Key required

    **Rate Limit**: 100 requests per minute

    **Path Parameters**:
    - `task_id`: Task ID (integer)

    **Returns**: Updated task object with:
    - `status`: Changed to "Accepted"
    - `agent`: Agent's wallet address
    - `accepted_at`: Acceptance timestamp
    - `blockchain_accept_tx`: Transaction hash of blockchain acceptance

    **Blockchain Integration**:
    - Acceptance recorded on smart contract
    - Agent commits to completing the task
    - Transaction hash stored for verification

    **Requirements**:
    - Task must be in "Open" status
    - User must have a registered agent
    - Agent must not already be assigned to this task

    **Errors**:
    - `400`: Task is not open / No agent found
    - `404`: Task not found
    - `401`: Invalid authentication

    **Gas Fees**:
    - Agent pays gas for acceptance transaction
    - Gas cost will be deducted from final reward (50% share)
    """
    user, agent = auth

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No agent found. Please register an agent first."
        )

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != TaskStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not open"
        )

    # Anti-cheat: Check for self-trade (publisher == acceptor)
    try:
        if task.publisher and agent.owner and task.publisher.lower() == agent.owner.lower():
            logger.warning(f"Self-trade detected: agent {agent.agent_id} accepting own task {task_id}")
            AntiCheatService.apply_penalty(
                db, agent.agent_id, "SELF_TRADE",
                f"Agent accepted own task {task_id} (publisher == acceptor)"
            )
    except Exception as e:
        logger.error(f"Anti-cheat self-trade check failed for task {task_id}: {e}")

    # Financial closure: check agent survival status before accepting
    try:
        survival = SurvivalService.get_agent_survival(db, agent.agent_id)
        if survival and survival.status == "ELIMINATED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "AGENT_ELIMINATED", "message": "Agent has been eliminated and cannot accept tasks"}}
            )
        if survival and survival.status == "CRITICAL":
            # Allow CRITICAL agents to accept tasks but log warning
            logger.warning(f"CRITICAL agent {agent.agent_id} accepting task {task_id}")
    except HTTPException:
        raise  # Re-raise our own exceptions
    except Exception as e:
        logger.warning(f"Financial check failed for agent {agent.agent_id}: {e}")
        # Don't block task acceptance on financial check failure

    # Update database
    task.status = TaskStatus.ACCEPTED
    task.agent = agent.owner
    task.accepted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    # Phase 2: Accept task on blockchain
    try:
        blockchain = get_blockchain_service()

        tx_hash = await blockchain.accept_task_on_chain(task.task_id)

        if tx_hash:
            task.blockchain_accept_tx = tx_hash
            db.commit()
            db.refresh(task)

            logger.info(f"Task {task.task_id} accepted on blockchain: {tx_hash}")
        else:
            logger.warning(f"Task {task.task_id} accepted in database but blockchain accept failed")

    except Exception as e:
        logger.error(f"Blockchain integration error for task accept {task.task_id}: {e}")

    # Phase 3: Auto-execute task using agent engine
    try:
        queue_id = await submit_task_to_queue(task.id, agent.agent_id, db)
        logger.info(f"Task {task.id} submitted to execution queue: {queue_id}")

        # Update agent current tasks count
        agent.current_tasks += 1
        db.commit()

    except Exception as e:
        logger.error(f"Failed to submit task {task.id} to execution queue: {e}")
        # Don't fail the accept operation if queue submission fails

    return task


@router.post("/{task_id}/submit", response_model=TaskResponse)
@limiter.limit("100/minute")
async def submit_task(
    request: Request,
    task_id: int,
    submission: TaskSubmit,
    auth: tuple = Depends(get_current_user_or_agent),
    db: Session = Depends(get_db)
):
    """
    Submit task result for verification.

    Submits the completed task result and records it on blockchain. The result
    will be verified before the task can be completed and rewards distributed.

    **Authentication**: JWT token or API Key required (must be assigned agent)

    **Rate Limit**: 100 requests per minute

    **Path Parameters**:
    - `task_id`: Task ID (integer)

    **Request Body**:
    - `result`: Task result/deliverable (required, string)

    **Returns**: Updated task object with:
    - `status`: Changed to "Submitted"
    - `result`: Submitted result
    - `submitted_at`: Submission timestamp
    - `blockchain_submit_tx`: Transaction hash of blockchain submission

    **Blockchain Integration**:
    - Result hash recorded on smart contract
    - Submission timestamp recorded on-chain
    - Transaction hash stored for verification

    **Requirements**:
    - Task must be in "Accepted" status
    - Must be the assigned agent
    - Result must not be empty

    **Errors**:
    - `400`: Task is not accepted
    - `403`: Not the assigned agent
    - `404`: Task not found
    - `401`: Invalid authentication

    **Next Steps**:
    - Publisher reviews the result
    - Publisher calls /complete to accept and distribute rewards
    - Or publisher can dispute if result is unsatisfactory

    **Gas Fees**:
    - Agent pays gas for submission transaction
    - Gas cost will be deducted from final reward (50% share)
    """
    user, agent = auth

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No agent found. Please register an agent first."
        )

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != TaskStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not accepted"
        )

    if task.agent != agent.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the assigned agent"
        )

    # Update database
    task.status = TaskStatus.SUBMITTED
    task.result = submission.result
    task.submitted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    # Phase 2: Submit result to blockchain
    try:
        blockchain = get_blockchain_service()

        tx_hash = await blockchain.submit_task_on_chain(
            task_id=task.task_id,
            result=submission.result
        )

        if tx_hash:
            task.blockchain_submit_tx = tx_hash
            db.commit()
            db.refresh(task)

            logger.info(f"Task {task.task_id} submitted to blockchain: {tx_hash}")
        else:
            logger.warning(f"Task {task.task_id} submitted in database but blockchain submit failed")

    except Exception as e:
        logger.error(f"Blockchain integration error for task submit {task.task_id}: {e}")

    # TODO [Phase 2]: Trigger verification engine
    # Current implementation: Manual verification (Phase 1 MVP)
    # Phase 2 will integrate with verification engine: VerificationEngine.verify(taskId, result)

    return task


@router.post("/{task_id}/dispute", response_model=TaskResponse)
@limiter.limit("10/minute")
async def dispute_task(
    request: Request,
    task_id: int,
    dispute: TaskDispute,
    auth: tuple = Depends(get_current_user_or_agent),
    db: Session = Depends(get_db)
):
    """
    Dispute task verification.

    Requires JWT token or API Key authentication.
    Rate limited to 10 requests per minute.
    """
    user, agent = auth

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No agent found. Please register an agent first."
        )

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != TaskStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not failed"
        )

    if task.agent != agent.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the assigned agent"
        )

    # TODO [Phase 2]: Interact with blockchain to dispute verification
    # Current implementation: Database-only dispute (Phase 1 MVP)
    # Phase 2 will integrate with smart contract: TaskMarket.disputeVerification(taskId, reason)

    task.status = TaskStatus.DISPUTED
    task.dispute_reason = dispute.reason

    db.commit()
    db.refresh(task)

    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete task and distribute rewards (publisher only).

    Marks the task as completed, triggers reward distribution on blockchain, and
    calculates gas fee sharing. Only the task publisher can complete a task.

    **Authentication**: JWT token required (must be task publisher)

    **Path Parameters**:
    - `task_id`: Task ID (integer)

    **Returns**: Updated task object with:
    - `status`: Changed to "Completed"
    - `completed_at`: Completion timestamp
    - `verified_at`: Verification timestamp
    - `blockchain_complete_tx`: Transaction hash of completion
    - `gas_used`: Total gas consumed across all transactions
    - `gas_cost`: Total gas cost in Wei
    - `gas_split`: Agent's 50% share of gas cost (deducted from reward)

    **Blockchain Integration**:
    - Completion recorded on smart contract
    - Rewards automatically distributed to agent
    - Gas fees calculated from all transaction receipts

    **Gas Fee Calculation**:
    1. Collects all transaction hashes (publish, accept, submit, complete)
    2. Retrieves gas used and gas price for each transaction
    3. Calculates total gas cost
    4. Agent pays 50% of total gas cost (deducted from reward)
    5. Actual reward = Original reward - Gas split

    **Requirements**:
    - Task must be in "Submitted" status
    - Must be the task publisher
    - Result must have been submitted

    **Errors**:
    - `400`: Task must be submitted before completion
    - `403`: Only task publisher can complete
    - `404`: Task not found
    - `401`: Invalid authentication

    **Example Response**:
    ```json
    {
      "status": "Completed",
      "gas_used": 250000,
      "gas_cost": 5000000000000000,
      "gas_split": 2500000000000000,
      "reward": 1000000000000000000,
      "actual_reward": 997500000000000000
    }
    ```
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.publisher != current_user.wallet_address:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only task publisher can complete the task"
        )

    if task.status != TaskStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must be submitted before completion"
        )

    # Update database
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    task.verified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    # Survival system: record income, cost, and auto-calculate scores
    try:
        agent = db.query(Agent).filter(Agent.owner == task.agent).first()
        if agent:
            COMPUTE_COST_WEI = 100000000000000000  # 0.1 ETH in Wei

            # Record task reward as income
            SurvivalService.record_income(
                db, agent.agent_id, task.reward,
                "TASK_REWARD", task_id=task.task_id,
                description=f"Task {task.task_id} completed"
            )

            # Record compute cost
            SurvivalService.record_cost(
                db, agent.agent_id, COMPUTE_COST_WEI,
                "COMPUTE_COST", task_id=task.task_id,
                description=f"Task {task.task_id} compute"
            )

            # Auto-calculate quality and efficiency scores
            task_duration = 0.0
            if task.accepted_at and task.completed_at:
                task_duration = (task.completed_at - task.accepted_at).total_seconds()

            SurvivalService.update_scores_on_task_completion(
                db=db,
                agent_id=agent.agent_id,
                task_reward=float(task.reward),
                task_duration_seconds=task_duration,
                published_duration_seconds=float(task.timeout),
                task_rating=None  # No manual rating yet; can be added later
            )

            logger.info(f"Survival auto-scored for agent {agent.agent_id} on task {task.task_id}")
    except Exception as e:
        logger.error(f"Survival system error for task {task_id}: {e}")
        # Don't let survival errors break task completion

    # Store task memory and reflection
    try:
        db_pool = await get_db_pool()
        memory_system = await get_memory_system(db_pool)
        reflection_system = await get_reflection_system(db_pool, memory_system)

        # Get agent from task
        agent = db.query(Agent).filter(Agent.owner == task.agent).first()

        if agent:
            # Store task execution memory
            execution_data = {
                "description": task.description,
                "task_type": task.task_type.value,
                "status": task.status.value,
                "result": task.result,
                "reward": task.reward,
                "execution_time": (task.completed_at - task.accepted_at).total_seconds() if task.accepted_at else 0
            }

            # Execute memory storage and reflection in parallel
            import asyncio
            memory_task = memory_system.store_task_memory(
                agent_id=agent.id,
                task_id=task.id,
                execution_data=execution_data,
                memory_type="task_execution"
            )

            reflection_task = reflection_system.reflect_on_task(
                agent_id=agent.id,
                task_id=task.id,
                result=execution_data
            )

            # Wait for both to complete and capture exceptions
            results = await asyncio.gather(memory_task, reflection_task, return_exceptions=True)

            # Log any errors that occurred
            if isinstance(results[0], Exception):
                logger.error(f"Memory storage failed: {results[0]}")
            if isinstance(results[1], Exception):
                logger.error(f"Reflection generation failed: {results[1]}")

            logger.info(f"Stored memory and reflection for agent {agent.id}, task {task.id}")
    except Exception as e:
        logger.error(f"Error storing memory/reflection: {e}")
        # Don't fail task completion if memory storage fails

    # EvoMap: trigger post-task learning cycle (async, fire-and-forget)
    try:
        agent_for_evomap = db.query(Agent).filter(Agent.owner == task.agent).first()
        if agent_for_evomap:
            import asyncio
            from services.evomap_integration_service import EvomapIntegrationService

            async def _run_learning_cycle():
                try:
                    evomap_svc = EvomapIntegrationService(db)
                    await evomap_svc.execute_learning_cycle(
                        task_id=task.id,
                        agent_id=agent_for_evomap.id,
                        task_result={
                            "task_type": task.task_type.value if task.task_type else "general",
                            "description": task.description,
                            "status": "completed",
                            "execution_time": (task.completed_at - task.accepted_at).total_seconds() if task.accepted_at and task.completed_at else 0,
                            "context": task.task_type.value if task.task_type else "general",
                        }
                    )
                    logger.info(f"EvoMap learning cycle completed for task {task.id}, agent {agent_for_evomap.id}")
                except Exception as e:
                    logger.warning(f"EvoMap learning cycle failed for task {task.id}: {e}")

            asyncio.create_task(_run_learning_cycle())
            logger.info(f"EvoMap learning cycle scheduled for task {task.id}")
    except Exception as e:
        logger.warning(f"Failed to schedule EvoMap learning cycle: {e}")

    # GEP: publish successful task solution to EvoMap global network
    try:
        import asyncio
        from services.gep_adapter import get_gep_adapter

        async def _publish_to_evomap():
            try:
                gep = get_gep_adapter()
                await gep.publish_gene(
                    name=f"Task {task.id}: {task.title[:50]}",
                    description=task.description[:200] if task.description else "",
                    code=task.result[:2000] if task.result else "",
                    task_type=task.task_type.value if task.task_type else "general",
                    confidence=0.8,
                    tags=["nautilus", task.task_type.value if task.task_type else "general"],
                )
                logger.info(f"Published task {task.id} solution to EvoMap")
            except Exception as e:
                logger.debug(f"GEP publish skipped for task {task.id}: {e}")

        asyncio.create_task(_publish_to_evomap())
    except Exception:
        pass  # GEP is optional, never block task completion

    # Phase 2: Complete task on blockchain (triggers reward distribution)
    try:
        blockchain = get_blockchain_service()

        tx_hash = await blockchain.complete_task_on_chain(task.task_id)

        if tx_hash:
            task.blockchain_complete_tx = tx_hash
            db.commit()
            db.refresh(task)

            logger.info(f"Task {task.task_id} completed on blockchain: {tx_hash}")

            # Phase 3: Calculate gas fees for all transactions
            tx_hashes = [
                task.blockchain_tx_hash,
                task.blockchain_accept_tx,
                task.blockchain_submit_tx,
                task.blockchain_complete_tx
            ]

            gas_info = blockchain.calculate_task_total_gas(tx_hashes)

            if gas_info:
                task.gas_used = gas_info['total_gas_used']
                task.gas_cost = gas_info['total_gas_cost']
                task.gas_split = gas_info['gas_split']

                db.commit()
                db.refresh(task)

                # Calculate actual reward after gas deduction
                actual_reward = task.reward - task.gas_split

                logger.info(f"Task {task.task_id} gas calculation:")
                logger.info(f"  Total gas used: {task.gas_used}")
                logger.info(f"  Total gas cost: {task.gas_cost} Wei")
                logger.info(f"  Agent's gas share (50%): {task.gas_split} Wei")
                logger.info(f"  Original reward: {task.reward} Wei")
                logger.info(f"  Actual reward after gas deduction: {actual_reward} Wei")
            else:
                logger.warning(f"Failed to calculate gas fees for task {task.task_id}")
        else:
            logger.warning(f"Task {task.task_id} completed in database but blockchain complete failed")

    except Exception as e:
        logger.error(f"Blockchain integration error for task complete {task.task_id}: {e}")

    return task


@router.get("/{task_id}/status")
async def get_task_status(task_id: int, db: Session = Depends(get_db)):
    """
    Get task status.

    Public endpoint.
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return {
        "task_id": task.id,
        "status": task.status,
        "agent": task.agent,
        "created_at": task.created_at,
        "accepted_at": task.accepted_at,
        "submitted_at": task.submitted_at,
        "verified_at": task.verified_at,
        "completed_at": task.completed_at
    }


@router.post("/{task_id}/execute")
@limiter.limit("20/minute")
async def execute_task(
    request: Request,
    task_id: int,
    auth: tuple = Depends(get_current_user_or_agent),
    db: Session = Depends(get_db)
):
    """
    Execute a task using the Agent Engine.

    Triggers synchronous execution of the task via MiniMax M2.7 LLM.
    The task must be in ACCEPTED state. Returns execution result directly.

    **Authentication**: JWT token or API Key required

    **Rate Limit**: 20 requests per minute
    """
    user, agent = auth

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No agent found. Please register an agent first."
        )

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != TaskStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task must be in ACCEPTED state, current: {task.status}"
        )

    try:
        result = await execute_task_by_agent(task.id, agent.agent_id, db)
        return {
            "success": result.get("success", False),
            "data": result,
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"Task {task_id} execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "EXECUTION_FAILED",
                    "message": str(e)
                }
            }
        )


class GasInfoResponse(BaseModel):
    """Gas fee information response."""
    task_id: int
    gas_used: Optional[int]
    gas_cost: Optional[int]
    gas_split: Optional[int]
    reward: int
    actual_reward: Optional[int]
    transactions: List[Dict[str, Optional[str]]]


@router.get("/{task_id}/gas", response_model=GasInfoResponse)
async def get_task_gas_info(task_id: int, db: Session = Depends(get_db)):
    """
    Get detailed gas fee information for a task.

    Returns comprehensive gas usage and cost breakdown including all transactions
    and the agent's share of gas costs.

    **Authentication**: None required (public endpoint)

    **Path Parameters**:
    - `task_id`: Task ID (integer)

    **Returns**:
    - `task_id`: Task identifier
    - `gas_used`: Total gas units consumed across all transactions
    - `gas_cost`: Total gas cost in Wei
    - `gas_split`: Agent's 50% share of gas cost (deducted from reward)
    - `reward`: Original reward amount in Wei
    - `actual_reward`: Reward after gas deduction (reward - gas_split)
    - `transactions`: Array of transaction details

    **Transaction Details**:
    Each transaction includes:
    - `type`: Transaction type (publish, accept, submit, complete)
    - `tx_hash`: Blockchain transaction hash
    - `description`: Human-readable description

    **Gas Fee Sharing**:
    - Total gas cost calculated from all transactions
    - Agent pays 50% of total gas cost
    - Gas split deducted from agent's reward
    - Publisher effectively pays 50% of gas costs

    **Errors**:
    - `404`: Task not found

    **Example Response**:
    ```json
    {
      "task_id": 1,
      "gas_used": 250000,
      "gas_cost": 5000000000000000,
      "gas_split": 2500000000000000,
      "reward": 1000000000000000000,
      "actual_reward": 997500000000000000,
      "transactions": [
        {
          "type": "publish",
          "tx_hash": "0x1234...",
          "description": "Task published by publisher"
        },
        {
          "type": "accept",
          "tx_hash": "0xabcd...",
          "description": "Task accepted by agent"
        }
      ]
    }
    ```
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Calculate actual reward after gas deduction
    actual_reward = None
    if task.gas_split is not None:
        actual_reward = task.reward - task.gas_split

    # Prepare transaction list
    transactions = [
        {
            "type": "publish",
            "tx_hash": task.blockchain_tx_hash,
            "description": "Task published by publisher"
        },
        {
            "type": "accept",
            "tx_hash": task.blockchain_accept_tx,
            "description": "Task accepted by agent"
        },
        {
            "type": "submit",
            "tx_hash": task.blockchain_submit_tx,
            "description": "Result submitted by agent"
        },
        {
            "type": "complete",
            "tx_hash": task.blockchain_complete_tx,
            "description": "Task completed by publisher"
        }
    ]

    return {
        "task_id": task.id,
        "gas_used": task.gas_used,
        "gas_cost": task.gas_cost,
        "gas_split": task.gas_split,
        "reward": task.reward,
        "actual_reward": actual_reward,
        "transactions": transactions
    }


@router.get("/{task_id}/recommendations", response_model=List[Dict])
@limiter.limit("100/minute")
async def get_task_recommendations(
    request: Request,
    task_id: int,
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get agent recommendations for a task.

    Returns a list of recommended agents based on:
    - Specialty match
    - Reputation
    - Availability
    - Success rate

    **Authentication**: JWT token required

    **Rate Limit**: 100 requests per minute

    **Path Parameters**:
    - `task_id`: Task ID (integer)

    **Query Parameters**:
    - `limit`: Maximum number of recommendations (1-10, default: 5)

    **Returns**: List of recommended agents with:
    - `agent_id`: Agent ID
    - `name`: Agent name
    - `description`: Agent description
    - `reputation`: Agent reputation score
    - `specialties`: Agent specialties
    - `completed_tasks`: Number of completed tasks
    - `failed_tasks`: Number of failed tasks
    - `current_tasks`: Current active tasks
    - `match_score`: Matching score (0-100)
    - `available`: Whether agent has capacity

    **Example Response**:
    ```json
    [
      {
        "agent_id": 1,
        "name": "CodeMaster",
        "description": "Expert in Python and JavaScript",
        "reputation": 850,
        "specialties": "CODE,DATA",
        "completed_tasks": 45,
        "failed_tasks": 2,
        "current_tasks": 1,
        "match_score": 87.5,
        "available": true
      }
    ]
    ```
    """
    from task_matcher import get_agent_recommendations

    # Check if task exists
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Get recommendations
    try:
        recommendations = await get_agent_recommendations(task_id, db, limit=limit)
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent recommendations"
        )

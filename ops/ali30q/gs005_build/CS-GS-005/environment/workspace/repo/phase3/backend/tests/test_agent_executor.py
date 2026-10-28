"""
Test Agent Executor Integration

Tests the integration between backend API and agent-engine.
"""
import pytest
import asyncio
from sqlalchemy.orm import Session

from models.database import Task, Agent, TaskStatus, TaskType
from agent_executor import (
    execute_task_by_agent,
    submit_task_to_queue,
    get_agent_status,
    get_agent_engine
)


@pytest.fixture
def sample_task(db: Session):
    """Create a sample task for testing."""
    task = Task(
        task_id="test_task_001",
        publisher="0x1234567890123456789012345678901234567890",
        description="Test task: Calculate fibonacci(10)",
        requirements="Write a Python function to calculate fibonacci numbers",
        reward=1000000000000000000,  # 1 ETH
        task_type=TaskType.CODE,
        status=TaskStatus.ACCEPTED,
        timeout=300
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def sample_agent(db: Session):
    """Create a sample agent for testing."""
    agent = Agent(
        agent_id=1,
        owner="0x1234567890123456789012345678901234567890",
        name="Test Agent",
        description="Test agent for integration testing",
        reputation=100,
        current_tasks=0,
        completed_tasks=0,
        failed_tasks=0
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@pytest.mark.asyncio
async def test_get_agent_engine():
    """Test getting agent engine instance."""
    engine = get_agent_engine(agent_id=1)

    assert engine is not None
    assert engine.agent_id == 1
    assert engine.max_concurrent_tasks == 3

    # Getting same agent should return cached instance
    engine2 = get_agent_engine(agent_id=1)
    assert engine is engine2


@pytest.mark.asyncio
async def test_get_agent_status():
    """Test getting agent status."""
    # Test idle agent
    status = await get_agent_status(agent_id=999)
    assert status["agent_id"] == 999
    assert status["status"] == "idle"
    assert status["current_tasks"] == 0
    assert status["available_capacity"] == 3

    # Test active agent
    engine = get_agent_engine(agent_id=1)
    engine.current_tasks = [1, 2]

    status = await get_agent_status(agent_id=1)
    assert status["agent_id"] == 1
    assert status["status"] == "active"
    assert status["current_tasks"] == 2
    assert status["available_capacity"] == 1


@pytest.mark.asyncio
async def test_submit_task_to_queue(db: Session, sample_task, sample_agent):
    """Test submitting task to execution queue."""
    queue_id = await submit_task_to_queue(
        task_id=sample_task.id,
        agent_id=sample_agent.agent_id,
        db=db
    )

    assert queue_id is not None
    assert f"task_{sample_task.id}" in queue_id
    assert f"agent_{sample_agent.agent_id}" in queue_id

    # Give background task time to start
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_execute_task_by_agent_success(db: Session, sample_task, sample_agent):
    """Test successful task execution."""
    # Note: This test requires Docker to be running
    try:
        result = await execute_task_by_agent(
            task_id=sample_task.id,
            agent_id=sample_agent.agent_id,
            db=db
        )

        assert result["success"] is True
        assert "result" in result
        assert "execution_time" in result

        # Check task status updated
        db.refresh(sample_task)
        assert sample_task.status == TaskStatus.SUBMITTED
        assert sample_task.result is not None

        # Check agent stats updated
        db.refresh(sample_agent)
        assert sample_agent.completed_tasks == 1

    except RuntimeError as e:
        if "Docker client not available" in str(e):
            pytest.skip("Docker not available for testing")
        else:
            raise


@pytest.mark.asyncio
async def test_execute_task_by_agent_task_not_found(db: Session, sample_agent):
    """Test execution with non-existent task."""
    with pytest.raises(ValueError, match="Task .* not found"):
        await execute_task_by_agent(
            task_id=99999,
            agent_id=sample_agent.agent_id,
            db=db
        )


@pytest.mark.asyncio
async def test_execute_task_by_agent_agent_not_found(db: Session, sample_task):
    """Test execution with non-existent agent."""
    with pytest.raises(ValueError, match="Agent .* not found"):
        await execute_task_by_agent(
            task_id=sample_task.id,
            agent_id=99999,
            db=db
        )


@pytest.mark.asyncio
async def test_execute_task_by_agent_wrong_status(db: Session, sample_agent):
    """Test execution with task in wrong status."""
    # Create task in OPEN status
    task = Task(
        task_id="test_task_002",
        publisher="0x1234567890123456789012345678901234567890",
        description="Test task",
        reward=1000000000000000000,
        task_type=TaskType.CODE,
        status=TaskStatus.OPEN,  # Wrong status
        timeout=300
    )
    db.add(task)
    db.commit()

    with pytest.raises(ValueError, match="not in ACCEPTED state"):
        await execute_task_by_agent(
            task_id=task.id,
            agent_id=sample_agent.agent_id,
            db=db
        )


@pytest.mark.asyncio
async def test_concurrent_task_execution(db: Session, sample_agent):
    """Test multiple tasks executing concurrently."""
    # Create multiple tasks
    tasks = []
    for i in range(3):
        task = Task(
            task_id=f"test_task_concurrent_{i}",
            publisher="0x1234567890123456789012345678901234567890",
            description=f"Test task {i}",
            requirements="Simple task",
            reward=1000000000000000000,
            task_type=TaskType.CODE,
            status=TaskStatus.ACCEPTED,
            timeout=300
        )
        db.add(task)
        tasks.append(task)

    db.commit()

    # Submit all tasks to queue
    queue_ids = []
    for task in tasks:
        queue_id = await submit_task_to_queue(
            task_id=task.id,
            agent_id=sample_agent.agent_id,
            db=db
        )
        queue_ids.append(queue_id)

    assert len(queue_ids) == 3
    assert len(set(queue_ids)) == 3  # All unique

    # Give background tasks time to start
    await asyncio.sleep(0.2)

    # Check agent status
    status = await get_agent_status(agent_id=sample_agent.agent_id)
    assert status["current_tasks"] <= 3  # Should not exceed max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

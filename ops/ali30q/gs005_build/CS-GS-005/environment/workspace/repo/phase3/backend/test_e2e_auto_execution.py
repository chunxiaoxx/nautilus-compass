#!/usr/bin/env python3
"""
End-to-End Test for Agent Auto-Execution

This script tests the complete flow:
1. Create a task
2. Agent accepts task
3. Task automatically executes
4. Result submitted to blockchain
5. Reward distributed

Usage:
    python test_e2e_auto_execution.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models.database import Task, Agent, User, TaskStatus, TaskType
from agent_executor import execute_task_by_agent, get_agent_status


def setup_test_database():
    """Setup test database with sample data."""
    # Use test database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nautilus:nautilus@localhost/nautilus_test")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Create test user
    user = User(
        username="test_user",
        email="test@example.com",
        wallet_address="0x1234567890123456789012345678901234567890",
        hashed_password="test_hash"
    )
    db.add(user)
    db.commit()

    # Create test agent
    agent = Agent(
        agent_id=1,
        owner=user.wallet_address,
        name="Test Agent",
        description="Test agent for E2E testing",
        reputation=100,
        specialties="CODE,DATA",
        current_tasks=0,
        completed_tasks=0,
        failed_tasks=0,
        total_earnings=0
    )
    db.add(agent)
    db.commit()

    # Create test task
    task = Task(
        task_id=f"test_task_{int(datetime.now(timezone.utc).timestamp())}",
        publisher=user.wallet_address,
        description="Calculate fibonacci(10)",
        requirements="""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
""",
        reward=1000000000000000000,  # 1 ETH
        task_type=TaskType.CODE,
        status=TaskStatus.ACCEPTED,  # Already accepted
        agent=user.wallet_address,
        timeout=300,
        accepted_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return db, task, agent


async def test_auto_execution():
    """Test automatic task execution."""
    print("=" * 60)
    print("🚀 Agent Auto-Execution E2E Test")
    print("=" * 60)
    print()

    # Setup
    print("📦 Setting up test database...")
    db, task, agent = setup_test_database()
    print(f"✅ Created task {task.id} and agent {agent.agent_id}")
    print()

    # Check initial agent status
    print("📊 Checking initial agent status...")
    status = await get_agent_status(agent.agent_id)
    print(f"   Agent ID: {status['agent_id']}")
    print(f"   Status: {status['status']}")
    print(f"   Current tasks: {status['current_tasks']}")
    print(f"   Available capacity: {status['available_capacity']}")
    print()

    # Execute task
    print("⚙️  Executing task...")
    print(f"   Task ID: {task.id}")
    print(f"   Task Type: {task.task_type}")
    print(f"   Description: {task.description}")
    print()

    try:
        result = await execute_task_by_agent(
            task_id=task.id,
            agent_id=agent.agent_id,
            db=db
        )

        print("✅ Task execution completed!")
        print()
        print("📊 Execution Results:")
        print(f"   Success: {result['success']}")
        print(f"   Execution time: {result['execution_time']:.2f}s")

        if result['success']:
            print(f"   Result: {result['result'][:100]}...")
            if result.get('blockchain_tx'):
                print(f"   Blockchain TX: {result['blockchain_tx']}")
        else:
            print(f"   Error: {result['error']}")
        print()

        # Check updated task status
        db.refresh(task)
        print("📋 Updated Task Status:")
        print(f"   Status: {task.status}")
        print(f"   Result: {task.result[:100] if task.result else 'None'}...")
        print(f"   Submitted at: {task.submitted_at}")
        print()

        # Check updated agent stats
        db.refresh(agent)
        print("🤖 Updated Agent Stats:")
        print(f"   Completed tasks: {agent.completed_tasks}")
        print(f"   Failed tasks: {agent.failed_tasks}")
        print(f"   Current tasks: {agent.current_tasks}")
        print()

        # Check final agent status
        status = await get_agent_status(agent.agent_id)
        print("📊 Final Agent Status:")
        print(f"   Status: {status['status']}")
        print(f"   Current tasks: {status['current_tasks']}")
        print(f"   Available capacity: {status['available_capacity']}")
        print()

        if result['success']:
            print("=" * 60)
            print("🎉 E2E Test PASSED!")
            print("=" * 60)
            return 0
        else:
            print("=" * 60)
            print("❌ E2E Test FAILED: Task execution failed")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("=" * 60)
        print("❌ E2E Test FAILED: Exception occurred")
        print("=" * 60)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(test_auto_execution())
    sys.exit(exit_code)

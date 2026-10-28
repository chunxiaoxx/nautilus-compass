"""
Benchmark script to measure API performance before and after optimization.
"""
import time
import statistics
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from main import app
from models.database import Base, Task, Agent, Reward, User, APIKey, TaskType, TaskStatus
from utils.database import get_db
from utils.auth import hash_password, generate_api_key


# Test database setup
TEST_DATABASE_URL = "sqlite:///./benchmark.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_test_data():
    """Setup test database with sample data."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create test user
    user = User(
        username="benchuser",
        email="bench@example.com",
        hashed_password=hash_password("testpass123"),
        wallet_address="0x1234567890123456789012345678901234567890",
        is_active=True
    )
    db.add(user)
    db.commit()

    # Create test agent
    agent = Agent(
        agent_id=1,
        owner=user.wallet_address,
        name="Benchmark Agent",
        description="Agent for benchmarking",
        reputation=100
    )
    db.add(agent)
    db.commit()

    # Create API key
    api_key = generate_api_key()
    api_key_obj = APIKey(
        key=api_key,
        agent_id=agent.agent_id,
        name="Benchmark Key"
    )
    db.add(api_key_obj)
    db.commit()

    # Create tasks
    print("Creating test data...")
    for i in range(500):
        task = Task(
            task_id=f"task_{i}",
            publisher=user.wallet_address,
            description=f"Benchmark task {i}",
            reward=1000000000000000000,
            task_type=TaskType.CODE,
            status=TaskStatus.OPEN if i % 3 == 0 else TaskStatus.COMPLETED,
            timeout=3600,
            created_at=datetime.now(timezone.utc)
        )
        db.add(task)

    # Create rewards
    for i in range(200):
        reward = Reward(
            task_id=f"task_{i}",
            agent=agent.owner,
            amount=1000000000000000000,
            status="Distributed",
            distributed_at=datetime.now(timezone.utc)
        )
        db.add(reward)

    db.commit()
    db.close()
    print("✓ Test data created")

    return api_key


def benchmark_endpoint(client: TestClient, method: str, url: str, headers: Dict = None, iterations: int = 10) -> Dict:
    """Benchmark a single endpoint."""
    times = []

    for _ in range(iterations):
        start = time.time()
        if method == "GET":
            response = client.get(url, headers=headers)
        elif method == "POST":
            response = client.post(url, headers=headers)
        elapsed = time.time() - start

        if response.status_code == 200:
            times.append(elapsed)

    if not times:
        return {"error": "All requests failed"}

    return {
        "min": min(times) * 1000,  # Convert to ms
        "max": max(times) * 1000,
        "avg": statistics.mean(times) * 1000,
        "median": statistics.median(times) * 1000,
        "p95": statistics.quantiles(times, n=20)[18] * 1000 if len(times) > 1 else times[0] * 1000,
        "iterations": len(times)
    }


def run_benchmarks(api_key: str):
    """Run all benchmarks."""
    client = TestClient(app)

    benchmarks = [
        ("GET", "/api/tasks?limit=50", None, "List Tasks (50)"),
        ("GET", "/api/tasks?limit=100", None, "List Tasks (100)"),
        ("GET", "/api/tasks?status=Open&limit=50", None, "List Tasks (filtered)"),
        ("GET", "/api/agents?limit=50", None, "List Agents (50)"),
        ("GET", "/api/agents?limit=100", None, "List Agents (100)"),
        ("GET", "/api/rewards/balance", {"X-API-Key": api_key}, "Get Balance"),
        ("GET", "/api/rewards/history?limit=50", {"X-API-Key": api_key}, "Reward History (50)"),
        ("GET", "/api/rewards/history?limit=100", {"X-API-Key": api_key}, "Reward History (100)"),
        ("GET", "/api/agents/1/tasks?limit=50", None, "Agent Tasks (50)"),
    ]

    print("\n" + "="*80)
    print("PERFORMANCE BENCHMARK RESULTS")
    print("="*80)
    print(f"\nIterations per endpoint: 10")
    print(f"Test data: 500 tasks, 200 rewards")
    print("\n" + "-"*80)
    print(f"{'Endpoint':<35} {'Avg':<10} {'Median':<10} {'P95':<10} {'Min':<10} {'Max':<10}")
    print("-"*80)

    results = []
    for method, url, headers, name in benchmarks:
        result = benchmark_endpoint(client, method, url, headers)
        results.append((name, result))

        if "error" not in result:
            print(f"{name:<35} {result['avg']:>8.1f}ms {result['median']:>8.1f}ms {result['p95']:>8.1f}ms {result['min']:>8.1f}ms {result['max']:>8.1f}ms")
        else:
            print(f"{name:<35} ERROR")

    print("-"*80)

    # Summary
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)

    all_avgs = [r[1]['avg'] for r in results if 'error' not in r[1]]
    if all_avgs:
        print(f"\nOverall Average Response Time: {statistics.mean(all_avgs):.1f}ms")
        print(f"Fastest Endpoint: {min(all_avgs):.1f}ms")
        print(f"Slowest Endpoint: {max(all_avgs):.1f}ms")

    # Performance targets
    print("\n" + "-"*80)
    print("PERFORMANCE TARGETS")
    print("-"*80)

    targets = {
        "List Tasks": 500,
        "List Agents": 300,
        "Get Balance": 300,
        "Reward History": 300,
        "Agent Tasks": 500
    }

    print(f"\n{'Endpoint':<35} {'Target':<15} {'Actual':<15} {'Status'}")
    print("-"*80)

    for name, result in results:
        if 'error' in result:
            continue

        # Find matching target
        target = None
        for key, val in targets.items():
            if key in name:
                target = val
                break

        if target:
            status = "✓ PASS" if result['avg'] < target else "✗ FAIL"
            target_str = f"< {target}ms"
            actual_str = f"{result['avg']:.1f}ms"
            print(f"{name:<35} {target_str:<15} {actual_str:<15} {status}")

    print("="*80)


def cleanup():
    """Cleanup test database."""
    try:
        os.remove("benchmark.db")
        print("\n✓ Cleanup completed")
    except Exception:
        pass


if __name__ == "__main__":
    print("="*80)
    print("NAUTILUS PHASE 3 - PERFORMANCE BENCHMARK")
    print("="*80)

    try:
        api_key = setup_test_data()
        run_benchmarks(api_key)
    finally:
        cleanup()

    print("\n" + "="*80)
    print("BENCHMARK COMPLETED")
    print("="*80)
    print("\nNext steps:")
    print("1. Review results against performance targets")
    print("2. If targets not met, run: python add_performance_indexes.py")
    print("3. Run benchmark again to measure improvement")
    print("4. Check PERFORMANCE_OPTIMIZATION_REPORT.md for details")
    print("="*80)

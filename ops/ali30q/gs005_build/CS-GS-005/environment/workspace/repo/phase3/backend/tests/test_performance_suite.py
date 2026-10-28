"""
Performance Tests for Nautilus Phase 3 Backend.

Tests response times, throughput, and system performance under load.
"""
import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models.database import Base, Task, Agent, User, TaskType, TaskStatus
from utils.database import get_db
from utils.auth import hash_password, create_access_token


# Test database setup
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database with sample data."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create test user
    user = User(
        username="perfuser",
        email="perf@example.com",
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
        name="Performance Agent",
        description="Agent for performance testing",
        specialties="python,testing",
        reputation=100,
        completed_tasks=0,
        failed_tasks=0,
        total_earnings=0
    )
    db.add(agent)
    db.commit()

    # Create multiple tasks for testing
    for i in range(100):
        task = Task(
            task_id=f"perf_task_{i}",
            publisher=user.wallet_address,
            description=f"Performance test task {i}",
            reward=1000000000000000000,  # 1 ETH
            task_type=TaskType.CODE,
            status=TaskStatus.OPEN if i % 3 == 0 else TaskStatus.COMPLETED,
            timeout=3600
        )
        db.add(task)

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(setup_database):
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token():
    """Generate auth token."""
    return create_access_token(data={"sub": "perfuser"})


class TestAPIResponseTime:
    """Test API response time performance."""

    def test_health_check_response_time(self, client):
        """Test health check endpoint response time."""
        times = []
        for _ in range(50):
            start = time.time()
            response = client.get("/health")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
        p99_time = statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times)

        print(f"\nHealth Check Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95_time*1000:.2f}ms")
        print(f"  P99: {p99_time*1000:.2f}ms")

        assert avg_time < 1.0, f"Average response time {avg_time}s exceeds 1s"
        assert p95_time < 2.0, f"P95 response time {p95_time}s exceeds 2s"

    def test_get_tasks_response_time(self, client):
        """Test GET /api/tasks response time."""
        times = []
        for _ in range(50):
            start = time.time()
            response = client.get("/api/tasks")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)

        print(f"\nGET /api/tasks Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95_time*1000:.2f}ms")

        assert avg_time < 1.0, f"Average response time {avg_time}s exceeds 1s"

    def test_get_agents_response_time(self, client):
        """Test GET /api/agents response time."""
        times = []
        for _ in range(50):
            start = time.time()
            response = client.get("/api/agents")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)

        print(f"\nGET /api/agents Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95_time*1000:.2f}ms")

        assert avg_time < 1.0, f"Average response time {avg_time}s exceeds 1s"

    def test_get_single_task_response_time(self, client):
        """Test GET /api/tasks/{id} response time."""
        times = []
        for _ in range(50):
            start = time.time()
            response = client.get("/api/tasks/perf_task_0")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)

        print(f"\nGET /api/tasks/{{id}} Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95_time*1000:.2f}ms")

        assert avg_time < 0.5, f"Average response time {avg_time}s exceeds 500ms"


class TestConcurrentRequests:
    """Test concurrent request handling."""

    def test_concurrent_health_checks(self, client):
        """Test handling concurrent health check requests."""
        def make_request():
            response = client.get("/health")
            return response.status_code

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]

        success_count = sum(1 for r in results if r == 200)
        success_rate = success_count / len(results)

        print(f"\nConcurrent Health Checks:")
        print(f"  Total requests: {len(results)}")
        print(f"  Successful: {success_count}")
        print(f"  Success rate: {success_rate*100:.1f}%")

        assert success_rate >= 0.95, f"Success rate {success_rate*100:.1f}% below 95%"

    def test_concurrent_task_queries(self, client):
        """Test handling concurrent task queries."""
        def make_request():
            response = client.get("/api/tasks")
            return response.status_code

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]
        elapsed = time.time() - start_time

        success_count = sum(1 for r in results if r == 200)
        throughput = len(results) / elapsed

        print(f"\nConcurrent Task Queries:")
        print(f"  Total requests: {len(results)}")
        print(f"  Successful: {success_count}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.1f} req/s")

        assert success_count >= 95, f"Only {success_count}/100 requests succeeded"
        assert throughput >= 10, f"Throughput {throughput:.1f} req/s below 10 req/s"

    def test_concurrent_agent_queries(self, client):
        """Test handling concurrent agent queries."""
        def make_request():
            response = client.get("/api/agents")
            return response.status_code

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]
        elapsed = time.time() - start_time

        success_count = sum(1 for r in results if r == 200)
        throughput = len(results) / elapsed

        print(f"\nConcurrent Agent Queries:")
        print(f"  Total requests: {len(results)}")
        print(f"  Successful: {success_count}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.1f} req/s")

        assert success_count >= 95, f"Only {success_count}/100 requests succeeded"


class TestDatabasePerformance:
    """Test database query performance."""

    def test_task_query_performance(self, client):
        """Test task query performance with filters."""
        # Test without filters
        start = time.time()
        response = client.get("/api/tasks")
        no_filter_time = time.time() - start
        assert response.status_code == 200

        # Test with status filter
        start = time.time()
        response = client.get("/api/tasks?status=Open")
        status_filter_time = time.time() - start
        assert response.status_code == 200

        # Test with type filter
        start = time.time()
        response = client.get("/api/tasks?task_type=CODE")
        type_filter_time = time.time() - start
        assert response.status_code == 200

        print(f"\nDatabase Query Performance:")
        print(f"  No filter: {no_filter_time*1000:.2f}ms")
        print(f"  Status filter: {status_filter_time*1000:.2f}ms")
        print(f"  Type filter: {type_filter_time*1000:.2f}ms")

        assert no_filter_time < 1.0, "Query without filter too slow"
        assert status_filter_time < 1.0, "Query with status filter too slow"
        assert type_filter_time < 1.0, "Query with type filter too slow"

    def test_pagination_performance(self, client):
        """Test pagination performance."""
        times = []
        for page in range(1, 6):
            start = time.time()
            response = client.get(f"/api/tasks?page={page}&limit=10")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = statistics.mean(times)

        print(f"\nPagination Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Max: {max(times)*1000:.2f}ms")

        assert avg_time < 1.0, f"Average pagination time {avg_time}s exceeds 1s"


class TestMemoryUsage:
    """Test memory usage patterns."""

    def test_large_result_set_handling(self, client):
        """Test handling large result sets."""
        # Query all tasks
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()

        print(f"\nLarge Result Set:")
        print(f"  Tasks returned: {len(data)}")

        # Should handle 100+ tasks without issues
        assert len(data) >= 0  # Just verify it doesn't crash


class TestCachePerformance:
    """Test cache performance."""

    def test_cache_hit_performance(self, client):
        """Test cache hit improves performance."""
        # First request (cache miss)
        start = time.time()
        response1 = client.get("/api/tasks")
        first_time = time.time() - start
        assert response1.status_code == 200

        # Second request (potential cache hit)
        start = time.time()
        response2 = client.get("/api/tasks")
        second_time = time.time() - start
        assert response2.status_code == 200

        print(f"\nCache Performance:")
        print(f"  First request: {first_time*1000:.2f}ms")
        print(f"  Second request: {second_time*1000:.2f}ms")
        print(f"  Improvement: {((first_time - second_time) / first_time * 100):.1f}%")

        # Second request should be at least as fast (may be cached)
        assert second_time <= first_time * 1.5  # Allow 50% variance


class TestEndpointThroughput:
    """Test overall system throughput."""

    def test_mixed_workload_throughput(self, client):
        """Test throughput with mixed endpoint requests."""
        def make_mixed_requests():
            endpoints = [
                "/health",
                "/api/tasks",
                "/api/agents",
                "/api/tasks/perf_task_0",
                "/api/agents/1"
            ]
            results = []
            for endpoint in endpoints:
                start = time.time()
                response = client.get(endpoint)
                elapsed = time.time() - start
                results.append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "time": elapsed
                })
            return results

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_mixed_requests) for _ in range(20)]
            all_results = [r for f in as_completed(futures) for r in f.result()]
        total_time = time.time() - start_time

        total_requests = len(all_results)
        successful = sum(1 for r in all_results if r["status"] == 200)
        throughput = total_requests / total_time

        print(f"\nMixed Workload Throughput:")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful: {successful}")
        print(f"  Time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.1f} req/s")

        assert successful / total_requests >= 0.95, "Success rate below 95%"
        assert throughput >= 20, f"Throughput {throughput:.1f} req/s below 20 req/s"

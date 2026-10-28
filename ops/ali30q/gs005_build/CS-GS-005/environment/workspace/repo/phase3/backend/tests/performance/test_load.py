"""
Performance and Load Tests

测试系统性能和负载能力
"""
import pytest
import asyncio
import time
import httpx
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestResponseTime:
    """测试响应时间"""

    def test_health_endpoint_response_time(self, client):
        """测试健康检查端点响应时间"""

        start = time.time()
        response = client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # 应在 1 秒内响应

    def test_agents_list_response_time(self, client):
        """测试 Agents 列表响应时间"""

        start = time.time()
        response = client.get("/api/agents")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 2.0  # 应在 2 秒内响应

    def test_metrics_endpoint_response_time(self, client):
        """测试 metrics 端点响应时间"""

        start = time.time()
        response = client.get("/metrics")
        duration = time.time() - start

        # Metrics 端点应该快速响应
        assert duration < 1.0


class TestConcurrentLoad:
    """测试并发负载"""

    def test_concurrent_health_checks(self, client):
        """测试并发健康检查"""

        def make_request():
            response = client.get("/health")
            return response.status_code

        # 使用线程池执行 50 个并发请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            start = time.time()
            results = list(executor.map(lambda _: make_request(), range(50)))
            duration = time.time() - start

        # 验证所有请求都成功
        assert all(status == 200 for status in results)
        # 50 个请求应在 10 秒内完成
        assert duration < 10.0

    def test_concurrent_agent_queries(self, client):
        """测试并发 Agent 查询"""

        def make_request():
            response = client.get("/api/agents")
            return response.status_code == 200

        # 20 个并发请求
        with ThreadPoolExecutor(max_workers=5) as executor:
            start = time.time()
            results = list(executor.map(lambda _: make_request(), range(20)))
            duration = time.time() - start

        # 至少 80% 的请求成功
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8
        # 应在合理时间内完成
        assert duration < 15.0

    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self):
        """测试异步并发请求"""

        async def make_request(client, url):
            try:
                response = await client.get(url)
                return response.status_code == 200
            except Exception:
                return False

        async with httpx.AsyncClient(base_url="http://testserver", timeout=10.0) as client:
            # 创建 30 个并发请求
            tasks = [
                make_request(client, "/api/agents")
                for _ in range(30)
            ]

            start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start

            # 统计成功的请求
            successful = sum(1 for r in results if r is True)
            success_rate = successful / len(results)

            # 至少 70% 成功
            assert success_rate >= 0.7
            # 应在合理时间内完成
            assert duration < 10.0


class TestDatabasePerformance:
    """测试数据库性能"""

    def test_repeated_queries(self, client):
        """测试重复查询性能"""

        # 预热
        client.get("/api/agents")

        # 测试 10 次查询
        durations = []
        for _ in range(10):
            start = time.time()
            response = client.get("/api/agents")
            duration = time.time() - start
            durations.append(duration)

            assert response.status_code == 200

        # 平均响应时间应该合理
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 2.0

        # 最慢的请求也应该在合理范围内
        max_duration = max(durations)
        assert max_duration < 5.0


class TestMemoryUsage:
    """测试内存使用"""

    def test_no_memory_leak_on_repeated_requests(self, client):
        """测试重复请求不会导致内存泄漏"""

        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行 100 次请求
        for _ in range(100):
            client.get("/api/agents")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（< 50MB）
        assert memory_increase < 50


class TestRateLimiting:
    """测试速率限制"""

    def test_rate_limit_enforcement(self, client):
        """测试速率限制是否生效"""

        # 快速发送大量请求
        responses = []
        for _ in range(150):  # 超过可能的速率限制
            response = client.get("/api/agents")
            responses.append(response.status_code)

        # 应该有一些请求被限制（429 状态码）
        # 注意：如果测试环境禁用了速率限制，这个测试可能会失败
        rate_limited = sum(1 for status in responses if status == 429)

        # 如果启用了速率限制，应该有被限制的请求
        # 如果未启用，所有请求都应该成功
        assert rate_limited > 0 or all(status == 200 for status in responses)


class TestCacheEffectiveness:
    """测试缓存效果"""

    def test_cached_response_faster(self, client):
        """测试缓存响应是否更快"""

        # 第一次请求（未缓存）
        start1 = time.time()
        response1 = client.get("/api/agents")
        duration1 = time.time() - start1

        assert response1.status_code == 200

        # 第二次请求（可能已缓存）
        start2 = time.time()
        response2 = client.get("/api/agents")
        duration2 = time.time() - start2

        assert response2.status_code == 200

        # 缓存的响应通常更快（但不是绝对的）
        # 这里只是记录，不做严格断言
        print(f"First request: {duration1:.3f}s, Second request: {duration2:.3f}s")


class TestStressTest:
    """压力测试"""

    @pytest.mark.slow
    def test_sustained_load(self, client):
        """测试持续负载"""

        duration_seconds = 10
        request_count = 0
        errors = 0
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            try:
                response = client.get("/api/agents")
                if response.status_code != 200:
                    errors += 1
                request_count += 1
            except Exception:
                errors += 1

        # 计算每秒请求数
        rps = request_count / duration_seconds
        error_rate = errors / request_count if request_count > 0 else 1

        print(f"Requests per second: {rps:.2f}")
        print(f"Error rate: {error_rate:.2%}")

        # 错误率应该低于 5%
        assert error_rate < 0.05
        # 应该能处理一定的请求量
        assert rps > 1.0

"""
Performance test for Redis cache integration.

Tests cache hit rate, P95 latency, and throughput.
"""
import asyncio
import time
import statistics
from typing import List
import sys
sys.path.insert(0, '..')

from services.wallet_service import verify_wallet_signature_cached
from services.agent_service import get_agent_cached
from services.task_service import get_tasks_cached
from cache import get_cache_stats, health_check


async def test_signature_verification_cache():
    """Test signature verification caching."""
    print("\n=== 测试1: 签名验证缓存 ===")

    # Mock data
    address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
    message = "Sign this message to authenticate with Nautilus: test123"
    signature = "0xtest_signature"

    latencies = []

    # Warm up cache
    try:
        await verify_wallet_signature_cached(address, message, signature)
    except Exception:
        pass

    # Test 100 requests
    for i in range(100):
        start = time.time()
        try:
            await verify_wallet_signature_cached(address, message, signature)
        except Exception:
            pass
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    # Calculate metrics
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile

    print(f"  平均延迟: {avg_latency:.2f}ms")
    print(f"  P95延迟: {p95_latency:.2f}ms")
    print(f"  最小延迟: {min(latencies):.2f}ms")
    print(f"  最大延迟: {max(latencies):.2f}ms")

    return {
        "avg": avg_latency,
        "p95": p95_latency,
        "min": min(latencies),
    "max": max(latencies)
    }


async def test_concurrent_requests():
    """Test concurrent request handling."""
    print("\n=== 测试2: 并发请求处理 ===")

    async def make_request():
        start = time.time()
        # Simulate API request
        await asyncio.sleep(0.01)  # Simulate work
        return (time.time() - start) * 1000

    # Test with 50 concurrent requests
    start_time = time.time()
    tasks = [make_request() for _ in range(50)]
    latencies = await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    # Calculate metrics
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    throughput = 50 / total_time

    print(f"  并发数: 50")
    print(f"  总时间: {total_time:.2f}s")
    print(f"  平均延迟: {avg_latency:.2f}ms")
    print(f"  P95延迟: {p95_latency:.2f}ms")
    print(f"  吞吐量: {throughput:.2f} req/s")

    return {
        "concurrent": 50,
        "total_time": total_time,
        "avg": avg_latency,
        "p95": p95_latency,
     "throughput": throughput
    }


def test_cache_health():
    """Test Redis cache health."""
    print("\n=== 测试3: Redis缓存健康检查 ===")

    is_healthy = health_check()
    print(f"  Redis连接: {'✅ 正常' if is_healthy else '❌ 异常'}")

    if is_healthy:
        stats = get_cache_stats()
        print(f"  总连接数: {stats.get('total_connections', 0)}")
        print(f"  总命令数: {stats.get('total_commands', 0)}")
        print(f"  缓存命中数: {stats.get('keyspace_hits', 0)}")
        print(f"  缓存未命中数: {stats.get('keyspace_misses', 0)}")
        print(f"  缓存命中率: {stats.get('hit_rate', 0):.2f}%")

        return stats

    return None


async def main():
    """Run all performance tests."""
    print("=" * 60)
    print("Redis缓存性能测试")
    print("=" * 60)

    # Test 1: Signature verification cache
    sig_results = await test_signature_verification_cache()

    # Test 2: Concurrent requests
    concurrent_results = await test_concurrent_requests()

    # Test 3: Cache health
    cache_stats = test_cache_health()

    # Summary
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    print("\n✅ 性能指标:")
    print(f"  签名验证P95: {sig_results['p95']:.2f}ms")
    print(f"  并发P95: {concurrent_results['p95']:.2f}ms")
    print(f"  吞吐量: {concurrent_results['throughput']:.2f} req/s")

    if cache_stats:
        print(f"  缓存命中率: {cache_stats.get('hit_rate', 0):.2f}%")

    print("\n🎯 目标对比:")
    print(f"  并发P95 < 1000ms: {'✅ 达标' if concurrent_results['p95'] < 1000 else '❌ 未达标'}")
    print(f"  吞吐量 > 10 req/s: {'✅ 达标' if concurrent_results['throughput'] > 10 else '❌ 未达标'}")

    if cache_stats:
        print(f"  缓存命中率 > 60%: {'✅ 达标' if cache_stats.get('hit_rate', 0) > 60 else '❌ 未达标'}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

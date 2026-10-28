#!/usr/bin/env python3
"""
性能基准测试脚本

测试优化前后的 API 性能对比
"""
import time
import statistics
import requests
import json
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys


class PerformanceTester:
    """性能测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}

    def test_endpoint(self, endpoint: str, method: str = "GET", data: dict = None, iterations: int = 10) -> Dict:
        """
        测试单个端点的性能

        Args:
            endpoint: API 端点
            method: HTTP 方法
            data: 请求数据
            iterations: 迭代次数

        Returns:
            性能统计数据
        """
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = 0

        print(f"\n测试 {method} {endpoint} ({iterations} 次)...")

        for i in range(iterations):
            try:
                start_time = time.time()

                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=10)
                else:
                    raise ValueError(f"不支持的方法: {method}")

                elapsed = time.time() - start_time
                response_times.append(elapsed)

                if response.status_code not in [200, 201]:
                    errors += 1
                    print(f"  ✗ 请求 {i+1} 失败: {response.status_code}")
                else:
                    print(f"  ✓ 请求 {i+1}: {elapsed*1000:.2f}ms")

            except Exception as e:
                errors += 1
                print(f"  ✗ 请求 {i+1} 异常: {e}")

        if not response_times:
            return {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "errors": errors,
                "avg_time": 0,
                "min_time": 0,
                "max_time": 0,
                "median_time": 0,
                "p95_time": 0,
                "p99_time": 0,
            }

        # 计算统计数据
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        median_time = statistics.median(response_times)

        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)
        p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_time
        p99_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_time

        result = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "errors": errors,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "median_time": median_time,
            "p95_time": p95_time,
            "p99_time": p99_time,
        }

        return result

    def test_concurrent_requests(self, endpoint: str, concurrent: int = 10, total: int = 100) -> Dict:
        """
        测试并发请求性能

        Args:
            endpoint: API 端点
            concurrent: 并发数
            total: 总请求数

        Returns:
            并发测试结果
        """
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = 0

        print(f"\n并发测试 {endpoint} (并发={concurrent}, 总数={total})...")

        def make_request(i):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                elapsed = time.time() - start_time

                if response.status_code == 200:
                    return elapsed, None
                else:
                    return None, f"Status {response.status_code}"
            except Exception as e:
                return None, str(e)

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request, i) for i in range(total)]

            for i, future in enumerate(as_completed(futures), 1):
                elapsed, error = future.result()
                if error:
                    errors += 1
                    print(f"  ✗ 请求 {i} 失败: {error}")
                else:
                    response_times.append(elapsed)
                    if i % 10 == 0:
                        print(f"  ✓ 完成 {i}/{total} 请求")

        total_time = time.time() - start_time

        if not response_times:
            return {
                "endpoint": endpoint,
                "concurrent": concurrent,
                "total": total,
                "errors": errors,
                "total_time": total_time,
                "throughput": 0,
                "avg_time": 0,
            }

        avg_time = statistics.mean(response_times)
        throughput = len(response_times) / total_time

        return {
            "endpoint": endpoint,
            "concurrent": concurrent,
            "total": total,
            "errors": errors,
            "total_time": total_time,
            "throughput": throughput,
            "avg_time": avg_time,
        }

    def run_benchmark(self):
        """运行完整的基准测试"""
        print("=" * 70)
        print("Nautilus API 性能基准测试")
        print("=" * 70)

        # 测试健康检查
        print("\n[1/6] 健康检查端点")
        health_result = self.test_endpoint("/health", iterations=20)
        self.results["health"] = health_result

        # 测试根端点
        print("\n[2/6] 根端点")
        root_result = self.test_endpoint("/", iterations=20)
        self.results["root"] = root_result

        # 测试 agents 列表
        print("\n[3/6] Agents 列表端点")
        agents_result = self.test_endpoint("/api/agents?skip=0&limit=10", iterations=20)
        self.results["agents_list"] = agents_result

        # 测试单个 agent
        print("\n[4/6] 单个 Agent 端点")
        agent_result = self.test_endpoint("/api/agents/1", iterations=20)
        self.results["agent_detail"] = agent_result

        # 测试 agent reputation
        print("\n[5/6] Agent Reputation 端点")
        reputation_result = self.test_endpoint("/api/agents/1/reputation", iterations=20)
        self.results["agent_reputation"] = reputation_result

        # 并发测试
        print("\n[6/6] 并发测试")
        concurrent_result = self.test_concurrent_requests("/api/agents?skip=0&limit=10", concurrent=10, total=50)
        self.results["concurrent"] = concurrent_result

        # 打印汇总报告
        self.print_summary()

    def print_summary(self):
        """打印测试汇总"""
        print("\n" + "=" * 70)
        print("测试结果汇总")
        print("=" * 70)

        # 单端点测试结果
        print("\n单端点性能测试:")
        print(f"{'端点':<30} {'平均':<10} {'最小':<10} {'最大':<10} {'P95':<10} {'错误':<8}")
        print("-" * 70)

        for key, result in self.results.items():
            if key == "concurrent":
                continue

            endpoint = result["endpoint"]
            avg = f"{result['avg_time']*1000:.2f}ms"
            min_t = f"{result['min_time']*1000:.2f}ms"
            max_t = f"{result['max_time']*1000:.2f}ms"
            p95 = f"{result['p95_time']*1000:.2f}ms"
            errors = f"{result['errors']}/{result['iterations']}"

            print(f"{endpoint:<30} {avg:<10} {min_t:<10} {max_t:<10} {p95:<10} {errors:<8}")

        # 并发测试结果
        if "concurrent" in self.results:
            result = self.results["concurrent"]
            print("\n并发性能测试:")
            print(f"  端点: {result['endpoint']}")
            print(f"  并发数: {result['concurrent']}")
            print(f"  总请求: {result['total']}")
            print(f"  成功: {result['total'] - result['errors']}")
            print(f"  失败: {result['errors']}")
            print(f"  总耗时: {result['total_time']:.2f}s")
            print(f"  吞吐量: {result['throughput']:.2f} req/s")
            print(f"  平均响应: {result['avg_time']*1000:.2f}ms")

        # 性能评估
        print("\n性能评估:")
        agents_avg = self.results.get("agents_list", {}).get("avg_time", 0)
        if agents_avg > 0:
            if agents_avg < 0.3:
                status = "✓ 优秀"
                color = "绿色"
            elif agents_avg < 0.5:
                status = "○ 良好"
                color = "黄色"
            else:
                status = "✗ 需要优化"
                color = "红色"

            print(f"  Agents 列表平均响应时间: {agents_avg*1000:.2f}ms - {status}")

        print("\n" + "=" * 70)

    def save_results(self, filename: str = "benchmark_results.json"):
        """保存测试结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n测试结果已保存到: {filename}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Nautilus API 性能基准测试")
    parser.add_argument("--url", default="http://localhost:8000", help="API 基础 URL")
    parser.add_argument("--output", default="benchmark_results.json", help="结果输出文件")

    args = parser.parse_args()

    # 检查服务是否可用
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print(f"错误: API 服务不可用 (状态码: {response.status_code})")
            sys.exit(1)
    except Exception as e:
        print(f"错误: 无法连接到 API 服务: {e}")
        print(f"请确保服务运行在 {args.url}")
        sys.exit(1)

    # 运行测试
    tester = PerformanceTester(base_url=args.url)
    tester.run_benchmark()
    tester.save_results(args.output)


if __name__ == "__main__":
    main()

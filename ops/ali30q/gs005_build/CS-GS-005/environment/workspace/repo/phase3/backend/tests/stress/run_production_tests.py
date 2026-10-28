"""
生产压力测试运行脚本

提供便捷的方式运行不同级别的生产压力测试。

使用方式:
    python run_production_tests.py --level light
    python run_production_tests.py --level medium
    python run_production_tests.py --level heavy
    python run_production_tests.py --level peak

版本: 1.0.0
创建时间: 2026-02-27
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime
import json
from pathlib import Path

# 测试场景配置
TEST_SCENARIOS = {
    "light": {
        "name": "轻负载测试",
        "description": "100并发用户，适合初步验证",
        "users": 100,
        "spawn_rate": 10,
        "run_time": "10m",
        "expected_p95": "< 200ms",
        "expected_throughput": "> 100 req/s",
        "expected_error_rate": "< 0.1%"
    },
    "medium": {
        "name": "中负载测试",
        "description": "500并发用户，模拟正常生产负载",
        "users": 500,
        "spawn_rate": 50,
        "run_time": "15m",
        "expected_p95": "< 300ms",
        "expected_throughput": "> 500 req/s",
        "expected_error_rate": "< 0.5%"
    },
    "heavy": {
        "name": "重负载测试",
        "description": "1000并发用户，测试系统极限",
        "users": 1000,
        "spawn_rate": 100,
        "run_time": "20m",
        "expected_p95": "< 500ms",
        "expected_throughput": "> 800 req/s",
        "expected_error_rate": "< 1%"
    },
    "peak": {
        "name": "峰值负载测试",
        "description": "2000并发用户，极限压力测试",
        "users": 2000,
        "spawn_rate": 200,
        "run_time": "15m",
        "expected_p95": "< 1000ms",
        "expected_throughput": "> 1000 req/s",
        "expected_error_rate": "< 2%"
    },
    "endurance": {
        "name": "耐久测试",
        "description": "长时间稳定负载，测试内存泄漏",
        "users": 200,
        "spawn_rate": 20,
        "run_time": "60m",
        "expected_p95": "< 300ms",
        "expected_throughput": "> 200 req/s",
        "expected_error_rate": "< 0.5%"
    }
}


def print_scenario_info(scenario_name: str):
    """打印场景信息"""
    if scenario_name not in TEST_SCENARIOS:
        print(f"错误: 未知场景 '{scenario_name}'")
        print(f"可用场景: {', '.join(TEST_SCENARIOS.keys())}")
        sys.exit(1)

    scenario = TEST_SCENARIOS[scenario_name]
    print("=" * 70)
    print(f"场景: {scenario['name']}")
    print("=" * 70)
    print(f"描述: {scenario['description']}")
    print(f"并发用户数: {scenario['users']}")
    print(f"启动速率: {scenario['spawn_rate']} 用户/秒")
    print(f"运行时间: {scenario['run_time']}")
    print(f"\n预期性能指标:")
    print(f"  - P95响应时间: {scenario['expected_p95']}")
    print(f"  - 吞吐量: {scenario['expected_throughput']}")
    print(f"  - 错误率: {scenario['expected_error_rate']}")
    print("=" * 70)


def run_load_test(scenario_name: str, host: str = "http://localhost:8000", headless: bool = True):
    """运行负载测试"""

    # 验证场景
    if scenario_name not in TEST_SCENARIOS:
        print(f"错误: 未知场景 '{scenario_name}'")
        print(f"可用场景: {', '.join(TEST_SCENARIOS.keys())}")
        sys.exit(1)

    scenario = TEST_SCENARIOS[scenario_name]

    # 打印场景信息
    print_scenario_info(scenario_name)
    print(f"\n目标主机: {host}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 确保输出目录存在
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    # 生成输出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_prefix = output_dir / f"production_{scenario_name}_{timestamp}"
    html_report = output_dir / f"production_{scenario_name}_{timestamp}.html"

    # 构建Locust命令
    locust_file = Path(__file__).parent / "production_load_test.py"
    cmd = [
        "locust",
        "-f", str(locust_file),
        "--host", host,
        "--users", str(scenario["users"]),
        "--spawn-rate", str(scenario["spawn_rate"]),
        "--run-time", scenario["run_time"]
    ]

    # 无头模式
    if headless:
        cmd.append("--headless")

    # CSV输出
    cmd.extend(["--csv", str(csv_prefix)])

    # HTML报告
    cmd.extend(["--html", str(html_report)])

    # 日志级别
    cmd.extend(["--loglevel", "INFO"])

    # 运行测试
    print(f"运行命令: {' '.join(cmd)}\n")
    print("=" * 70)

    try:
        result = subprocess.run(cmd, check=True)
        print("=" * 70)
        print(f"\n✓ 测试完成！")
        print(f"\n报告文件:")
        print(f"  - HTML报告: {html_report}")
        print(f"  - CSV数据: {csv_prefix}_stats.csv")
        print(f"  - 失败记录: {csv_prefix}_failures.csv")
        print(f"  - 异常记录: {csv_prefix}_exceptions.csv")

        # 分析结果
        analyze_results(csv_prefix, scenario)

        return 0
    except subprocess.CalledProcessError as e:
        print("=" * 70)
        print(f"\n✗ 测试失败: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 130


def analyze_results(csv_prefix: Path, scenario: dict):
    """分析测试结果"""
    stats_file = Path(f"{csv_prefix}_stats.csv")

    if not stats_file.exists():
        print("\n⚠ 无法找到统计文件，跳过结果分析")
        return

    print("\n" + "=" * 70)
    print("结果分析")
    print("=" * 70)

    try:
        import csv
        with open(stats_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if not rows:
                print("无统计数据")
                return

            # 获取汇总行（通常是最后一行）
            summary = rows[-1]

            total_requests = int(summary.get('Request Count', 0))
            failure_count = int(summary.get('Failure Count', 0))
            avg_response = float(summary.get('Average Response Time', 0))
            p95_response = float(summary.get('95%', 0))
            p99_response = float(summary.get('99%', 0))
            rps = float(summary.get('Requests/s', 0))

            error_rate = (failure_count / total_requests * 100) if total_requests > 0 else 0

            print(f"\n整体性能:")
            print(f"  总请求数: {total_requests:,}")
            print(f"  失败请求: {failure_count:,}")
            print(f"  错误率: {error_rate:.3f}%")
            print(f"  吞吐量: {rps:.2f} req/s")
            print(f"\n响应时间:")
            print(f"  平均: {avg_response:.2f}ms")
            print(f"  P95: {p95_response:.2f}ms")
            print(f"  P99: {p99_response:.2f}ms")

            # 性能基准验证
            print(f"\n性能基准验证:")

            # 解析预期值
            expected_p95 = float(scenario['expected_p95'].replace('< ', '').replace('ms', ''))
            expected_throughput = float(scenario['expected_throughput'].replace('> ', '').replace(' req/s', ''))
            expected_error_rate = float(scenario['expected_error_rate'].replace('< ', '').replace('%', ''))

            p95_pass = p95_response < expected_p95
            throughput_pass = rps > expected_throughput
            error_rate_pass = error_rate < expected_error_rate

            print(f"  P95响应时间 {scenario['expected_p95']}: {'✓ 通过' if p95_pass else '✗ 未达标'} ({p95_response:.2f}ms)")
            print(f"  吞吐量 {scenario['expected_throughput']}: {'✓ 通过' if throughput_pass else '✗ 未达标'} ({rps:.2f} req/s)")
            print(f"  错误率 {scenario['expected_error_rate']}: {'✓ 通过' if error_rate_pass else '✗ 未达标'} ({error_rate:.3f}%)")

            all_pass = p95_pass and throughput_pass and error_rate_pass
            print(f"\n总体评估: {'✓ 所有指标达标' if all_pass else '✗ 部分指标未达标'}")

            # 端点性能分析
            print(f"\n端点性能 (Top 10):")
            print(f"{'端点':<40} {'请求数':>10} {'平均(ms)':>12} {'P95(ms)':>10} {'失败':>8}")
            print("-" * 85)

            # 排除汇总行，按请求数排序
            endpoint_rows = [r for r in rows[:-1] if r.get('Name') != 'Aggregated']
            endpoint_rows.sort(key=lambda x: int(x.get('Request Count', 0)), reverse=True)

            for row in endpoint_rows[:10]:
                name = row.get('Name', 'Unknown')[:38]
                count = int(row.get('Request Count', 0))
                avg = float(row.get('Average Response Time', 0))
                p95 = float(row.get('95%', 0))
                failures = int(row.get('Failure Count', 0))

                print(f"{name:<40} {count:>10,} {avg:>12.2f} {p95:>10.2f} {failures:>8}")

    except Exception as e:
        print(f"\n⚠ 结果分析失败: {e}")


def list_scenarios():
    """列出所有可用场景"""
    print("\n可用的压力测试场景:\n")
    for name, config in TEST_SCENARIOS.items():
        print(f"  {name:12} - {config['name']}")
        print(f"               {config['description']}")
        print(f"               用户数: {config['users']}, 运行时间: {config['run_time']}")
        print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生产环境压力测试运行器")
    parser.add_argument(
        '--level',
        choices=list(TEST_SCENARIOS.keys()),
        help='测试级别'
    )
    parser.add_argument(
        '--host',
        default='http://localhost:8000',
        help='目标主机 (默认: http://localhost:8000)'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='使用Web界面模式'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用场景'
    )

    args = parser.parse_args()

    if args.list:
        list_scenarios()
        return 0

    if not args.level:
        print("错误: 必须指定测试级别")
        print("\n使用 --list 查看可用场景")
        print("\n示例:")
        print("  python run_production_tests.py --level light")
        print("  python run_production_tests.py --level medium --host http://staging.example.com")
        return 1

    # 运行测试
    return run_load_test(
        scenario_name=args.level,
        host=args.host,
        headless=not args.no_headless
    )


if __name__ == "__main__":
    sys.exit(main())

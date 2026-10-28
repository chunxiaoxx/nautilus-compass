"""
比较压力测试结果的工具

用于对比不同时间点的测试结果，识别性能退化或改进。

使用方式:
    python compare_load_test_results.py results/test1_stats.csv results/test2_stats.csv
"""

import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple


def load_stats(csv_path: str) -> Dict[str, Dict]:
    """加载统计CSV文件"""
    stats = {}

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Name', row.get('name', ''))
                if name and name != 'Aggregated':
                    stats[name] = {
                        'requests': int(row.get('Request Count', row.get('requests', 0))),
                        'failures': int(row.get('Failure Count', row.get('failures', 0))),
                        'avg_response': float(row.get('Average Response Time', row.get('avg_response_time', 0))),
                        'min_response': float(row.get('Min Response Time', row.get('min_response_time', 0))),
                        'max_response': float(row.get('Max Response Time', row.get('max_response_time', 0))),
                        'median_response': float(row.get('Median Response Time', row.get('median_response_time', 0))),
                        'rps': float(row.get('Requests/s', row.get('rps', 0))),
                    }
    except Exception as e:
        print(f"错误: 无法读取文件 {csv_path}: {e}")
        sys.exit(1)

    return stats


def calculate_change(old_value: float, new_value: float) -> Tuple[float, str]:
    """计算变化百分比和状态"""
    if old_value == 0:
        return 0.0, "N/A"

    change = ((new_value - old_value) / old_value) * 100

    if abs(change) < 5:
        status = "→"  # 基本不变
    elif change > 0:
        status = "↑"  # 增加
    else:
        status = "↓"  # 减少

    return change, status


def compare_stats(old_stats: Dict, new_stats: Dict) -> None:
    """比较两组统计数据"""

    print("\n" + "=" * 100)
    print("压力测试结果对比")
    print("=" * 100)

    # 获取所有端点
    all_endpoints = set(old_stats.keys()) | set(new_stats.keys())

    if not all_endpoints:
        print("错误: 没有找到可比较的数据")
        return

    # 打印表头
    print(f"\n{'端点':<40} {'指标':<20} {'旧值':<15} {'新值':<15} {'变化':<15} {'状态':<5}")
    print("-" * 100)

    for endpoint in sorted(all_endpoints):
        old = old_stats.get(endpoint)
        new = new_stats.get(endpoint)

        if not old:
            print(f"{endpoint:<40} {'新增端点':<20} {'-':<15} {'-':<15} {'-':<15} {'+':<5}")
            continue

        if not new:
            print(f"{endpoint:<40} {'已移除端点':<20} {'-':<15} {'-':<15} {'-':<15} {'-':<5}")
            continue

        # 比较各项指标
        metrics = [
            ('请求数', old['requests'], new['requests'], False),
            ('失败数', old['failures'], new['failures'], True),
            ('平均响应时间(ms)', old['avg_response'], new['avg_response'], True),
            ('中位数响应时间(ms)', old['median_response'], new['median_response'], True),
            ('最大响应时间(ms)', old['max_response'], new['max_response'], True),
            ('RPS', old['rps'], new['rps'], False),
        ]

        first_metric = True
        for metric_name, old_val, new_val, lower_is_better in metrics:
            change, status = calculate_change(old_val, new_val)

            # 确定是改进还是退化
            if abs(change) >= 5:
                if lower_is_better:
                    # 对于响应时间和失败数，越低越好
                    if change < 0:
                        status += " ✓"  # 改进
                    else:
                        status += " ✗"  # 退化
                else:
                    # 对于请求数和RPS，越高越好
                    if change > 0:
                        status += " ✓"  # 改进
                    else:
                        status += " ✗"  # 退化

            endpoint_name = endpoint if first_metric else ""
            change_str = f"{change:+.1f}%" if change != 0 else "0.0%"

            print(f"{endpoint_name:<40} {metric_name:<20} {old_val:<15.2f} {new_val:<15.2f} {change_str:<15} {status:<5}")
            first_metric = False

        print("-" * 100)

    # 总体摘要
    print("\n" + "=" * 100)
    print("总体摘要")
    print("=" * 100)

    # 计算总体指标
    old_total_requests = sum(s['requests'] for s in old_stats.values())
    new_total_requests = sum(s['requests'] for s in new_stats.values())

    old_total_failures = sum(s['failures'] for s in old_stats.values())
    new_total_failures = sum(s['failures'] for s in new_stats.values())

    old_avg_response = sum(s['avg_response'] * s['requests'] for s in old_stats.values()) / old_total_requests if old_total_requests > 0 else 0
    new_avg_response = sum(s['avg_response'] * s['requests'] for s in new_stats.values()) / new_total_requests if new_total_requests > 0 else 0

    old_error_rate = (old_total_failures / old_total_requests * 100) if old_total_requests > 0 else 0
    new_error_rate = (new_total_failures / new_total_requests * 100) if new_total_requests > 0 else 0

    print(f"\n总请求数: {old_total_requests} → {new_total_requests} ({calculate_change(old_total_requests, new_total_requests)[0]:+.1f}%)")
    print(f"总失败数: {old_total_failures} → {new_total_failures} ({calculate_change(old_total_failures, new_total_failures)[0]:+.1f}%)")
    print(f"平均响应时间: {old_avg_response:.2f}ms → {new_avg_response:.2f}ms ({calculate_change(old_avg_response, new_avg_response)[0]:+.1f}%)")
    print(f"错误率: {old_error_rate:.2f}% → {new_error_rate:.2f}% ({calculate_change(old_error_rate, new_error_rate)[0]:+.1f}%)")

    # 性能评估
    print("\n" + "=" * 100)
    print("性能评估")
    print("=" * 100)

    improvements = []
    regressions = []

    for endpoint in all_endpoints:
        old = old_stats.get(endpoint)
        new = new_stats.get(endpoint)

        if old and new:
            # 检查响应时间
            response_change = calculate_change(old['avg_response'], new['avg_response'])[0]
            if response_change < -10:  # 改进超过10%
                improvements.append(f"  ✓ {endpoint}: 响应时间改进 {abs(response_change):.1f}%")
            elif response_change > 10:  # 退化超过10%
                regressions.append(f"  ✗ {endpoint}: 响应时间退化 {response_change:.1f}%")

            # 检查错误率
            old_error_rate = (old['failures'] / old['requests'] * 100) if old['requests'] > 0 else 0
            new_error_rate = (new['failures'] / new['requests'] * 100) if new['requests'] > 0 else 0
            error_change = new_error_rate - old_error_rate

            if error_change > 1:  # 错误率增加超过1%
                regressions.append(f"  ✗ {endpoint}: 错误率增加 {error_change:.2f}%")

    if improvements:
        print("\n改进项:")
        for item in improvements:
            print(item)

    if regressions:
        print("\n退化项:")
        for item in regressions:
            print(item)

    if not improvements and not regressions:
        print("\n性能基本保持稳定")

    print("\n" + "=" * 100)


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python compare_load_test_results.py <旧测试结果.csv> <新测试结果.csv>")
        print("\n示例:")
        print("  python compare_load_test_results.py results/test1_stats.csv results/test2_stats.csv")
        sys.exit(1)

    old_csv = sys.argv[1]
    new_csv = sys.argv[2]

    # 检查文件是否存在
    if not Path(old_csv).exists():
        print(f"错误: 文件不存在: {old_csv}")
        sys.exit(1)

    if not Path(new_csv).exists():
        print(f"错误: 文件不存在: {new_csv}")
        sys.exit(1)

    print(f"\n对比测试结果:")
    print(f"  旧测试: {old_csv}")
    print(f"  新测试: {new_csv}")

    # 加载数据
    old_stats = load_stats(old_csv)
    new_stats = load_stats(new_csv)

    # 比较数据
    compare_stats(old_stats, new_stats)


if __name__ == "__main__":
    main()

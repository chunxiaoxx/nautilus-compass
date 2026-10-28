"""
压力测试分析工具

分析压力测试结果，生成详细的性能报告。

功能:
- 解析Locust CSV结果
- 分析性能指标
- 识别性能瓶颈
- 生成对比报告

使用方式:
    python analyze_test_results.py --csv results/production_light_20260227_143000_stats.csv

版本: 1.0.0
创建时间: 2026-02-27
"""

import csv
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys


class TestResultAnalyzer:
    """测试结果分析器"""

    def __init__(self, csv_file: Path):
        self.csv_file = csv_file
        self.stats = []
        self.summary = {}
        self.endpoints = []

    def load_data(self):
        """加载CSV数据"""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"文件不存在: {self.csv_file}")

        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.stats = list(reader)

        if not self.stats:
            raise ValueError("CSV文件为空")

        # 最后一行通常是汇总数据
        self.summary = self.stats[-1]
        # 其他行是各个端点的数据
        self.endpoints = [s for s in self.stats[:-1] if s.get('Name') != 'Aggregated']

    def analyze(self) -> Dict[str, Any]:
        """分析数据"""
        analysis = {
            'overall': self.analyze_overall(),
            'endpoints': self.analyze_endpoints(),
            'bottlenecks': self.identify_bottlenecks(),
            'recommendations': self.generate_recommendations()
        }
        return analysis

    def analyze_overall(self) -> Dict[str, Any]:
        """分析整体性能"""
        total_requests = int(self.summary.get('Request Count', 0))
        failure_count = int(self.summary.get('Failure Count', 0))
        avg_response = float(self.summary.get('Average Response Time', 0))
        min_response = float(self.summary.get('Min Response Time', 0))
        max_response = float(self.summary.get('Max Response Time', 0))
        median_response = float(self.summary.get('Median Response Time', 0))
        p95_response = float(self.summary.get('95%', 0))
        p99_response = float(self.summary.get('99%', 0))
        rps = float(self.summary.get('Requests/s', 0))

        error_rate = (failure_count / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_requests': total_requests,
            'failure_count': failure_count,
            'error_rate': error_rate,
            'throughput_rps': rps,
            'response_times': {
                'min': min_response,
                'avg': avg_response,
                'median': median_response,
                'p95': p95_response,
                'p99': p99_response,
                'max': max_response
            }
        }

    def analyze_endpoints(self) -> List[Dict[str, Any]]:
        """分析各端点性能"""
        endpoint_analysis = []

        for endpoint in self.endpoints:
            name = endpoint.get('Name', 'Unknown')
            count = int(endpoint.get('Request Count', 0))
            failures = int(endpoint.get('Failure Count', 0))
            avg = float(endpoint.get('Average Response Time', 0))
            min_time = float(endpoint.get('Min Response Time', 0))
            max_time = float(endpoint.get('Max Response Time', 0))
            median = float(endpoint.get('Median Response Time', 0))
            p95 = float(endpoint.get('95%', 0))
            p99 = float(endpoint.get('99%', 0))

            error_rate = (failures / count * 100) if count > 0 else 0

            endpoint_analysis.append({
                'name': name,
                'request_count': count,
                'failure_count': failures,
                'error_rate': error_rate,
                'response_times': {
                    'min': min_time,
                    'avg': avg,
                    'median': median,
                    'p95': p95,
                    'p99': p99,
                    'max': max_time
                }
            })

        # 按请求数排序
        endpoint_analysis.sort(key=lambda x: x['request_count'], reverse=True)
        return endpoint_analysis

    def identify_bottlenecks(self) -> Dict[str, Any]:
        """识别性能瓶颈"""
        bottlenecks = {
            'slow_endpoints': [],
            'high_error_endpoints': [],
            'high_variance_endpoints': []
        }

        for endpoint in self.endpoints:
            name = endpoint.get('Name', 'Unknown')
            avg = float(endpoint.get('Average Response Time', 0))
            p95 = float(endpoint.get('95%', 0))
            failures = int(endpoint.get('Failure Count', 0))
            count = int(endpoint.get('Request Count', 0))
            error_rate = (failures / count * 100) if count > 0 else 0

            # 慢端点 (P95 > 500ms)
            if p95 > 500:
                bottlenecks['slow_endpoints'].append({
                    'name': name,
                    'p95': p95,
                    'avg': avg
                })

            # 高错误率端点 (错误率 > 1%)
            if error_rate > 1.0:
                bottlenecks['high_error_endpoints'].append({
                    'name': name,
                    'error_rate': error_rate,
                    'failures': failures,
                    'total': count
                })

            # 高方差端点 (P95 > 2 * avg)
            if avg > 0 and p95 > 2 * avg:
                bottlenecks['high_variance_endpoints'].append({
                    'name': name,
                    'avg': avg,
                    'p95': p95,
                    'variance_ratio': p95 / avg
                })

        # 排序
        bottlenecks['slow_endpoints'].sort(key=lambda x: x['p95'], reverse=True)
        bottlenecks['high_error_endpoints'].sort(key=lambda x: x['error_rate'], reverse=True)
        bottlenecks['high_variance_endpoints'].sort(key=lambda x: x['variance_ratio'], reverse=True)

        return bottlenecks

    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        overall = self.analyze_overall()
        bottlenecks = self.identify_bottlenecks()

        # 基于错误率的建议
        if overall['error_rate'] > 1.0:
            recommendations.append(
                f"错误率较高 ({overall['error_rate']:.2f}%)，建议检查应用日志和错误处理逻辑"
            )

        # 基于响应时间的建议
        if overall['response_times']['p95'] > 500:
            recommendations.append(
                f"P95响应时间较高 ({overall['response_times']['p95']:.2f}ms)，建议优化数据库查询和缓存策略"
            )

        if overall['response_times']['p99'] > 1000:
            recommendations.append(
                f"P99响应时间过高 ({overall['response_times']['p99']:.2f}ms)，存在严重的性能问题"
            )

        # 基于吞吐量的建议
        if overall['throughput_rps'] < 100:
            recommendations.append(
                f"吞吐量较低 ({overall['throughput_rps']:.2f} req/s)，建议增加服务器资源或优化应用性能"
            )

        # 基于瓶颈的建议
        if bottlenecks['slow_endpoints']:
            slow_count = len(bottlenecks['slow_endpoints'])
            recommendations.append(
                f"发现 {slow_count} 个慢端点，建议优化这些端点的性能"
            )

        if bottlenecks['high_error_endpoints']:
            error_count = len(bottlenecks['high_error_endpoints'])
            recommendations.append(
                f"发现 {error_count} 个高错误率端点，建议检查这些端点的错误处理"
            )

        if bottlenecks['high_variance_endpoints']:
            variance_count = len(bottlenecks['high_variance_endpoints'])
            recommendations.append(
                f"发现 {variance_count} 个高方差端点，响应时间不稳定，建议检查资源竞争和锁问题"
            )

        # 通用建议
        if not recommendations:
            recommendations.append("整体性能良好，继续保持")

        return recommendations

    def print_report(self, analysis: Dict[str, Any]):
        """打印分析报告"""
        print("=" * 70)
        print("压力测试结果分析报告")
        print("=" * 70)
        print(f"测试文件: {self.csv_file.name}")
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        # 整体性能
        overall = analysis['overall']
        print("整体性能:")
        print(f"  总请求数: {overall['total_requests']:,}")
        print(f"  失败请求: {overall['failure_count']:,}")
        print(f"  错误率: {overall['error_rate']:.3f}%")
        print(f"  吞吐量: {overall['throughput_rps']:.2f} req/s")
        print()

        print("响应时间:")
        rt = overall['response_times']
        print(f"  最小: {rt['min']:.2f}ms")
        print(f"  平均: {rt['avg']:.2f}ms")
        print(f"  中位数: {rt['median']:.2f}ms")
        print(f"  P95: {rt['p95']:.2f}ms")
        print(f"  P99: {rt['p99']:.2f}ms")
        print(f"  最大: {rt['max']:.2f}ms")
        print()

        # 端点性能 (Top 10)
        endpoints = analysis['endpoints'][:10]
        print("端点性能 (Top 10):")
        print(f"{'端点':<40} {'请求数':>10} {'平均(ms)':>12} {'P95(ms)':>10} {'错误率':>10}")
        print("-" * 85)
        for ep in endpoints:
            name = ep['name'][:38]
            count = ep['request_count']
            avg = ep['response_times']['avg']
            p95 = ep['response_times']['p95']
            error_rate = ep['error_rate']
            print(f"{name:<40} {count:>10,} {avg:>12.2f} {p95:>10.2f} {error_rate:>9.2f}%")
        print()

        # 性能瓶颈
        bottlenecks = analysis['bottlenecks']
        print("性能瓶颈分析:")
        print()

        if bottlenecks['slow_endpoints']:
            print(f"  慢端点 ({len(bottlenecks['slow_endpoints'])} 个):")
            for ep in bottlenecks['slow_endpoints'][:5]:
                print(f"    - {ep['name']}: P95={ep['p95']:.2f}ms, 平均={ep['avg']:.2f}ms")
            print()

        if bottlenecks['high_error_endpoints']:
            print(f"  高错误率端点 ({len(bottlenecks['high_error_endpoints'])} 个):")
            for ep in bottlenecks['high_error_endpoints'][:5]:
                print(f"    - {ep['name']}: 错误率={ep['error_rate']:.2f}%, 失败={ep['failures']}/{ep['total']}")
            print()

        if bottlenecks['high_variance_endpoints']:
            print(f"  高方差端点 ({len(bottlenecks['high_variance_endpoints'])} 个):")
            for ep in bottlenecks['high_variance_endpoints'][:5]:
                print(f"    - {ep['name']}: P95/平均={ep['variance_ratio']:.2f}x")
            print()

        if not any(bottlenecks.values()):
            print("  未发现明显的性能瓶颈")
            print()

        # 优化建议
        recommendations = analysis['recommendations']
        print("优化建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        print()

        print("=" * 70)

    def save_report(self, analysis: Dict[str, Any], output_file: Path):
        """保存分析报告"""
        report = {
            'metadata': {
                'source_file': str(self.csv_file),
                'analysis_time': datetime.now().isoformat()
            },
            'analysis': analysis
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"分析报告已保存到: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="压力测试结果分析工具")
    parser.add_argument(
        '--csv',
        required=True,
        help='Locust CSV统计文件路径'
    )
    parser.add_argument(
        '--output',
        help='输出JSON报告文件路径（可选）'
    )

    args = parser.parse_args()

    csv_file = Path(args.csv)
    if not csv_file.exists():
        print(f"错误: 文件不存在: {csv_file}")
        return 1

    try:
        # 创建分析器
        analyzer = TestResultAnalyzer(csv_file)

        # 加载数据
        analyzer.load_data()

        # 分析
        analysis = analyzer.analyze()

        # 打印报告
        analyzer.print_report(analysis)

        # 保存报告
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = csv_file.parent / f"{csv_file.stem}_analysis.json"

        analyzer.save_report(analysis, output_file)

        return 0

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

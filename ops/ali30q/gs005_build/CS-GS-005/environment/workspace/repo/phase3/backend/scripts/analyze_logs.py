"""
日志分析脚本
用于分析应用日志，提供错误统计、性能分析和异常检测
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional
import argparse


class LogAnalyzer:
    """日志分析器"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.logs = []

    def load_json_logs(self, log_file: str, max_lines: Optional[int] = None) -> List[Dict]:
        """加载JSON格式的日志文件"""
        logs = []
        log_path = self.log_dir / log_file

        if not log_path.exists():
            print(f"警告: 日志文件不存在: {log_path}")
            return logs

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if max_lines and i >= max_lines:
                        break
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"错误: 无法读取日志文件 {log_path}: {e}")

        return logs

    def analyze_errors(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """分析错误日志"""
        print(f"\n{'='*60}")
        print("错误分析报告")
        print(f"{'='*60}")

        # 加载错误日志
        error_logs = self.load_json_logs("nautilus.error.json.log")

        if not error_logs:
            print("没有找到错误日志")
            return {}

        # 时间过滤
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
        filtered_logs = []

        for log in error_logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                if log_time >= cutoff_time:
                    filtered_logs.append(log)
            except (KeyError, ValueError):
                continue

        if not filtered_logs:
            print(f"最近 {time_range_hours} 小时内没有错误日志")
            return {}

        # 统计错误类型
        error_types = Counter()
        error_messages = defaultdict(list)
        error_sources = Counter()
        error_timeline = defaultdict(int)

        for log in filtered_logs:
            # 错误类型统计
            if 'exception' in log and 'type' in log['exception']:
                error_type = log['exception']['type']
                error_types[error_type] += 1
                error_messages[error_type].append(log.get('message', 'N/A'))

            # 错误来源统计
            if 'source' in log:
                source = f"{log['source'].get('file', 'unknown')}:{log['source'].get('line', 0)}"
                error_sources[source] += 1

            # 时间线统计（按小时）
            try:
                log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                hour_key = log_time.strftime('%Y-%m-%d %H:00')
                error_timeline[hour_key] += 1
            except (KeyError, ValueError):
                continue

        # 输出统计结果
        print(f"\n总错误数: {len(filtered_logs)}")
        print(f"时间范围: 最近 {time_range_hours} 小时")

        print(f"\n{'='*60}")
        print("错误类型 Top 10:")
        print(f"{'='*60}")
        for error_type, count in error_types.most_common(10):
            percentage = (count / len(filtered_logs)) * 100
            print(f"{error_type:40} {count:5} ({percentage:.1f}%)")
            # 显示该类型的前3个错误消息
            for msg in error_messages[error_type][:3]:
                print(f"  └─ {msg[:80]}")

        print(f"\n{'='*60}")
        print("错误来源 Top 10:")
        print(f"{'='*60}")
        for source, count in error_sources.most_common(10):
            percentage = (count / len(filtered_logs)) * 100
            print(f"{source:50} {count:5} ({percentage:.1f}%)")

        print(f"\n{'='*60}")
        print("错误时间线（按小时）:")
        print(f"{'='*60}")
        for hour, count in sorted(error_timeline.items())[-24:]:
            bar = '█' * min(count, 50)
            print(f"{hour} {bar} {count}")

        return {
            "total_errors": len(filtered_logs),
            "error_types": dict(error_types),
            "error_sources": dict(error_sources),
            "error_timeline": dict(error_timeline)
        }

    def analyze_performance(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """分析性能日志"""
        print(f"\n{'='*60}")
        print("性能分析报告")
        print(f"{'='*60}")

        # 加载访问日志
        access_logs = self.load_json_logs("access.json.log")

        if not access_logs:
            print("没有找到访问日志")
            return {}

        # 时间过滤
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
        filtered_logs = []

        for log in access_logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                if log_time >= cutoff_time:
                    filtered_logs.append(log)
            except (KeyError, ValueError):
                continue

        if not filtered_logs:
            print(f"最近 {time_range_hours} 小时内没有访问日志")
            return {}

        # 性能统计
        endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0,
            'min_duration': float('inf'),
            'max_duration': 0,
            'durations': []
        })

        status_codes = Counter()
        slow_requests = []

        for log in filtered_logs:
            # 提取HTTP信息
            if 'http' not in log:
                continue

            http = log['http']
            method = http.get('method', 'UNKNOWN')
            path = http.get('path', 'unknown')
            status_code = http.get('status_code', 0)
            duration_ms = http.get('duration_ms', 0)

            # 端点统计
            endpoint_key = f"{method} {path}"
            stats = endpoint_stats[endpoint_key]
            stats['count'] += 1
            stats['total_duration'] += duration_ms
            stats['min_duration'] = min(stats['min_duration'], duration_ms)
            stats['max_duration'] = max(stats['max_duration'], duration_ms)
            stats['durations'].append(duration_ms)

            # 状态码统计
            status_codes[status_code] += 1

            # 慢请求检测（超过1秒）
            if duration_ms > 1000:
                slow_requests.append({
                    'endpoint': endpoint_key,
                    'duration_ms': duration_ms,
                    'timestamp': log.get('timestamp', 'N/A'),
                    'request_id': log.get('request_id', 'N/A')
                })

        # 计算平均值和百分位数
        for endpoint, stats in endpoint_stats.items():
            if stats['count'] > 0:
                stats['avg_duration'] = stats['total_duration'] / stats['count']
                # 计算P95和P99
                durations = sorted(stats['durations'])
                p95_idx = int(len(durations) * 0.95)
                p99_idx = int(len(durations) * 0.99)
                stats['p95_duration'] = durations[p95_idx] if p95_idx < len(durations) else 0
                stats['p99_duration'] = durations[p99_idx] if p99_idx < len(durations) else 0

        # 输出统计结果
        print(f"\n总请求数: {len(filtered_logs)}")
        print(f"时间范围: 最近 {time_range_hours} 小时")

        print(f"\n{'='*60}")
        print("端点性能统计 Top 10（按平均响应时间）:")
        print(f"{'='*60}")
        print(f"{'端点':<40} {'请求数':>8} {'平均(ms)':>10} {'P95(ms)':>10} {'P99(ms)':>10} {'最大(ms)':>10}")
        print(f"{'-'*60}")

        sorted_endpoints = sorted(
            endpoint_stats.items(),
            key=lambda x: x[1]['avg_duration'],
            reverse=True
        )[:10]

        for endpoint, stats in sorted_endpoints:
            print(f"{endpoint:<40} {stats['count']:>8} {stats['avg_duration']:>10.2f} "
                  f"{stats['p95_duration']:>10.2f} {stats['p99_duration']:>10.2f} {stats['max_duration']:>10.2f}")

        print(f"\n{'='*60}")
        print("HTTP状态码分布:")
        print(f"{'='*60}")
        for status_code, count in sorted(status_codes.items()):
            percentage = (count / len(filtered_logs)) * 100
            print(f"{status_code:3} {count:6} ({percentage:.1f}%)")

        print(f"\n{'='*60}")
        print(f"慢请求 Top 10（超过1秒）:")
        print(f"{'='*60}")
        if slow_requests:
            sorted_slow = sorted(slow_requests, key=lambda x: x['duration_ms'], reverse=True)[:10]
            for req in sorted_slow:
                print(f"{req['endpoint']:<40} {req['duration_ms']:>8.2f}ms")
                print(f"  └─ 时间: {req['timestamp']}, Request ID: {req['request_id']}")
        else:
            print("没有慢请求")

        return {
            "total_requests": len(filtered_logs),
            "endpoint_stats": {k: {
                'count': v['count'],
                'avg_duration': v['avg_duration'],
                'p95_duration': v['p95_duration'],
                'p99_duration': v['p99_duration']
            } for k, v in endpoint_stats.items()},
            "status_codes": dict(status_codes),
            "slow_requests_count": len(slow_requests)
        }

    def detect_anomalies(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """检测异常"""
        print(f"\n{'='*60}")
        print("异常检测报告")
        print(f"{'='*60}")

        # 加载应用日志
        app_logs = self.load_json_logs("nautilus.json.log", max_lines=10000)

        if not app_logs:
            print("没有找到应用日志")
            return {}

        # 时间过滤
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
        filtered_logs = []

        for log in app_logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                if log_time >= cutoff_time:
                    filtered_logs.append(log)
            except (KeyError, ValueError):
                continue

        if not filtered_logs:
            print(f"最近 {time_range_hours} 小时内没有应用日志")
            return {}

        # 异常检测
        anomalies = {
            'high_error_rate': [],
            'repeated_errors': [],
            'unusual_patterns': []
        }

        # 1. 检测高错误率时段
        error_rate_by_hour = defaultdict(lambda: {'total': 0, 'errors': 0})

        for log in filtered_logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                hour_key = log_time.strftime('%Y-%m-%d %H:00')
                error_rate_by_hour[hour_key]['total'] += 1
                if log.get('level') in ['ERROR', 'CRITICAL']:
                    error_rate_by_hour[hour_key]['errors'] += 1
            except (KeyError, ValueError):
                continue

        for hour, stats in error_rate_by_hour.items():
            if stats['total'] > 10:  # 至少10个请求
                error_rate = (stats['errors'] / stats['total']) * 100
                if error_rate > 10:  # 错误率超过10%
                    anomalies['high_error_rate'].append({
                        'hour': hour,
                        'error_rate': error_rate,
                        'total': stats['total'],
                        'errors': stats['errors']
                    })

        # 2. 检测重复错误
        error_messages = Counter()
        for log in filtered_logs:
            if log.get('level') in ['ERROR', 'CRITICAL']:
                msg = log.get('message', '')[:100]  # 截取前100个字符
                error_messages[msg] += 1

        for msg, count in error_messages.items():
            if count > 10:  # 重复超过10次
                anomalies['repeated_errors'].append({
                    'message': msg,
                    'count': count
                })

        # 3. 检测异常模式（例如：突然的日志量激增）
        log_volume_by_hour = Counter()
        for log in filtered_logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                hour_key = log_time.strftime('%Y-%m-%d %H:00')
                log_volume_by_hour[hour_key] += 1
            except (KeyError, ValueError):
                continue

        if log_volume_by_hour:
            volumes = list(log_volume_by_hour.values())
            avg_volume = sum(volumes) / len(volumes)
            for hour, volume in log_volume_by_hour.items():
                if volume > avg_volume * 3:  # 超过平均值3倍
                    anomalies['unusual_patterns'].append({
                        'hour': hour,
                        'volume': volume,
                        'avg_volume': avg_volume,
                        'ratio': volume / avg_volume
                    })

        # 输出结果
        print(f"\n总日志数: {len(filtered_logs)}")
        print(f"时间范围: 最近 {time_range_hours} 小时")

        print(f"\n{'='*60}")
        print("高错误率时段:")
        print(f"{'='*60}")
        if anomalies['high_error_rate']:
            for item in sorted(anomalies['high_error_rate'], key=lambda x: x['error_rate'], reverse=True):
                print(f"{item['hour']} - 错误率: {item['error_rate']:.1f}% "
                      f"({item['errors']}/{item['total']})")
        else:
            print("未检测到高错误率时段")

        print(f"\n{'='*60}")
        print("重复错误 Top 10:")
        print(f"{'='*60}")
        if anomalies['repeated_errors']:
            sorted_errors = sorted(anomalies['repeated_errors'], key=lambda x: x['count'], reverse=True)[:10]
            for item in sorted_errors:
                print(f"[{item['count']}次] {item['message']}")
        else:
            print("未检测到重复错误")

        print(f"\n{'='*60}")
        print("异常日志量时段:")
        print(f"{'='*60}")
        if anomalies['unusual_patterns']:
            for item in sorted(anomalies['unusual_patterns'], key=lambda x: x['ratio'], reverse=True):
                print(f"{item['hour']} - 日志量: {item['volume']} "
                      f"(平均: {item['avg_volume']:.0f}, 比率: {item['ratio']:.1f}x)")
        else:
            print("未检测到异常日志量")

        return anomalies


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='日志分析工具')
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='日志目录路径（默认: logs）'
    )
    parser.add_argument(
        '--time-range',
        type=int,
        default=24,
        help='分析时间范围（小时，默认: 24）'
    )
    parser.add_argument(
        '--analysis-type',
        choices=['errors', 'performance', 'anomalies', 'all'],
        default='all',
        help='分析类型（默认: all）'
    )
    parser.add_argument(
        '--output',
        help='输出JSON报告到文件'
    )

    args = parser.parse_args()

    analyzer = LogAnalyzer(args.log_dir)

    results = {}

    if args.analysis_type in ['errors', 'all']:
        results['errors'] = analyzer.analyze_errors(args.time_range)

    if args.analysis_type in ['performance', 'all']:
        results['performance'] = analyzer.analyze_performance(args.time_range)

    if args.analysis_type in ['anomalies', 'all']:
        results['anomalies'] = analyzer.detect_anomalies(args.time_range)

    # 输出JSON报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n报告已保存到: {args.output}")

    print(f"\n{'='*60}")
    print("分析完成")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

"""
系统资源监控脚本

在压力测试期间监控系统资源使用情况。

功能:
- CPU使用率监控
- 内存使用监控
- 数据库连接池监控
- 网络IO监控
- 实时性能指标收集

使用方式:
    python monitor_resources.py --duration 600 --interval 5

版本: 1.0.0
创建时间: 2026-02-27
"""

import psutil
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import requests
import sys


class ResourceMonitor:
    """系统资源监控器"""

    def __init__(self, interval: int = 5, api_url: str = "http://localhost:8000"):
        self.interval = interval
        self.api_url = api_url
        self.metrics: List[Dict[str, Any]] = []
        self.start_time = None
        self.process = psutil.Process()

    def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()

        return {
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': time.time() - self.start_time if self.start_time else 0,
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
                'per_cpu': psutil.cpu_percent(percpu=True)
            },
            'memory': {
                'total_mb': memory.total / 1024 / 1024,
                'available_mb': memory.available / 1024 / 1024,
                'used_mb': memory.used / 1024 / 1024,
                'percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / 1024 / 1024 / 1024,
                'used_gb': disk.used / 1024 / 1024 / 1024,
                'free_gb': disk.free / 1024 / 1024 / 1024,
                'percent': disk.percent
            },
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        }

    def collect_process_metrics(self) -> Dict[str, Any]:
        """收集进程指标"""
        try:
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            num_threads = self.process.num_threads()
            connections = len(self.process.connections())

            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_info.rss / 1024 / 1024,
                'threads': num_threads,
                'connections': connections
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}

    def collect_api_metrics(self) -> Dict[str, Any]:
        """收集API性能指标"""
        try:
            # 性能统计
            response = requests.get(f"{self.api_url}/performance/stats", timeout=5)
            performance_stats = response.json() if response.status_code == 200 else {}

            # 缓存统计
            response = requests.get(f"{self.api_url}/cache/stats", timeout=5)
            cache_stats = response.json() if response.status_code == 200 else {}

            # 数据库连接池
            response = requests.get(f"{self.api_url}/database/pool", timeout=5)
            pool_stats = response.json() if response.status_code == 200 else {}

            return {
                'performance': performance_stats,
                'cache': cache_stats,
                'database_pool': pool_stats
            }
        except Exception as e:
            return {'error': str(e)}

    def collect_metrics(self) -> Dict[str, Any]:
        """收集所有指标"""
        metrics = {
            'system': self.collect_system_metrics(),
            'process': self.collect_process_metrics(),
            'api': self.collect_api_metrics()
        }
        return metrics

    def monitor(self, duration: int):
        """开始监控"""
        print("=" * 70)
        print("系统资源监控")
        print("=" * 70)
        print(f"监控间隔: {self.interval}秒")
        print(f"监控时长: {duration}秒")
        print(f"API地址: {self.api_url}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        self.start_time = time.time()
        end_time = self.start_time + duration
        iteration = 0

        try:
            while time.time() < end_time:
                iteration += 1
                elapsed = time.time() - self.start_time

                # 收集指标
                metrics = self.collect_metrics()
                self.metrics.append(metrics)

                # 输出当前状态
                system = metrics['system']
                process = metrics['process']
                api = metrics['api']

                print(f"[{elapsed:.0f}s] 迭代 {iteration}")
                print(f"  系统 - CPU: {system['cpu']['percent']:.1f}%, "
                      f"内存: {system['memory']['percent']:.1f}% "
                      f"({system['memory']['used_mb']:.0f}MB)")

                if process:
                    print(f"  进程 - CPU: {process.get('cpu_percent', 0):.1f}%, "
                          f"内存: {process.get('memory_mb', 0):.0f}MB, "
                          f"线程: {process.get('threads', 0)}, "
                          f"连接: {process.get('connections', 0)}")

                if 'performance' in api and api['performance']:
                    perf = api['performance']
                    print(f"  API - 请求: {perf.get('total_requests', 0)}, "
                          f"平均响应: {perf.get('avg_response_time', 0):.2f}ms, "
                          f"RPS: {perf.get('requests_per_second', 0):.2f}")

                if 'cache' in api and api['cache']:
                    cache = api['cache']
                    print(f"  缓存 - 命中率: {cache.get('hit_rate', 0):.1f}%, "
                          f"条目: {cache.get('size', 0)}")

                if 'database_pool' in api and api['database_pool']:
                    pool = api['database_pool']
                    print(f"  数据库 - 连接池: {pool.get('connections_in_use', 0)}/{pool.get('pool_size', 0)}, "
                          f"利用率: {pool.get('utilization', 0):.1f}%")

                print()

                # 等待下一个间隔
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n监控被用户中断")

        # 保存结果
        self.save_results()

    def save_results(self):
        """保存监控结果"""
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"resource_monitor_{timestamp}.json"

        # 计算统计信息
        summary = self.calculate_summary()

        data = {
            'metadata': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': time.time() - self.start_time,
                'interval_seconds': self.interval,
                'sample_count': len(self.metrics)
            },
            'summary': summary,
            'metrics': self.metrics
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print("=" * 70)
        print("监控完成")
        print("=" * 70)
        print(f"结果已保存到: {output_file}")
        print()

        # 输出摘要
        self.print_summary(summary)

    def calculate_summary(self) -> Dict[str, Any]:
        """计算统计摘要"""
        if not self.metrics:
            return {}

        cpu_values = [m['system']['cpu']['percent'] for m in self.metrics]
        memory_values = [m['system']['memory']['percent'] for m in self.metrics]
        memory_mb_values = [m['system']['memory']['used_mb'] for m in self.metrics]

        process_cpu_values = [m['process'].get('cpu_percent', 0) for m in self.metrics if m['process']]
        process_memory_values = [m['process'].get('memory_mb', 0) for m in self.metrics if m['process']]

        return {
            'system': {
                'cpu': {
                    'min': min(cpu_values),
                    'max': max(cpu_values),
                    'avg': sum(cpu_values) / len(cpu_values)
                },
                'memory': {
                    'min_percent': min(memory_values),
                    'max_percent': max(memory_values),
                    'avg_percent': sum(memory_values) / len(memory_values),
                    'min_mb': min(memory_mb_values),
                    'max_mb': max(memory_mb_values),
                    'avg_mb': sum(memory_mb_values) / len(memory_mb_values)
                }
            },
            'process': {
                'cpu': {
                    'min': min(process_cpu_values) if process_cpu_values else 0,
                    'max': max(process_cpu_values) if process_cpu_values else 0,
                    'avg': sum(process_cpu_values) / len(process_cpu_values) if process_cpu_values else 0
                },
                'memory': {
                    'min_mb': min(process_memory_values) if process_memory_values else 0,
                    'max_mb': max(process_memory_values) if process_memory_values else 0,
                    'avg_mb': sum(process_memory_values) / len(process_memory_values) if process_memory_values else 0
                }
            }
        }

    def print_summary(self, summary: Dict[str, Any]):
        """打印摘要信息"""
        print("资源使用摘要:")
        print()

        if 'system' in summary:
            sys_cpu = summary['system']['cpu']
            sys_mem = summary['system']['memory']

            print("系统资源:")
            print(f"  CPU使用率:")
            print(f"    最小: {sys_cpu['min']:.1f}%")
            print(f"    最大: {sys_cpu['max']:.1f}%")
            print(f"    平均: {sys_cpu['avg']:.1f}%")
            print(f"  内存使用:")
            print(f"    最小: {sys_mem['min_percent']:.1f}% ({sys_mem['min_mb']:.0f}MB)")
            print(f"    最大: {sys_mem['max_percent']:.1f}% ({sys_mem['max_mb']:.0f}MB)")
            print(f"    平均: {sys_mem['avg_percent']:.1f}% ({sys_mem['avg_mb']:.0f}MB)")
            print()

        if 'process' in summary:
            proc_cpu = summary['process']['cpu']
            proc_mem = summary['process']['memory']

            print("进程资源:")
            print(f"  CPU使用率:")
            print(f"    最小: {proc_cpu['min']:.1f}%")
            print(f"    最大: {proc_cpu['max']:.1f}%")
            print(f"    平均: {proc_cpu['avg']:.1f}%")
            print(f"  内存使用:")
            print(f"    最小: {proc_mem['min_mb']:.0f}MB")
            print(f"    最大: {proc_mem['max_mb']:.0f}MB")
            print(f"    平均: {proc_mem['avg_mb']:.0f}MB")
            print()

        # 性能评估
        print("性能评估:")
        if 'system' in summary:
            cpu_avg = summary['system']['cpu']['avg']
            mem_avg = summary['system']['memory']['avg_percent']

            cpu_status = "正常" if cpu_avg < 70 else "偏高" if cpu_avg < 90 else "过高"
            mem_status = "正常" if mem_avg < 70 else "偏高" if mem_avg < 90 else "过高"

            print(f"  CPU使用: {cpu_status} (平均 {cpu_avg:.1f}%)")
            print(f"  内存使用: {mem_status} (平均 {mem_avg:.1f}%)")

            if cpu_avg > 90:
                print("  ⚠ 警告: CPU使用率过高，可能影响性能")
            if mem_avg > 90:
                print("  ⚠ 警告: 内存使用率过高，可能导致系统不稳定")

        print("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="系统资源监控工具")
    parser.add_argument(
        '--duration',
        type=int,
        default=600,
        help='监控时长（秒），默认600秒（10分钟）'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='采样间隔（秒），默认5秒'
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000',
        help='API地址，默认 http://localhost:8000'
    )

    args = parser.parse_args()

    # 检查psutil是否可用
    try:
        import psutil
    except ImportError:
        print("错误: 需要安装 psutil 库")
        print("安装命令: pip install psutil")
        return 1

    # 创建监控器并开始监控
    monitor = ResourceMonitor(interval=args.interval, api_url=args.api_url)
    monitor.monitor(duration=args.duration)

    return 0


if __name__ == "__main__":
    sys.exit(main())

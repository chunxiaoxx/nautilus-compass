#!/usr/bin/env python3
"""
安全事件日志分析脚本
分析日志文件中的安全事件，生成报告
"""
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Any
import argparse


class SecurityLogAnalyzer:
    """安全日志分析器"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.events = []
        self.stats = defaultdict(int)

    def parse_log_file(self, log_file: Path) -> None:
        """解析日志文件"""
        print(f"解析日志文件: {log_file}")

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # 尝试解析 JSON 格式日志
                    try:
                        log_entry = json.loads(line.strip())
                        self._process_json_log(log_entry)
                    except json.JSONDecodeError:
                        # 尝试解析文本格式日志
                        self._process_text_log(line)
        except Exception as e:
            print(f"解析日志文件失败: {e}")

    def _process_json_log(self, log_entry: Dict[str, Any]) -> None:
        """处理 JSON 格式日志"""
        # 检查是否为安全事件
        if 'security_event' in log_entry or 'event_type' in log_entry:
            event = {
                'timestamp': log_entry.get('timestamp', ''),
                'event_type': log_entry.get('event_type', 'unknown'),
                'severity': log_entry.get('severity', 'info'),
                'message': log_entry.get('message', ''),
                'details': log_entry.get('details', {})
            }
            self.events.append(event)
            self.stats[event['event_type']] += 1

    def _process_text_log(self, line: str) -> None:
        """处理文本格式日志"""
        # 登录失败
        if 'login failed' in line.lower() or 'authentication failed' in line.lower():
            self.events.append({
                'timestamp': self._extract_timestamp(line),
                'event_type': 'login_failed',
                'severity': 'warning',
                'message': line.strip(),
                'details': {}
            })
            self.stats['login_failed'] += 1

        # 权限拒绝
        elif 'permission denied' in line.lower() or 'access denied' in line.lower():
            self.events.append({
                'timestamp': self._extract_timestamp(line),
                'event_type': 'permission_denied',
                'severity': 'warning',
                'message': line.strip(),
                'details': {}
            })
            self.stats['permission_denied'] += 1

        # 异常 API 调用
        elif 'abnormal' in line.lower() or 'suspicious' in line.lower():
            self.events.append({
                'timestamp': self._extract_timestamp(line),
                'event_type': 'abnormal_api_call',
                'severity': 'critical',
                'message': line.strip(),
                'details': {}
            })
            self.stats['abnormal_api_call'] += 1

    def _extract_timestamp(self, line: str) -> str:
        """从日志行中提取时间戳"""
        # 尝试匹配常见的时间戳格式
        patterns = [
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',
            r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}',
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)

        return datetime.now().isoformat()

    def analyze_logs(self, hours: int = 24) -> None:
        """分析指定时间范围内的日志"""
        print(f"\n分析最近 {hours} 小时的日志...")

        # 查找所有日志文件
        log_files = list(self.log_dir.glob("*.log"))
        if not log_files:
            print(f"未找到日志文件在目录: {self.log_dir}")
            return

        # 解析所有日志文件
        for log_file in log_files:
            self.parse_log_file(log_file)

        print(f"共解析 {len(self.events)} 个安全事件")

    def generate_report(self) -> str:
        """生成安全事件报告"""
        report = []
        report.append("=" * 80)
        report.append("Nautilus 安全事件分析报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"事件总数: {len(self.events)}")
        report.append("")

        # 事件类型统计
        report.append("事件类型统计:")
        report.append("-" * 80)
        for event_type, count in sorted(self.stats.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {event_type:30s}: {count:5d}")
        report.append("")

        # 严重程度统计
        severity_stats = Counter(event['severity'] for event in self.events)
        report.append("严重程度统计:")
        report.append("-" * 80)
        for severity in ['critical', 'warning', 'info']:
            count = severity_stats.get(severity, 0)
            report.append(f"  {severity:30s}: {count:5d}")
        report.append("")

        # 最近的关键事件
        critical_events = [e for e in self.events if e['severity'] == 'critical']
        if critical_events:
            report.append("最近的关键安全事件 (最多显示 10 条):")
            report.append("-" * 80)
            for event in critical_events[-10:]:
                report.append(f"  时间: {event['timestamp']}")
                report.append(f"  类型: {event['event_type']}")
                report.append(f"  消息: {event['message'][:100]}")
                report.append("")

        # 建议
        report.append("安全建议:")
        report.append("-" * 80)
        if self.stats.get('login_failed', 0) > 10:
            report.append("  ⚠️  检测到大量登录失败，建议检查是否存在暴力破解攻击")
        if self.stats.get('permission_denied', 0) > 20:
            report.append("  ⚠️  检测到大量权限拒绝事件，建议检查权限配置")
        if self.stats.get('abnormal_api_call', 0) > 0:
            report.append("  🚨 检测到异常 API 调用，建议立即调查")
        if not any([self.stats.get('login_failed', 0) > 10,
                    self.stats.get('permission_denied', 0) > 20,
                    self.stats.get('abnormal_api_call', 0) > 0]):
            report.append("  ✅ 未发现明显的安全威胁")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, output_file: str = "security_report.txt") -> None:
        """保存报告到文件"""
        report = self.generate_report()
        output_path = Path(output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n报告已保存到: {output_path.absolute()}")

    def export_json(self, output_file: str = "security_events.json") -> None:
        """导出事件为 JSON 格式"""
        output_path = Path(output_file)

        data = {
            'generated_at': datetime.now().isoformat(),
            'total_events': len(self.events),
            'statistics': dict(self.stats),
            'events': self.events
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"事件数据已导出到: {output_path.absolute()}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Nautilus 安全事件日志分析工具')
    parser.add_argument('--log-dir', default='logs', help='日志目录路径')
    parser.add_argument('--hours', type=int, default=24, help='分析最近N小时的日志')
    parser.add_argument('--output', default='security_report.txt', help='报告输出文件')
    parser.add_argument('--json', help='导出 JSON 格式的事件数据')
    parser.add_argument('--print', action='store_true', help='打印报告到控制台')

    args = parser.parse_args()

    # 创建分析器
    analyzer = SecurityLogAnalyzer(log_dir=args.log_dir)

    # 分析日志
    analyzer.analyze_logs(hours=args.hours)

    # 生成并保存报告
    analyzer.save_report(output_file=args.output)

    # 打印报告
    if args.print:
        print("\n" + analyzer.generate_report())

    # 导出 JSON
    if args.json:
        analyzer.export_json(output_file=args.json)


if __name__ == "__main__":
    main()

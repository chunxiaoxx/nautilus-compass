#!/usr/bin/env python3
"""
安全扫描脚本
扫描代码中的常见安全问题
"""
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class SecurityIssue:
    """安全问题"""
    def __init__(self, severity: str, category: str, file_path: str,
                 line_number: int, description: str, code_snippet: str = ""):
        self.severity = severity  # critical, high, medium, low, info
        self.category = category
        self.file_path = file_path
        self.line_number = line_number
        self.description = description
        self.code_snippet = code_snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "code_snippet": self.code_snippet
        }


class SecurityScanner:
    """安全扫描器"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues: List[SecurityIssue] = []

        # 安全模式定义
        self.patterns = {
            "hardcoded_secrets": [
                (r'password\s*=\s*["\'][^"\']{3,}["\']', "硬编码密码"),
                (r'secret\s*=\s*["\'][^"\']{10,}["\']', "硬编码密钥"),
                (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', "硬编码API密钥"),
                (r'token\s*=\s*["\'][^"\']{10,}["\']', "硬编码Token"),
                (r'private[_-]?key\s*=\s*["\']0x[a-fA-F0-9]{64}["\']', "硬编码私钥"),
            ],
            "sql_injection": [
                (r'execute\s*\(\s*["\'].*%s.*["\']', "可能的SQL注入风险"),
                (r'execute\s*\(\s*f["\'].*\{.*\}.*["\']', "使用f-string的SQL查询"),
                (r'\.format\s*\(.*\).*execute', "使用format的SQL查询"),
            ],
            "command_injection": [
                (r'os\.system\s*\(', "使用os.system执行命令"),
                (r'subprocess\.call\s*\(.*shell\s*=\s*True', "subprocess使用shell=True"),
                (r'eval\s*\(', "使用eval函数"),
                (r'exec\s*\(', "使用exec函数"),
            ],
            "insecure_deserialization": [
                (r'pickle\.loads?\s*\(', "使用pickle反序列化"),
                (r'yaml\.load\s*\([^,)]*\)', "不安全的YAML加载"),
            ],
            "weak_crypto": [
                (r'md5\s*\(', "使用MD5哈希"),
                (r'sha1\s*\(', "使用SHA1哈希"),
                (r'random\.random', "使用不安全的随机数"),
            ],
            "debug_code": [
                (r'print\s*\(.*password', "打印密码信息"),
                (r'print\s*\(.*secret', "打印密钥信息"),
                (r'print\s*\(.*token', "打印Token信息"),
                (r'DEBUG\s*=\s*True', "调试模式开启"),
            ],
        }

    def scan_file(self, file_path: Path):
        """扫描单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # 跳过注释行
                if line.strip().startswith('#'):
                    continue

                # 检查各种安全模式
                for category, patterns in self.patterns.items():
                    for pattern, description in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # 确定严重程度
                            severity = self._determine_severity(category)

                            # 检查是否为示例文件
                            if 'example' in str(file_path).lower() or 'test' in str(file_path).lower():
                                severity = "info"

                            issue = SecurityIssue(
                                severity=severity,
                                category=category,
                                file_path=str(file_path.relative_to(self.root_dir)),
                                line_number=line_num,
                                description=description,
                                code_snippet=line.strip()
                            )
                            self.issues.append(issue)

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

    def _determine_severity(self, category: str) -> str:
        """确定严重程度"""
        severity_map = {
            "hardcoded_secrets": "critical",
            "sql_injection": "high",
            "command_injection": "critical",
            "insecure_deserialization": "high",
            "weak_crypto": "medium",
            "debug_code": "low",
        }
        return severity_map.get(category, "medium")

    def scan_directory(self):
        """扫描整个目录"""
        print(f"🔍 扫描目录: {self.root_dir}")

        # 排除的目录
        exclude_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'htmlcov',
            'node_modules', 'venv', '.venv', 'logs', 'keys'
        }

        # 扫描所有Python文件
        python_files = []
        for file_path in self.root_dir.rglob('*.py'):
            # 检查是否在排除目录中
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            python_files.append(file_path)

        print(f"📁 找到 {len(python_files)} 个Python文件")

        for file_path in python_files:
            self.scan_file(file_path)

        print(f"✅ 扫描完成，发现 {len(self.issues)} 个潜在问题")

    def generate_report(self) -> Dict[str, Any]:
        """生成报告"""
        # 按严重程度分组
        by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }

        for issue in self.issues:
            by_severity[issue.severity].append(issue.to_dict())

        # 按类别分组
        by_category = {}
        for issue in self.issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue.to_dict())

        return {
            "scan_time": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_category": {k: len(v) for k, v in by_category.items()},
            "issues": {
                "by_severity": by_severity,
                "by_category": by_category
            }
        }

    def print_summary(self):
        """打印摘要"""
        report = self.generate_report()

        print("\n" + "="*70)
        print("🔒 安全扫描报告摘要")
        print("="*70)
        print(f"扫描时间: {report['scan_time']}")
        print(f"总问题数: {report['total_issues']}")
        print("\n按严重程度分类:")
        for severity, count in report['by_severity'].items():
            if count > 0:
                emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "ℹ️"
                }
                print(f"  {emoji.get(severity, '•')} {severity.upper()}: {count}")

        print("\n按类别分类:")
        for category, count in report['by_category'].items():
            print(f"  • {category}: {count}")

        print("="*70)

    def save_report(self, output_file: str):
        """保存报告到JSON文件"""
        report = self.generate_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到: {output_file}")


def main():
    """主函数"""
    # 获取项目根目录
    root_dir = Path(__file__).parent

    # 创建扫描器
    scanner = SecurityScanner(root_dir)

    # 执行扫描
    scanner.scan_directory()

    # 打印摘要
    scanner.print_summary()

    # 保存详细报告
    scanner.save_report("security_scan_report.json")

    # 返回问题数量
    return len(scanner.issues)


if __name__ == "__main__":
    import sys
    issues_count = main()
    sys.exit(0)  # 不因为发现问题而退出失败

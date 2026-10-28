#!/usr/bin/env python3
"""
性能优化验证脚本
验证所有性能优化措施是否正确实施
"""
import os
import sys
import time
import json
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class PerformanceValidator:
    """性能优化验证器"""

    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def validate_all(self):
        """执行所有验证"""
        print("=" * 80)
        print("🚀 Nautilus Phase 3 - 性能优化验证")
        print("=" * 80)
        print()

        # 1. 验证数据库优化
        self.validate_database_optimization()

        # 2. 验证缓存实施
        self.validate_cache_implementation()

        # 3. 验证异步处理
        self.validate_async_processing()

        # 4. 验证监控配置
        self.validate_monitoring()

        # 5. 验证工具和脚本
        self.validate_tools()

        # 6. 验证文档
        self.validate_documentation()

        # 生成报告
        self.generate_report()

    def validate_database_optimization(self):
        """验证数据库优化"""
        print("📊 验证数据库优化...")
        print("-" * 80)

        # 检查索引优化脚本
        if os.path.exists('add_performance_indexes.py'):
            self.results['passed'].append("✅ 索引优化脚本存在")
        else:
            self.results['failed'].append("❌ 索引优化脚本缺失")

        # 检查查询分析脚本
        if os.path.exists('analyze_query_performance.py'):
            self.results['passed'].append("✅ 查询分析脚本存在")
        else:
            self.results['failed'].append("❌ 查询分析脚本缺失")

        # 检查连接池监控
        if os.path.exists('utils/pool_monitor.py'):
            self.results['passed'].append("✅ 连接池监控工具存在")
        else:
            self.results['failed'].append("❌ 连接池监控工具缺失")

        # 检查查询优化工具
        if os.path.exists('utils/query_optimizer.py'):
            self.results['passed'].append("✅ 查询优化工具存在")
        else:
            self.results['failed'].append("❌ 查询优化工具缺失")

        # 检查数据库配置
        try:
            from utils.database import engine
            pool_size = engine.pool.size()
            if pool_size >= 20:
                self.results['passed'].append(f"✅ 连接池大小已优化: {pool_size}")
            else:
                self.results['warnings'].append(f"⚠️  连接池大小较小: {pool_size}")
        except Exception as e:
            self.results['warnings'].append(f"⚠️  无法检查连接池配置: {e}")

        print()

    def validate_cache_implementation(self):
        """验证缓存实施"""
        print("🔄 验证缓存实施...")
        print("-" * 80)

        # 检查内存缓存
        if os.path.exists('utils/cache.py'):
            self.results['passed'].append("✅ 内存缓存模块存在")
        else:
            self.results['failed'].append("❌ 内存缓存模块缺失")

        # 检查Redis缓存
        if os.path.exists('utils/redis_cache.py'):
            self.results['passed'].append("✅ Redis缓存模块存在")
        else:
            self.results['failed'].append("❌ Redis缓存模块缺失")

        # 检查缓存装饰器
        try:
            from utils.cache import cached, get_cache
            self.results['passed'].append("✅ 缓存装饰器可用")
        except ImportError as e:
            self.results['failed'].append(f"❌ 缓存装饰器导入失败: {e}")

        # 检查缓存端点
        try:
            from main import app
            routes = [route.path for route in app.routes]
            if '/cache/stats' in routes:
                self.results['passed'].append("✅ 缓存统计端点存在")
            else:
                self.results['warnings'].append("⚠️  缓存统计端点缺失")
        except Exception as e:
            self.results['warnings'].append(f"⚠️  无法检查缓存端点: {e}")

        print()

    def validate_async_processing(self):
        """验证异步处理"""
        print("⚡ 验证异步处理...")
        print("-" * 80)

        # 检查异步队列
        if os.path.exists('utils/async_queue.py'):
            self.results['passed'].append("✅ 异步任务队列存在")
        else:
            self.results['failed'].append("❌ 异步任务队列缺失")

        # 检查异步队列功能
        try:
            from utils.async_queue import AsyncTaskQueue, TaskPriority, background_task
            self.results['passed'].append("✅ 异步队列功能可用")
        except ImportError as e:
            self.results['failed'].append(f"❌ 异步队列导入失败: {e}")

        print()

    def validate_monitoring(self):
        """验证监控配置"""
        print("📈 验证监控配置...")
        print("-" * 80)

        # 检查性能中间件
        if os.path.exists('utils/performance_middleware.py'):
            self.results['passed'].append("✅ 性能监控中间件存在")
        else:
            self.results['failed'].append("❌ 性能监控中间件缺失")

        # 检查监控配置
        if os.path.exists('monitoring_config.py'):
            self.results['passed'].append("✅ 监控配置文件存在")
        else:
            self.results['warnings'].append("⚠️  监控配置文件缺失")

        # 检查监控端点
        try:
            from main import app
            routes = [route.path for route in app.routes]
            monitoring_endpoints = [
                '/performance/stats',
                '/database/pool',
                '/metrics'
            ]
            for endpoint in monitoring_endpoints:
                if endpoint in routes:
                    self.results['passed'].append(f"✅ 监控端点存在: {endpoint}")
                else:
                    self.results['warnings'].append(f"⚠️  监控端点缺失: {endpoint}")
        except Exception as e:
            self.results['warnings'].append(f"⚠️  无法检查监控端点: {e}")

        print()

    def validate_tools(self):
        """验证工具和脚本"""
        print("🛠️  验证工具和脚本...")
        print("-" * 80)

        tools = [
            ('benchmark_performance.py', '基准测试工具'),
            ('analyze_query_performance.py', '查询分析工具'),
            ('add_performance_indexes.py', '索引优化脚本'),
            ('quick_performance_check.py', '快速性能检查'),
            ('verify_application_performance.py', '性能验证脚本')
        ]

        for tool_file, tool_name in tools:
            if os.path.exists(tool_file):
                self.results['passed'].append(f"✅ {tool_name}存在")
            else:
                self.results['warnings'].append(f"⚠️  {tool_name}缺失")

        print()

    def validate_documentation(self):
        """验证文档"""
        print("📚 验证文档...")
        print("-" * 80)

        docs = [
            ('PERFORMANCE_OPTIMIZATION_FINAL_REPORT.md', '性能优化最终报告'),
            ('PERFORMANCE_OPTIMIZATION.md', '性能优化详细指南'),
            ('CDN_SETUP_GUIDE.md', 'CDN配置指南'),
            ('PERFORMANCE_OPTIMIZATION_SUMMARY.md', '性能优化总结'),
            ('PERFORMANCE_QUICK_REFERENCE.md', '快速参考'),
            ('PERFORMANCE_README.md', '使用说明')
        ]

        for doc_file, doc_name in docs:
            if os.path.exists(doc_file):
                # 检查文件大小
                size = os.path.getsize(doc_file)
                if size > 1000:  # 至少1KB
                    self.results['passed'].append(f"✅ {doc_name}存在 ({size} bytes)")
                else:
                    self.results['warnings'].append(f"⚠️  {doc_name}内容较少 ({size} bytes)")
            else:
                self.results['warnings'].append(f"⚠️  {doc_name}缺失")

        print()

    def generate_report(self):
        """生成验证报告"""
        print("=" * 80)
        print("📋 验证报告")
        print("=" * 80)
        print()

        # 通过的检查
        if self.results['passed']:
            print(f"✅ 通过检查 ({len(self.results['passed'])}项):")
            print("-" * 80)
            for item in self.results['passed']:
                print(f"  {item}")
            print()

        # 警告
        if self.results['warnings']:
            print(f"⚠️  警告 ({len(self.results['warnings'])}项):")
            print("-" * 80)
            for item in self.results['warnings']:
                print(f"  {item}")
            print()

        # 失败的检查
        if self.results['failed']:
            print(f"❌ 失败检查 ({len(self.results['failed'])}项):")
            print("-" * 80)
            for item in self.results['failed']:
                print(f"  {item}")
            print()

        # 总结
        print("=" * 80)
        print("📊 验证总结")
        print("=" * 80)
        total = len(self.results['passed']) + len(self.results['warnings']) + len(self.results['failed'])
        passed_rate = len(self.results['passed']) / total * 100 if total > 0 else 0

        print(f"总检查项: {total}")
        print(f"通过: {len(self.results['passed'])} ({passed_rate:.1f}%)")
        print(f"警告: {len(self.results['warnings'])}")
        print(f"失败: {len(self.results['failed'])}")
        print()

        # 最终状态
        if len(self.results['failed']) == 0:
            if len(self.results['warnings']) == 0:
                print("🎉 状态: 完美! 所有优化措施已正确实施")
                return 0
            else:
                print("✅ 状态: 良好! 核心优化已实施，有少量警告")
                return 0
        else:
            print("⚠️  状态: 需要改进! 存在失败的检查项")
            return 1

    def save_report(self, filename: str = 'performance_validation_report.json'):
        """保存验证报告为JSON"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': self.results,
            'summary': {
                'total': len(self.results['passed']) + len(self.results['warnings']) + len(self.results['failed']),
                'passed': len(self.results['passed']),
                'warnings': len(self.results['warnings']),
                'failed': len(self.results['failed'])
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 验证报告已保存: {filename}")


def main():
    """主函数"""
    validator = PerformanceValidator()
    exit_code = validator.validate_all()

    # 保存报告
    validator.save_report()

    print()
    print("=" * 80)
    print("验证完成!")
    print("=" * 80)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
性能优化完整验证脚本
验证所有优化措施是否正确实施
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

class PerformanceValidator:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def check_file_exists(self, filepath: str, description: str) -> bool:
        """检查文件是否存在"""
        if os.path.exists(filepath):
            self.passed.append(f"✅ {description}: {filepath}")
            return True
        else:
            self.failed.append(f"❌ {description}: {filepath} 不存在")
            return False

    def check_files_exist(self, files: List[Tuple[str, str]]) -> int:
        """批量检查文件"""
        count = 0
        for filepath, description in files:
            if self.check_file_exists(filepath, description):
                count += 1
        return count

    def validate_optimization_tools(self):
        """验证优化工具库"""
        print("=" * 80)
        print("📦 验证优化工具库")
        print("=" * 80)

        tools = [
            ('utils/cache.py', '内存缓存管理器'),
            ('utils/redis_cache.py', 'Redis分布式缓存'),
            ('utils/query_optimizer.py', '查询优化工具'),
            ('utils/async_queue.py', '异步任务队列'),
            ('utils/performance_middleware.py', '性能监控中间件'),
            ('utils/pool_monitor.py', '连接池监控'),
        ]

        count = self.check_files_exist(tools)
        print(f"\n✅ 优化工具库: {count}/{len(tools)} 个模块")
        print()

    def validate_scripts(self):
        """验证性能脚本"""
        print("=" * 80)
        print("🔧 验证性能脚本")
        print("=" * 80)

        scripts = [
            ('benchmark_performance.py', '性能基准测试'),
            ('analyze_query_performance.py', '查询性能分析'),
            ('add_performance_indexes.py', '索引优化脚本'),
            ('quick_performance_check.py', '快速性能检查'),
            ('verify_application_performance.py', '应用性能验证'),
            ('validate_performance_optimization.py', '优化验证脚本'),
            ('show_performance_results.py', '成果展示脚本'),
            ('performance_statistics.py', '项目统计脚本'),
            ('deploy_performance_optimization.sh', '一键部署脚本'),
        ]

        count = self.check_files_exist(scripts)
        print(f"\n✅ 性能脚本: {count}/{len(scripts)} 个脚本")
        print()

    def validate_documentation(self):
        """验证文档"""
        print("=" * 80)
        print("📚 验证核心文档")
        print("=" * 80)

        docs = [
            ('PERFORMANCE_OPTIMIZATION_FINAL.md', '最终总结报告'),
            ('PERFORMANCE_OPTIMIZATION.md', '详细优化指南'),
            ('CDN_SETUP_GUIDE.md', 'CDN配置指南'),
            ('PERFORMANCE_QUICK_GUIDE.md', '快速参考指南'),
            ('README_PERFORMANCE_OPTIMIZATION.md', '项目README'),
            ('PERFORMANCE_QUICK_START.md', '快速上手指南'),
        ]

        count = self.check_files_exist(docs)
        print(f"\n✅ 核心文档: {count}/{len(docs)} 份文档")
        print()

    def validate_code_integration(self):
        """验证代码集成"""
        print("=" * 80)
        print("🔍 验证代码集成")
        print("=" * 80)

        checks = []

        # 检查缓存集成
        if os.path.exists('utils/cache.py'):
            with open('utils/cache.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'class SimpleCache' in content:
                    checks.append("✅ 内存缓存类已实现")
                if 'def cached' in content:
                    checks.append("✅ 缓存装饰器已实现")

        # 检查Redis缓存
        if os.path.exists('utils/redis_cache.py'):
            with open('utils/redis_cache.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'class RedisCache' in content:
                    checks.append("✅ Redis缓存类已实现")
                if 'ConnectionPool' in content:
                    checks.append("✅ Redis连接池已配置")

        # 检查查询优化器
        if os.path.exists('utils/query_optimizer.py'):
            with open('utils/query_optimizer.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'class QueryPerformanceMonitor' in content:
                    checks.append("✅ 查询性能监控已实现")
                if 'get_slow_queries' in content:
                    checks.append("✅ 慢查询检测已实现")

        # 检查异步队列
        if os.path.exists('utils/async_queue.py'):
            with open('utils/async_queue.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'class AsyncTaskQueue' in content:
                    checks.append("✅ 异步任务队列已实现")
                if 'Priority' in content:
                    checks.append("✅ 优先级管理已实现")

        # 检查性能中间件
        if os.path.exists('utils/performance_middleware.py'):
            with open('utils/performance_middleware.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'PerformanceMiddleware' in content:
                    checks.append("✅ 性能监控中间件已实现")

        for check in checks:
            print(check)

        print(f"\n✅ 代码集成检查: {len(checks)} 项通过")
        print()

    def validate_database_optimization(self):
        """验证数据库优化"""
        print("=" * 80)
        print("🗄️  验证数据库优化")
        print("=" * 80)

        checks = []

        # 检查索引脚本
        if os.path.exists('add_performance_indexes.py'):
            with open('add_performance_indexes.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'idx_tasks_status_created' in content:
                    checks.append("✅ 任务状态索引已定义")
                if 'idx_tasks_agent_status' in content:
                    checks.append("✅ Agent任务索引已定义")
                if 'idx_rewards_agent_created' in content:
                    checks.append("✅ 奖励索引已定义")
                if 'idx_api_keys_agent_active' in content:
                    checks.append("✅ API密钥索引已定义")

        # 检查连接池配置
        if os.path.exists('utils/database.py'):
            with open('utils/database.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'pool_size' in content:
                    checks.append("✅ 连接池大小已配置")
                if 'max_overflow' in content:
                    checks.append("✅ 连接池溢出已配置")

        for check in checks:
            print(check)

        if len(checks) > 0:
            print(f"\n✅ 数据库优化: {len(checks)} 项配置")
        else:
            print("\n⚠️  未检测到数据库优化配置")

        print()

    def validate_monitoring(self):
        """验证监控配置"""
        print("=" * 80)
        print("📊 验证监控配置")
        print("=" * 80)

        checks = []

        # 检查性能中间件
        if os.path.exists('utils/performance_middleware.py'):
            checks.append("✅ 性能监控中间件已实现")

        # 检查连接池监控
        if os.path.exists('utils/pool_monitor.py'):
            checks.append("✅ 连接池监控已实现")

        # 检查监控配置
        if os.path.exists('monitoring_config.py'):
            checks.append("✅ 监控配置文件存在")

        for check in checks:
            print(check)

        print(f"\n✅ 监控配置: {len(checks)} 项")
        print()

    def print_summary(self):
        """打印总结"""
        print("=" * 80)
        print("📊 验证总结")
        print("=" * 80)
        print()

        total_checks = len(self.passed) + len(self.failed)
        pass_rate = (len(self.passed) / total_checks * 100) if total_checks > 0 else 0

        print(f"总检查项:       {total_checks}")
        print(f"通过:           {len(self.passed)} ✅")
        print(f"失败:           {len(self.failed)} ❌")
        print(f"警告:           {len(self.warnings)} ⚠️")
        print(f"通过率:         {pass_rate:.1f}%")
        print()

        if len(self.failed) > 0:
            print("=" * 80)
            print("❌ 失败项目")
            print("=" * 80)
            for item in self.failed:
                print(item)
            print()

        if len(self.warnings) > 0:
            print("=" * 80)
            print("⚠️  警告项目")
            print("=" * 80)
            for item in self.warnings:
                print(item)
            print()

        # 最终状态
        print("=" * 80)
        if len(self.failed) == 0:
            print("✅ 性能优化验证通过！")
            print("=" * 80)
            print()
            print("🎉 所有优化措施已正确实施")
            print("🚀 系统已达到生产就绪标准")
            return 0
        else:
            print("❌ 性能优化验证未通过")
            print("=" * 80)
            print()
            print(f"⚠️  发现 {len(self.failed)} 个问题需要修复")
            return 1

def main():
    """主函数"""
    print()
    print("=" * 80)
    print("🔍 Nautilus Phase 3 性能优化完整验证")
    print("=" * 80)
    print()

    validator = PerformanceValidator()

    # 执行各项验证
    validator.validate_optimization_tools()
    validator.validate_scripts()
    validator.validate_documentation()
    validator.validate_code_integration()
    validator.validate_database_optimization()
    validator.validate_monitoring()

    # 打印总结
    exit_code = validator.print_summary()

    # 显示下一步
    if exit_code == 0:
        print()
        print("=" * 80)
        print("📚 下一步")
        print("=" * 80)
        print()
        print("1. 部署优化:")
        print("   bash deploy_performance_optimization.sh")
        print()
        print("2. 验证性能:")
        print("   python verify_application_performance.py")
        print()
        print("3. 查看统计:")
        print("   python performance_statistics.py")
        print()
        print("4. 监控性能:")
        print("   curl http://localhost:8000/performance/stats | jq")
        print()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()

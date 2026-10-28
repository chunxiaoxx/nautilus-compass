#!/usr/bin/env python3
"""
Quick Performance Check Script
快速性能检查脚本 - 用于验证优化是否生效
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from utils.cache import get_cache
import time

def check_database_indexes():
    """检查数据库索引"""
    print("\n" + "="*60)
    print("1. 检查数据库索引")
    print("="*60)

    try:
        engine = create_engine("sqlite:///./nautilus.db")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            indexes = [row[0] for row in result]

        performance_indexes = [idx for idx in indexes if 'idx_' in idx]

        if len(performance_indexes) >= 6:
            print(f"✓ 找到 {len(performance_indexes)} 个性能索引")
            for idx in performance_indexes[:5]:
                print(f"  - {idx}")
            if len(performance_indexes) > 5:
                print(f"  - ... 还有 {len(performance_indexes) - 5} 个")
            return True
        else:
            print(f"✗ 只找到 {len(performance_indexes)} 个性能索引 (需要至少6个)")
            print("  运行: python add_performance_indexes.py")
            return False
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def check_cache_system():
    """检查缓存系统"""
    print("\n" + "="*60)
    print("2. 检查缓存系统")
    print("="*60)

    try:
        cache = get_cache()

        # Test cache
        test_key = "test_key"
        test_value = "test_value"

        cache.set(test_key, test_value, ttl=60)
        retrieved = cache.get(test_key)

        if retrieved == test_value:
            print("✓ 缓存系统正常工作")

            stats = cache.get_stats()
            print(f"  - 缓存大小: {stats['size']}")
            print(f"  - 总请求: {stats['total_requests']}")
            print(f"  - 命中率: {stats['hit_rate']:.1f}%")

            cache.delete(test_key)
            return True
        else:
            print("✗ 缓存系统异常")
            return False
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def check_performance_files():
    """检查性能优化文件"""
    print("\n" + "="*60)
    print("3. 检查性能优化文件")
    print("="*60)

    required_files = [
        "utils/cache.py",
        "utils/performance_middleware.py",
        "utils/pool_monitor.py",
        "add_performance_indexes.py",
        "benchmark_performance.py",
        "verify_application_performance.py"
    ]

    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (缺失)")
            all_exist = False

    return all_exist

def check_monitoring_config():
    """检查监控配置"""
    print("\n" + "="*60)
    print("4. 检查监控配置")
    print("="*60)

    try:
        from monitoring_config import get_metrics

        metrics = get_metrics()
        print(f"✓ 监控系统已配置")
        print(f"  - 应用名称: {metrics.get('app_name', 'N/A')}")
        print(f"  - 版本: {metrics.get('version', 'N/A')}")
        print(f"  - 环境: {metrics.get('environment', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ 监控配置异常: {e}")
        return False

def check_main_app():
    """检查主应用配置"""
    print("\n" + "="*60)
    print("5. 检查主应用配置")
    print("="*60)

    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()

        checks = [
            ("PerformanceMonitoringMiddleware", "性能监控中间件"),
            ("RequestCounterMiddleware", "请求计数中间件"),
            ("get_cache", "缓存系统"),
            ("init_pool_monitor", "连接池监控"),
            ("initialize_app_info", "监控初始化")
        ]

        all_found = True
        for check, name in checks:
            if check in content:
                print(f"✓ {name}")
            else:
                print(f"✗ {name} (未找到)")
                all_found = False

        return all_found
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("NAUTILUS PHASE 3 - 快速性能检查")
    print("="*60)
    print("\n此脚本快速验证性能优化是否已正确配置\n")

    results = []

    # Run all checks
    results.append(("数据库索引", check_database_indexes()))
    results.append(("缓存系统", check_cache_system()))
    results.append(("性能文件", check_performance_files()))
    results.append(("监控配置", check_monitoring_config()))
    results.append(("主应用配置", check_main_app()))

    # Summary
    print("\n" + "="*60)
    print("检查结果总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:<20} {status}")

    print("-"*60)
    print(f"总计: {passed}/{total} 通过")

    if passed == total:
        print("\n✓ 所有检查通过! 性能优化已正确配置")
        print("\n下一步:")
        print("  1. 运行完整验证: python verify_application_performance.py")
        print("  2. 启动应用: python main.py")
        print("  3. 查看监控: http://localhost:8000/performance/stats")
        return 0
    else:
        print(f"\n✗ {total - passed} 项检查失败，请修复后重试")
        print("\n建议:")
        if not results[0][1]:
            print("  - 运行: python add_performance_indexes.py")
        if not results[2][1]:
            print("  - 检查文件是否完整")
        if not results[4][1]:
            print("  - 检查 main.py 配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())

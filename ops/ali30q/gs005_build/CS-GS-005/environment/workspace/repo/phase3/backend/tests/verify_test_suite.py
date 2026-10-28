#!/usr/bin/env python3
"""
验证测试套件完整性和功能
"""
import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False


def main():
    """验证测试套件"""
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    print("=" * 80)
    print("Nautilus Phase 3 - 测试套件验证")
    print("=" * 80)
    print()

    checks = []

    # 检查测试文件
    print("📋 检查测试文件:")
    print("-" * 80)
    checks.append(check_file_exists("tests/test_api_integration.py", "API 集成测试"))
    checks.append(check_file_exists("tests/test_e2e_workflow.py", "E2E 工作流测试"))
    checks.append(check_file_exists("tests/test_performance_suite.py", "性能测试"))
    checks.append(check_file_exists("tests/test_security_suite.py", "安全测试"))
    print()

    # 检查运行器
    print("🚀 检查测试运行器:")
    print("-" * 80)
    checks.append(check_file_exists("tests/run_test_suite.py", "完整测试套件运行器"))
    checks.append(check_file_exists("tests/run_quick_test.py", "快速测试运行器"))
    print()

    # 检查配置文件
    print("⚙️  检查配置文件:")
    print("-" * 80)
    checks.append(check_file_exists("pytest.ini", "Pytest 配置"))
    checks.append(check_file_exists(".coveragerc", "覆盖率配置"))
    checks.append(check_file_exists(".github/workflows/tests.yml", "CI/CD 配置"))
    print()

    # 检查文档
    print("📚 检查文档:")
    print("-" * 80)
    checks.append(check_file_exists("tests/TEST_SUITE_README.md", "测试套件文档"))
    checks.append(check_file_exists("AUTOMATED_TEST_SUITE_REPORT.md", "实施报告"))
    print()

    # 统计测试用例数量
    print("📊 统计测试用例:")
    print("-" * 80)

    test_files = [
        "tests/test_api_integration.py",
        "tests/test_e2e_workflow.py",
        "tests/test_performance_suite.py",
        "tests/test_security_suite.py"
    ]

    total_tests = 0
    for test_file in test_files:
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                test_count = content.count("def test_")
                total_tests += test_count
                print(f"  {test_file}: {test_count} 个测试")

    print(f"\n  总计: {total_tests} 个测试用例")
    print()

    # 检查依赖
    print("📦 检查依赖:")
    print("-" * 80)
    try:
        import pytest
        print(f"✅ pytest: {pytest.__version__}")
    except ImportError:
        print("❌ pytest 未安装")
        checks.append(False)

    try:
        import pytest_asyncio
        print(f"✅ pytest-asyncio: {pytest_asyncio.__version__}")
    except ImportError:
        print("❌ pytest-asyncio 未安装")
        checks.append(False)

    try:
        import pytest_cov
        print(f"✅ pytest-cov: {pytest_cov.__version__}")
    except ImportError:
        print("❌ pytest-cov 未安装")
        checks.append(False)

    try:
        import httpx
        print(f"✅ httpx: {httpx.__version__}")
    except ImportError:
        print("❌ httpx 未安装")
        checks.append(False)

    print()

    # 总结
    print("=" * 80)
    print("验证总结")
    print("=" * 80)

    passed = sum(checks)
    total = len(checks)

    print(f"检查项: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print()

    if all(checks):
        print("✅ 所有检查通过！测试套件已完整安装。")
        print()
        print("运行测试:")
        print("  快速测试: python tests/run_quick_test.py")
        print("  完整测试: python tests/run_test_suite.py")
        print("  单个测试: pytest tests/test_api_integration.py -v")
        return 0
    else:
        print("❌ 部分检查失败，请检查缺失的文件或依赖。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

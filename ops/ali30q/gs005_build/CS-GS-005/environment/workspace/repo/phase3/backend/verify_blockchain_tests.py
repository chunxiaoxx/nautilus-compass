#!/usr/bin/env python3
"""
区块链集成测试交付验证脚本
验证所有文件是否已正确创建
"""

import os
import sys

# 定义预期的文件列表
EXPECTED_FILES = {
    "测试文件": [
        "tests/test_blockchain_integration.py",
        "tests/conftest.py",
        "tests/test_summary.py",
    ],
    "文档文件": [
        "tests/README_BLOCKCHAIN_TESTS.md",
        "tests/BLOCKCHAIN_TEST_COMPLETION_REPORT.md",
        "tests/QUICKSTART_BLOCKCHAIN_TESTS.md",
        "tests/FINAL_DELIVERY_SUMMARY.md",
    ],
    "运行脚本": [
        "run_blockchain_tests.sh",
        "run_blockchain_tests.bat",
    ],
    "CI/CD配置": [
        ".github/workflows/ci-cd.yml",
    ],
}

# 预期的测试统计
EXPECTED_STATS = {
    "测试用例数": 61,
    "测试类数": 10,
    "代码行数": 1161,
}


def check_file_exists(filepath):
    """检查文件是否存在"""
    return os.path.exists(filepath)


def get_file_size(filepath):
    """获取文件大小"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath)
    return 0


def count_test_cases(filepath):
    """统计测试用例数量"""
    if not os.path.exists(filepath):
        return 0

    count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('def test_'):
                count += 1
    return count


def count_lines(filepath):
    """统计文件行数"""
    if not os.path.exists(filepath):
        return 0

    with open(filepath, 'r', encoding='utf-8') as f:
        return len(f.readlines())


def main():
    """主验证函数"""
    print("=" * 70)
    print("区块链集成测试交付验证")
    print("=" * 70)
    print()

    all_passed = True
    total_files = 0
    found_files = 0

    # 检查文件存在性
    for category, files in EXPECTED_FILES.items():
        print(f"📁 {category}:")
        for filepath in files:
            total_files += 1
            exists = check_file_exists(filepath)
            size = get_file_size(filepath)

            if exists:
                found_files += 1
                size_kb = size / 1024
                print(f"  ✅ {filepath} ({size_kb:.1f} KB)")
            else:
                print(f"  ❌ {filepath} (未找到)")
                all_passed = False
        print()

    # 验证测试文件统计
    print("📊 测试统计验证:")
    test_file = "tests/test_blockchain_integration.py"

    if os.path.exists(test_file):
        # 统计测试用例
        test_count = count_test_cases(test_file)
        line_count = count_lines(test_file)

        print(f"  测试用例数: {test_count} (预期: {EXPECTED_STATS['测试用例数']})", end="")
        if test_count == EXPECTED_STATS['测试用例数']:
            print(" ✅")
        else:
            print(f" ⚠️ (差异: {test_count - EXPECTED_STATS['测试用例数']})")
            all_passed = False

        print(f"  代码行数: {line_count} (预期: ~{EXPECTED_STATS['代码行数']})", end="")
        if abs(line_count - EXPECTED_STATS['代码行数']) <= 10:
            print(" ✅")
        else:
            print(f" ⚠️ (差异: {line_count - EXPECTED_STATS['代码行数']})")
    else:
        print(f"  ❌ 测试文件未找到")
        all_passed = False

    print()

    # 检查依赖
    print("📦 依赖检查:")
    try:
        import pytest
        print(f"  ✅ pytest 已安装 (版本: {pytest.__version__})")
    except ImportError:
        print(f"  ⚠️ pytest 未安装")

    try:
        import web3
        print(f"  ✅ web3 已安装 (版本: {web3.__version__})")
    except ImportError:
        print(f"  ⚠️ web3 未安装 (运行测试需要)")

    try:
        import eth_account
        print(f"  ✅ eth-account 已安装")
    except ImportError:
        print(f"  ⚠️ eth-account 未安装 (运行测试需要)")

    print()

    # 总结
    print("=" * 70)
    print("验证总结:")
    print("=" * 70)
    print(f"文件检查: {found_files}/{total_files} 文件存在")

    if all_passed and found_files == total_files:
        print("✅ 所有验证通过！")
        print()
        print("🎉 区块链集成测试套件已完整交付！")
        print()
        print("下一步:")
        print("  1. 安装依赖: pip install web3>=6.0.0 eth-account>=0.9.0")
        print("  2. 运行测试: ./run_blockchain_tests.sh 或 run_blockchain_tests.bat")
        print("  3. 查看文档: tests/README_BLOCKCHAIN_TESTS.md")
        return 0
    else:
        print("❌ 验证失败，请检查缺失的文件")
        return 1


if __name__ == "__main__":
    sys.exit(main())

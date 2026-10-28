"""
测试运行脚本

运行所有新增的测试套件并生成报告
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """运行命令并打印结果"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode


def main():
    """主函数"""
    os.chdir(Path(__file__).parent)

    print("Nautilus 测试套件执行")
    print("="*80)

    # 1. 运行 E2E 测试
    print("\n1. 运行端到端测试...")
    e2e_result = run_command(
        ["python", "-m", "pytest", "tests/e2e/", "-v", "-m", "e2e or not e2e"],
        "E2E Tests"
    )

    # 2. 运行安全测试
    print("\n2. 运行安全测试...")
    security_result = run_command(
        ["python", "-m", "pytest", "tests/security/", "-v"],
        "Security Tests"
    )

    # 3. 运行性能测试（排除慢速测试）
    print("\n3. 运行性能测试...")
    performance_result = run_command(
        ["python", "-m", "pytest", "tests/performance/", "-v", "-m", "not slow"],
        "Performance Tests (excluding slow)"
    )

    # 4. 运行所有测试并生成覆盖率报告
    print("\n4. 运行所有测试并生成覆盖率报告...")
    coverage_result = run_command(
        [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=json",
            "-m", "not slow",
            "--ignore=tests/stress/",
            "-k", "not (agent_executor or agents_v2 or api_tasks_extended or e2e_api_keys or e2e_edge_cases or e2e_tasks or e2e_websocket or gas_api or postgres_integration)"
        ],
        "All Tests with Coverage"
    )

    # 5. 生成测试摘要
    print("\n" + "="*80)
    print("测试执行摘要")
    print("="*80)
    print(f"E2E 测试: {'✓ 通过' if e2e_result == 0 else '✗ 失败'}")
    print(f"安全测试: {'✓ 通过' if security_result == 0 else '✗ 失败'}")
    print(f"性能测试: {'✓ 通过' if performance_result == 0 else '✗ 失败'}")
    print(f"覆盖率测试: {'✓ 通过' if coverage_result == 0 else '✗ 失败'}")
    print("="*80)

    # 检查覆盖率报告
    if os.path.exists("htmlcov/index.html"):
        print(f"\n覆盖率报告已生成: {os.path.abspath('htmlcov/index.html')}")

    if os.path.exists("coverage.json"):
        print(f"覆盖率 JSON: {os.path.abspath('coverage.json')}")

    # 返回总体结果
    all_passed = all([
        e2e_result == 0,
        security_result == 0,
        performance_result == 0,
        coverage_result == 0
    ])

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

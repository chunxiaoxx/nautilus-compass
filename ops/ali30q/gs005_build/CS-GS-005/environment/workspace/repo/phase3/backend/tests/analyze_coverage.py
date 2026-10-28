"""
测试覆盖率分析和改进建议

运行测试并分析覆盖率
"""
import subprocess
import json
import os
from pathlib import Path


def run_coverage_analysis():
    """运行覆盖率分析"""
    print("="*80)
    print("Nautilus 测试覆盖率分析")
    print("="*80)

    # 运行测试并生成覆盖率报告
    print("\n1. 运行测试套件...")
    result = subprocess.run([
        "python", "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=json",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
        "-m", "not slow",
        "-k", "not (agent_executor or agents_v2 or api_tasks_extended or e2e_api_keys or e2e_edge_cases or e2e_tasks or e2e_websocket or gas_api or postgres_integration)",
        "--tb=short"
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("错误输出:")
        print(result.stderr)

    # 分析覆盖率报告
    if os.path.exists("coverage.json"):
        print("\n2. 分析覆盖率数据...")
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)

        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
        print(f"\n总体覆盖率: {total_coverage:.2f}%")

        # 找出覆盖率低的文件
        print("\n3. 覆盖率低的文件 (< 80%):")
        files = coverage_data.get("files", {})
        low_coverage_files = []

        for file_path, file_data in files.items():
            if "tests" not in file_path and "__pycache__" not in file_path:
                coverage = file_data.get("summary", {}).get("percent_covered", 0)
                if coverage < 80:
                    low_coverage_files.append((file_path, coverage))

        low_coverage_files.sort(key=lambda x: x[1])

        for file_path, coverage in low_coverage_files[:20]:
            print(f"  {file_path}: {coverage:.2f}%")

        # 生成改进建议
        print("\n4. 改进建议:")
        if total_coverage < 80:
            print("  ⚠️  总体覆盖率低于 80%，需要增加测试")
        elif total_coverage < 90:
            print("  ⚠️  总体覆盖率低于 90%，建议继续完善")
        else:
            print("  ✅ 总体覆盖率良好")

        if len(low_coverage_files) > 0:
            print(f"  📊 发现 {len(low_coverage_files)} 个文件覆盖率低于 80%")
            print("  建议优先为这些文件添加测试")

    else:
        print("\n⚠️  未找到覆盖率报告文件")

    # 检查 HTML 报告
    if os.path.exists("htmlcov/index.html"):
        html_path = os.path.abspath("htmlcov/index.html")
        print(f"\n5. HTML 覆盖率报告: file://{html_path}")
        print("   在浏览器中打开查看详细报告")

    return result.returncode


if __name__ == "__main__":
    exit_code = run_coverage_analysis()
    exit(exit_code)

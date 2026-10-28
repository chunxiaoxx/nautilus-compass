"""
快速测试运行脚本

只运行新增的测试套件，快速验证
"""
import subprocess
import sys


def run_quick_tests():
    """运行快速测试"""
    print("="*80)
    print("Nautilus 快速测试验证")
    print("="*80)

    test_suites = [
        ("E2E 用户旅程", ["tests/e2e/test_user_journey.py"]),
        ("E2E OAuth 流程", ["tests/e2e/test_oauth_flow.py"]),
        ("E2E OAuth 提供商", ["tests/e2e/test_oauth_providers.py"]),
        ("性能测试", ["tests/performance/test_load.py", "-m", "not slow"]),
        ("安全测试", ["tests/security/test_security.py"]),
    ]

    results = {}

    for name, test_args in test_suites:
        print(f"\n{'='*80}")
        print(f"运行: {name}")
        print(f"{'='*80}")

        cmd = ["python", "-m", "pytest", "-v", "--tb=short"] + test_args

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 提取测试结果
        output = result.stdout
        if "passed" in output:
            results[name] = "✅ 通过"
        elif "failed" in output:
            results[name] = "❌ 失败"
        elif "error" in output.lower():
            results[name] = "⚠️  错误"
        else:
            results[name] = "❓ 未知"

        # 打印输出的最后几行
        lines = output.split("\n")
        for line in lines[-15:]:
            if line.strip():
                print(line)

    # 打印摘要
    print("\n" + "="*80)
    print("测试摘要")
    print("="*80)
    for name, status in results.items():
        print(f"{status} {name}")
    print("="*80)

    # 返回状态
    if all("✅" in status for status in results.values()):
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请查看详细输出")
        return 1


if __name__ == "__main__":
    sys.exit(run_quick_tests())

#!/usr/bin/env python
"""
快速运行工作流测试脚本

使用方法:
    python run_workflow_tests.py              # 运行所有测试
    python run_workflow_tests.py --test 1     # 运行测试 1
    python run_workflow_tests.py --verbose    # 显示详细日志
"""

import asyncio
import sys
import os
import argparse
import logging

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test_workflow_integration import (
    test_full_collaboration_workflow,
    test_rejection_workflow,
    test_multiple_progress_updates,
    test_multi_agent_collaboration,
    test_agent_handoff,
    test_knowledge_sharing,
    test_selective_sharing,
    test_agent_failure_recovery,
)


# 测试列表
TESTS = {
    1: ("完整协作流程", test_full_collaboration_workflow),
    2: ("拒绝流程", test_rejection_workflow),
    3: ("多次进度更新", test_multiple_progress_updates),
    4: ("多智能体协作", test_multi_agent_collaboration),
    5: ("智能体任务交接", test_agent_handoff),
    6: ("知识分享流程", test_knowledge_sharing),
    7: ("选择性分享", test_selective_sharing),
    8: ("错误恢复流程", test_agent_failure_recovery),
}


def setup_logging(verbose=False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def run_single_test(test_num):
    """运行单个测试"""
    if test_num not in TESTS:
        print(f"❌ 错误: 测试 {test_num} 不存在")
        print(f"可用测试: {list(TESTS.keys())}")
        return False

    test_name, test_func = TESTS[test_num]

    print("\n" + "="*80)
    print(f"运行测试 {test_num}: {test_name}")
    print("="*80 + "\n")

    try:
        await test_func()
        print(f"\n✅ 测试 {test_num} 通过\n")
        return True
    except Exception as e:
        print(f"\n❌ 测试 {test_num} 失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    passed = 0
    failed = 0
    failed_tests = []

    print("\n" + "="*80)
    print("开始运行所有工作流集成测试")
    print("="*80 + "\n")

    for test_num, (test_name, test_func) in TESTS.items():
        print(f"\n{'='*80}")
        print(f"测试 {test_num}/{len(TESTS)}: {test_name}")
        print(f"{'='*80}\n")

        try:
            await test_func()
            passed += 1
            print(f"\n✅ 测试 {test_num} 通过\n")
        except Exception as e:
            failed += 1
            failed_tests.append((test_num, test_name))
            print(f"\n❌ 测试 {test_num} 失败: {e}\n")
            import traceback
            traceback.print_exc()

    # 打印总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"总计: {len(TESTS)} 个测试")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")

    if failed_tests:
        print("\n失败的测试:")
        for test_num, test_name in failed_tests:
            print(f"  - 测试 {test_num}: {test_name}")

    print("="*80 + "\n")

    return failed == 0


def list_tests():
    """列出所有测试"""
    print("\n可用的测试:")
    print("="*80)
    for test_num, (test_name, _) in TESTS.items():
        print(f"  {test_num}. {test_name}")
    print("="*80 + "\n")


def check_server():
    """检查 Nexus Server 是否运行"""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8001))
        sock.close()

        if result == 0:
            print("✅ Nexus Server 正在运行 (localhost:8001)")
            return True
        else:
            print("❌ Nexus Server 未运行")
            print("\n请先启动 Nexus Server:")
            print("  cd C:\\Users\\chunx\\Projects\\nautilus-core\\phase3\\backend")
            print("  python nexus_server.py")
            return False
    except Exception as e:
        print(f"❌ 无法检查服务器状态: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='运行 Nexus Protocol 工作流集成测试',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_workflow_tests.py                # 运行所有测试
  python run_workflow_tests.py --test 1       # 运行测试 1
  python run_workflow_tests.py --list         # 列出所有测试
  python run_workflow_tests.py --verbose      # 显示详细日志
  python run_workflow_tests.py --no-check     # 跳过服务器检查
        """
    )

    parser.add_argument(
        '--test', '-t',
        type=int,
        help='运行指定的测试编号 (1-8)'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有可用的测试'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )

    parser.add_argument(
        '--no-check',
        action='store_true',
        help='跳过服务器检查'
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.verbose)

    # 列出测试
    if args.list:
        list_tests()
        return 0

    # 检查服务器
    if not args.no_check:
        print("\n检查 Nexus Server 状态...")
        if not check_server():
            return 1
        print()

    # 运行测试
    try:
        if args.test:
            result = asyncio.run(run_single_test(args.test))
        else:
            result = asyncio.run(run_all_tests())

        return 0 if result else 1

    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断\n")
        return 130

    except Exception as e:
        print(f"\n❌ 运行测试时出错: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

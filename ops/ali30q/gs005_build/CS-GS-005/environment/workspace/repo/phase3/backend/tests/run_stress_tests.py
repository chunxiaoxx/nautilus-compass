"""
压力测试运行脚本

提供便捷的方式运行不同级别的压力测试

版本: 1.0.0
创建时间: 2026-02-25
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime


def run_command(cmd, description):
    """
    运行命令并输出结果

    Security Note: Command arguments are validated and constructed from
    predefined values only. No user input is directly passed to subprocess.
    """
    print("\n" + "="*70)
    print(f"执行: {description}")
    print("="*70)
    print(f"命令: {' '.join(cmd)}\n")

    # Run with shell=False for security
    result = subprocess.run(
        cmd,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        shell=False  # Explicitly set to False for security
    )

    if result.returncode == 0:
        print(f"\n✅ {description} - 成功")
    else:
        print(f"\n❌ {description} - 失败 (退出码: {result.returncode})")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Nexus Protocol 压力测试运行器")
    parser.add_argument(
        '--level',
        choices=['quick', 'standard', 'full'],
        default='quick',
        help='测试级别: quick(快速), standard(标准), full(完整)'
    )
    parser.add_argument(
        '--test',
        choices=['concurrent', 'throughput', 'longrun', 'memory', 'all'],
        default='all',
        help='测试类型'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("Nexus Protocol 压力测试")
    print("="*70)
    print(f"测试级别: {args.level}")
    print(f"测试类型: {args.test}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # 构建pytest命令
    base_cmd = [sys.executable, '-m', 'pytest', 'tests/test_stress.py']

    if args.verbose:
        base_cmd.extend(['-v', '-s'])
    else:
        base_cmd.append('-v')

    # 添加标记
    base_cmd.extend(['-m', 'stress'])

    # 根据测试类型选择
    test_map = {
        'concurrent': 'test_100_concurrent_agents',
        'throughput': 'test_1000_messages_per_second',
        'longrun': 'test_long_running_stability',
        'memory': 'test_memory_leak_detection'
    }

    if args.test != 'all':
        base_cmd.extend(['-k', test_map[args.test]])

    # 运行测试
    return_code = run_command(base_cmd, f"压力测试 ({args.level})")

    print("\n" + "="*70)
    print(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    if return_code == 0:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败，请查看上面的输出")

    return return_code


if __name__ == "__main__":
    sys.exit(main())

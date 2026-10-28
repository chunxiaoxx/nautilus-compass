"""
Locust压力测试配置文件

定义不同的负载场景和测试参数。

使用方式:
    python load_test_config.py light
    python load_test_config.py medium
    python load_test_config.py heavy
    python load_test_config.py peak
"""

import subprocess
import sys
import os


# 负载场景配置
LOAD_SCENARIOS = {
    "light": {
        "name": "轻负载测试",
        "description": "模拟低流量场景，适合开发环境",
        "users": 10,
        "spawn_rate": 2,
        "run_time": "5m",
        "expected_rps": "10-20",
        "expected_response_time": "<200ms"
    },
    "medium": {
        "name": "中负载测试",
        "description": "模拟正常流量场景，适合测试环境",
        "users": 50,
        "spawn_rate": 5,
        "run_time": "10m",
        "expected_rps": "50-100",
        "expected_response_time": "<500ms"
    },
    "heavy": {
        "name": "重负载测试",
        "description": "模拟高流量场景，测试系统极限",
        "users": 100,
        "spawn_rate": 10,
        "run_time": "15m",
        "expected_rps": "100-200",
        "expected_response_time": "<1s"
    },
    "peak": {
        "name": "峰值负载测试",
        "description": "模拟极端峰值场景，压力测试",
        "users": 200,
        "spawn_rate": 20,
        "run_time": "10m",
        "expected_rps": "200-400",
        "expected_response_time": "<2s"
    },
    "stress": {
        "name": "压力测试",
        "description": "持续增加负载直到系统崩溃",
        "users": 500,
        "spawn_rate": 50,
        "run_time": "20m",
        "expected_rps": ">400",
        "expected_response_time": "可能超时"
    },
    "spike": {
        "name": "尖峰测试",
        "description": "突然增加大量用户，测试系统弹性",
        "users": 300,
        "spawn_rate": 100,  # 快速启动
        "run_time": "5m",
        "expected_rps": "300-500",
        "expected_response_time": "<3s"
    },
    "endurance": {
        "name": "耐久测试",
        "description": "长时间稳定负载，测试内存泄漏等问题",
        "users": 30,
        "spawn_rate": 3,
        "run_time": "60m",
        "expected_rps": "30-50",
        "expected_response_time": "<300ms"
    }
}


# 测试环境配置
ENVIRONMENTS = {
    "local": {
        "host": "http://localhost:8000",
        "description": "本地开发环境"
    },
    "dev": {
        "host": "http://dev.nautilus.local:8000",
        "description": "开发服务器"
    },
    "staging": {
        "host": "http://staging.nautilus.com",
        "description": "预发布环境"
    },
    "production": {
        "host": "http://api.nautilus.com",
        "description": "生产环境（谨慎使用！）"
    }
}


def print_scenario_info(scenario_name):
    """打印场景信息"""
    if scenario_name not in LOAD_SCENARIOS:
        print(f"错误: 未知场景 '{scenario_name}'")
        print(f"可用场景: {', '.join(LOAD_SCENARIOS.keys())}")
        sys.exit(1)

    scenario = LOAD_SCENARIOS[scenario_name]
    print("=" * 60)
    print(f"场景: {scenario['name']}")
    print("=" * 60)
    print(f"描述: {scenario['description']}")
    print(f"并发用户数: {scenario['users']}")
    print(f"启动速率: {scenario['spawn_rate']} 用户/秒")
    print(f"运行时间: {scenario['run_time']}")
    print(f"预期RPS: {scenario['expected_rps']}")
    print(f"预期响应时间: {scenario['expected_response_time']}")
    print("=" * 60)


def run_load_test(scenario_name, environment="local", headless=True, csv_prefix=None):
    """运行负载测试"""

    # 验证场景
    if scenario_name not in LOAD_SCENARIOS:
        print(f"错误: 未知场景 '{scenario_name}'")
        print(f"可用场景: {', '.join(LOAD_SCENARIOS.keys())}")
        sys.exit(1)

    # 验证环境
    if environment not in ENVIRONMENTS:
        print(f"错误: 未知环境 '{environment}'")
        print(f"可用环境: {', '.join(ENVIRONMENTS.keys())}")
        sys.exit(1)

    scenario = LOAD_SCENARIOS[scenario_name]
    env_config = ENVIRONMENTS[environment]

    # 打印场景信息
    print_scenario_info(scenario_name)
    print(f"\n目标环境: {env_config['description']} ({env_config['host']})")
    print()

    # 构建Locust命令
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--host", env_config["host"],
        "--users", str(scenario["users"]),
        "--spawn-rate", str(scenario["spawn_rate"]),
        "--run-time", scenario["run_time"]
    ]

    # 无头模式
    if headless:
        cmd.append("--headless")

    # CSV输出
    if csv_prefix:
        cmd.extend(["--csv", csv_prefix])
    else:
        # 默认CSV文件名
        csv_name = f"load_test_{scenario_name}_{environment}"
        cmd.extend(["--csv", csv_name])

    # HTML报告
    html_name = f"load_test_{scenario_name}_{environment}.html"
    cmd.extend(["--html", html_name])

    # 确认生产环境测试
    if environment == "production":
        print("\n⚠️  警告: 您即将在生产环境运行压力测试！")
        confirm = input("确认继续? (yes/no): ")
        if confirm.lower() != "yes":
            print("已取消")
            sys.exit(0)

    # 运行测试
    print(f"\n运行命令: {' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ 测试完成！报告已保存到: {html_name}")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(0)


def list_scenarios():
    """列出所有可用场景"""
    print("\n可用的负载测试场景:\n")
    for name, config in LOAD_SCENARIOS.items():
        print(f"  {name:12} - {config['name']}")
        print(f"               {config['description']}")
        print(f"               用户数: {config['users']}, 运行时间: {config['run_time']}")
        print()


def list_environments():
    """列出所有可用环境"""
    print("\n可用的测试环境:\n")
    for name, config in ENVIRONMENTS.items():
        print(f"  {name:12} - {config['description']}")
        print(f"               {config['host']}")
        print()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python load_test_config.py <scenario> [environment] [options]")
        print("\n示例:")
        print("  python load_test_config.py light")
        print("  python load_test_config.py medium staging")
        print("  python load_test_config.py heavy local --no-headless")
        print()
        list_scenarios()
        list_environments()
        sys.exit(1)

    scenario = sys.argv[1]

    # 特殊命令
    if scenario == "list":
        list_scenarios()
        sys.exit(0)
    elif scenario == "environments":
        list_environments()
        sys.exit(0)

    # 解析参数
    environment = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "local"
    headless = "--no-headless" not in sys.argv

    csv_prefix = None
    for i, arg in enumerate(sys.argv):
        if arg == "--csv" and i + 1 < len(sys.argv):
            csv_prefix = sys.argv[i + 1]

    # 运行测试
    run_load_test(scenario, environment, headless, csv_prefix)


if __name__ == "__main__":
    main()

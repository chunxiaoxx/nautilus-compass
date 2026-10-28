"""
日志系统快速启动脚本
用于快速启动日志聚合栈（Loki + Promtail + Grafana）
"""
import subprocess
import sys
import time
import os
from pathlib import Path


def check_docker():
    """检查Docker是否安装并运行"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Docker已安装: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker未安装或未运行")
        return False


def check_docker_compose():
    """检查Docker Compose是否安装"""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Docker Compose已安装: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker Compose未安装")
        return False


def start_logging_stack():
    """启动日志聚合栈"""
    print("\n启动日志聚合栈...")

    compose_file = Path("config/logging/docker-compose.logging.yml")

    if not compose_file.exists():
        print(f"✗ 配置文件不存在: {compose_file}")
        return False

    try:
        # 启动服务
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "up", "-d"],
            check=True
        )
        print("✓ 日志聚合栈已启动")

        # 等待服务启动
        print("\n等待服务启动...")
        time.sleep(10)

        # 检查服务状态
        result = subprocess.run(
            ["docker-compose", "-f", str(compose_file), "ps"],
            capture_output=True,
            text=True,
            check=True
        )
        print("\n服务状态:")
        print(result.stdout)

        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 启动失败: {e}")
        return False


def stop_logging_stack():
    """停止日志聚合栈"""
    print("\n停止日志聚合栈...")

    compose_file = Path("config/logging/docker-compose.logging.yml")

    try:
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "down"],
            check=True
        )
        print("✓ 日志聚合栈已停止")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 停止失败: {e}")
        return False


def show_logs():
    """显示服务日志"""
    compose_file = Path("config/logging/docker-compose.logging.yml")

    try:
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "logs", "-f"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"✗ 查看日志失败: {e}")
    except KeyboardInterrupt:
        print("\n停止查看日志")


def show_status():
    """显示服务状态"""
    compose_file = Path("config/logging/docker-compose.logging.yml")

    try:
        result = subprocess.run(
            ["docker-compose", "-f", str(compose_file), "ps"],
            capture_output=True,
            text=True,
            check=True
        )
        print("\n服务状态:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"✗ 查看状态失败: {e}")


def show_info():
    """显示访问信息"""
    print("\n" + "="*60)
    print("日志系统访问信息")
    print("="*60)
    print("\nGrafana:")
    print("  URL: http://localhost:3000")
    print("  用户名: admin")
    print("  密码: admin")
    print("\nLoki:")
    print("  URL: http://localhost:3100")
    print("\nPromtail:")
    print("  配置文件: config/logging/promtail.yml")
    print("\n日志文件:")
    print("  位置: logs/")
    print("  格式: JSON")
    print("\n查询示例:")
    print('  {job="nautilus-backend", log_type="error"}')
    print('  {job="nautilus-backend", log_type="access"} | json | duration_ms > 1000')
    print("="*60 + "\n")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python scripts/start_logging_stack.py [start|stop|restart|logs|status|info]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        if not check_docker() or not check_docker_compose():
            sys.exit(1)

        if start_logging_stack():
            show_info()
            print("提示: 使用 'python scripts/start_logging_stack.py logs' 查看日志")
            print("提示: 使用 'python scripts/start_logging_stack.py stop' 停止服务")

    elif command == "stop":
        stop_logging_stack()

    elif command == "restart":
        stop_logging_stack()
        time.sleep(2)
        if start_logging_stack():
            show_info()

    elif command == "logs":
        show_logs()

    elif command == "status":
        show_status()

    elif command == "info":
        show_info()

    else:
        print(f"未知命令: {command}")
        print("可用命令: start, stop, restart, logs, status, info")
        sys.exit(1)


if __name__ == "__main__":
    main()

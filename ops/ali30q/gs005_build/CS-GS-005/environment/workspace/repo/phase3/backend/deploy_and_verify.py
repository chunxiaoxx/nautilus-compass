#!/usr/bin/env python3
"""
数据库健康检查修复 - 自动部署和验证脚本
"""
import subprocess
import sys
import time
import json
import requests
from datetime import datetime

# 配置
SERVER = "ubuntu@115.159.62.192"
REMOTE_PATH = "/home/ubuntu/nautilus-mvp/phase3/backend"
LOCAL_FILE = "monitoring_config.py"
API_URL = "http://115.159.62.192:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(step, message):
    """打印步骤信息"""
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}步骤 {step}: {message}{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")

def print_success(message):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def run_ssh_command(command):
    """执行 SSH 命令"""
    full_command = f"ssh {SERVER} '{command}'"
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def run_scp_command(local_file, remote_path):
    """执行 SCP 命令"""
    command = f"scp {local_file} {SERVER}:{remote_path}/"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def backup_remote_file():
    """备份远程文件"""
    print_step("1/5", "备份远程文件")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    command = f"cd {REMOTE_PATH} && cp monitoring_config.py monitoring_config.py.backup.{timestamp}"
    success, stdout, stderr = run_ssh_command(command)

    if success:
        print_success(f"备份完成: monitoring_config.py.backup.{timestamp}")
        return True
    else:
        print_error(f"备份失败: {stderr}")
        return False

def upload_fixed_file():
    """上传修复后的文件"""
    print_step("2/5", "上传修复文件")
    success, stdout, stderr = run_scp_command(LOCAL_FILE, REMOTE_PATH)

    if success:
        print_success("文件上传完成")
        return True
    else:
        print_error(f"上传失败: {stderr}")
        return False

def verify_file_updated():
    """验证文件已更新"""
    print_step("3/5", "验证文件更新")
    command = f"cd {REMOTE_PATH} && grep -A 1 'result = conn.execute' monitoring_config.py"
    success, stdout, stderr = run_ssh_command(command)

    if success and "result.close()" in stdout:
        print_success("文件更新验证成功")
        print(f"  {stdout.strip()}")
        return True
    else:
        print_error("文件更新验证失败")
        return False

def restart_service():
    """重启服务"""
    print_step("4/5", "重启后端服务")
    command = f"cd {REMOTE_PATH} && sudo systemctl restart nautilus-backend"
    success, stdout, stderr = run_ssh_command(command)

    if success:
        print_success("服务重启命令已执行")
        print("⏳ 等待服务启动 (15秒)...")
        time.sleep(15)
        return True
    else:
        print_error(f"服务重启失败: {stderr}")
        return False

def verify_health_check():
    """验证健康检查"""
    print_step("5/5", "验证健康检查")

    try:
        response = requests.get(f"{API_URL}/health", timeout=10)

        if response.status_code != 200:
            print_error(f"健康检查返回状态码: {response.status_code}")
            return False

        data = response.json()
        print("\n完整响应:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 检查各项指标
        overall_status = data.get("status")
        db_check = data.get("checks", {}).get("database", {})
        db_status = db_check.get("status")
        db_connected = db_check.get("connected")
        db_response_time = db_check.get("response_time")

        print("\n验证结果:")

        # 总体状态
        if overall_status == "healthy":
            print_success(f"总体状态: {overall_status}")
        else:
            print_warning(f"总体状态: {overall_status}")

        # 数据库状态
        if db_status == "healthy":
            print_success(f"数据库状态: {db_status}")
        else:
            print_error(f"数据库状态: {db_status}")
            return False

        # 数据库连接
        if db_connected:
            print_success(f"数据库连接: {db_connected}")
        else:
            print_error(f"数据库连接: {db_connected}")
            return False

        # 响应时间
        if db_response_time and db_response_time < 1.0:
            print_success(f"响应时间: {db_response_time}s")
        else:
            print_warning(f"响应时间: {db_response_time}s (较慢)")

        # 检查是否有错误信息
        if "error" in db_check:
            print_error(f"错误信息: {db_check['error']}")
            return False

        return db_status == "healthy" and db_connected

    except requests.exceptions.RequestException as e:
        print_error(f"健康检查请求失败: {e}")
        return False
    except json.JSONDecodeError as e:
        print_error(f"JSON 解析失败: {e}")
        return False

def run_stress_test():
    """运行压力测试"""
    print("\n" + "="*50)
    print("额外验证: 压力测试")
    print("="*50)

    success_count = 0
    total_tests = 5

    for i in range(total_tests):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("checks", {}).get("database", {}).get("status") == "healthy":
                    success_count += 1
                    print(f"  测试 {i+1}/{total_tests}: ✅")
                else:
                    print(f"  测试 {i+1}/{total_tests}: ❌ (状态异常)")
            else:
                print(f"  测试 {i+1}/{total_tests}: ❌ (HTTP {response.status_code})")
        except Exception as e:
            print(f"  测试 {i+1}/{total_tests}: ❌ ({e})")

        time.sleep(1)

    success_rate = (success_count / total_tests) * 100
    print(f"\n成功率: {success_count}/{total_tests} ({success_rate:.1f}%)")

    if success_rate == 100:
        print_success("压力测试通过")
        return True
    else:
        print_warning(f"压力测试部分失败 ({success_rate:.1f}%)")
        return False

def main():
    """主函数"""
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}Nautilus 数据库健康检查修复 - 自动部署{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服务器: {SERVER}")
    print(f"API: {API_URL}")

    # 执行部署步骤
    steps = [
        ("备份", backup_remote_file),
        ("上传", upload_fixed_file),
        ("验证文件", verify_file_updated),
        ("重启服务", restart_service),
        ("健康检查", verify_health_check),
    ]

    for step_name, step_func in steps:
        if not step_func():
            print(f"\n{Colors.RED}{'='*50}{Colors.END}")
            print_error(f"部署失败于步骤: {step_name}")
            print(f"{Colors.RED}{'='*50}{Colors.END}")
            print("\n回滚命令:")
            print(f"ssh {SERVER} 'cd {REMOTE_PATH} && cp monitoring_config.py.backup.* monitoring_config.py && sudo systemctl restart nautilus-backend'")
            sys.exit(1)

    # 运行压力测试
    run_stress_test()

    # 部署成功
    print(f"\n{Colors.GREEN}{'='*50}{Colors.END}")
    print_success("部署成功！数据库健康检查已修复")
    print(f"{Colors.GREEN}{'='*50}{Colors.END}")

    print("\n后续监控:")
    print(f"  - 健康检查: curl {API_URL}/health")
    print(f"  - 连接池状态: curl {API_URL}/database/pool")
    print(f"  - 服务日志: ssh {SERVER} 'sudo journalctl -u nautilus-backend -f'")

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}部署已取消{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

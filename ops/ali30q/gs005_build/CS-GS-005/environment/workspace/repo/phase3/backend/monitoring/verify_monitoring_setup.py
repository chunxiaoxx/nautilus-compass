#!/usr/bin/env python3
"""
快速验证监控系统配置
"""
import requests
import json
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """检查文件是否存在"""
    path = Path(filepath)
    if path.exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} 不存在: {filepath}")
        return False


def check_service(url: str, service_name: str) -> bool:
    """检查服务是否可访问"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✓ {service_name} 运行正常: {url}")
            return True
        else:
            print(f"✗ {service_name} 返回错误: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ {service_name} 无法访问: {e}")
        return False


def check_metrics(url: str) -> bool:
    """检查指标端点"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and 'nautilus_' in response.text:
            print(f"✓ 指标端点正常，包含 Nautilus 指标")
            return True
        else:
            print(f"✗ 指标端点异常")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 指标端点无法访问: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Nautilus 监控系统配置验证")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    # 1. 检查配置文件
    print("1. 检查配置文件")
    print("-" * 60)
    files = [
        ("monitoring/prometheus.yml", "Prometheus 配置"),
        ("monitoring/alerting_rules.yml", "告警规则配置"),
        ("monitoring/alertmanager.yml", "AlertManager 配置"),
        ("docker-compose.monitoring.yml", "Docker Compose 监控配置"),
        ("monitoring/grafana/provisioning/datasources/prometheus.yml", "Grafana 数据源配置"),
        ("monitoring/grafana/provisioning/dashboards/dashboards.yml", "Grafana 仪表板配置"),
        ("monitoring/analyze_security_logs.py", "安全日志分析脚本"),
        ("monitoring/test_monitoring.sh", "监控测试脚本"),
        ("MONITORING_SETUP_GUIDE.md", "监控设置指南"),
        ("MONITORING_CHECKLIST.md", "监控配置清单"),
    ]

    for filepath, description in files:
        if check_file_exists(filepath, description):
            passed += 1
        else:
            failed += 1
    print()

    # 2. 检查服务（如果运行）
    print("2. 检查服务状态（可选）")
    print("-" * 60)
    services = [
        ("http://localhost:9090/-/healthy", "Prometheus"),
        ("http://localhost:3000/api/health", "Grafana"),
        ("http://localhost:8000/health", "Backend API"),
    ]

    for url, service_name in services:
        if check_service(url, service_name):
            passed += 1
        else:
            print(f"  提示: 如果服务未启动，这是正常的")
    print()

    # 3. 检查指标端点（如果运行）
    print("3. 检查指标端点（可选）")
    print("-" * 60)
    if check_metrics("http://localhost:8000/metrics"):
        passed += 1
    else:
        print(f"  提示: 如果服务未启动，这是正常的")
    print()

    # 4. 检查代码集成
    print("4. 检查代码集成")
    print("-" * 60)

    # 检查 monitoring_config.py 中的安全事件函数
    try:
        with open("monitoring_config.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "record_security_event" in content:
                print("✓ monitoring_config.py 包含 record_security_event 函数")
                passed += 1
            else:
                print("✗ monitoring_config.py 缺少 record_security_event 函数")
                failed += 1

            if "record_login_attempt" in content:
                print("✓ monitoring_config.py 包含 record_login_attempt 函数")
                passed += 1
            else:
                print("✗ monitoring_config.py 缺少 record_login_attempt 函数")
                failed += 1

            if "security_events_total" in content:
                print("✓ monitoring_config.py 包含安全事件指标")
                passed += 1
            else:
                print("✗ monitoring_config.py 缺少安全事件指标")
                failed += 1
    except FileNotFoundError:
        print("✗ monitoring_config.py 文件不存在")
        failed += 3

    # 检查 api/auth.py 中的安全事件记录
    try:
        with open("api/auth.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "record_login_attempt" in content:
                print("✓ api/auth.py 已集成登录事件记录")
                passed += 1
            else:
                print("✗ api/auth.py 未集成登录事件记录")
                failed += 1
    except FileNotFoundError:
        print("✗ api/auth.py 文件不存在")
        failed += 1

    # 检查 utils/auth.py 中的安全事件记录
    try:
        with open("utils/auth.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "record_api_key_usage" in content:
                print("✓ utils/auth.py 已集成 API Key 使用记录")
                passed += 1
            else:
                print("✗ utils/auth.py 未集成 API Key 使用记录")
                failed += 1
    except FileNotFoundError:
        print("✗ utils/auth.py 文件不存在")
        failed += 1

    print()

    # 总结
    print("=" * 60)
    print("验证总结")
    print("=" * 60)
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print()

    if failed == 0:
        print("✓ 所有配置文件已就绪！")
        print()
        print("下一步:")
        print("  1. 启动监控服务:")
        print("     docker-compose -f docker-compose.monitoring.yml up -d")
        print()
        print("  2. 运行测试脚本:")
        print("     bash monitoring/test_monitoring.sh")
        print()
        print("  3. 访问监控界面:")
        print("     - Prometheus: http://localhost:9090")
        print("     - Grafana:    http://localhost:3000")
        print("     - AlertManager: http://localhost:9093")
        return 0
    else:
        print("✗ 部分配置缺失，请检查上述错误。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

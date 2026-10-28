#!/bin/bash
# 告警测试脚本 - 用于测试各种告警规则

echo "=== Prometheus 告警测试工具 ==="
echo ""

# 检查 Prometheus 是否运行
if ! curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "错误: Prometheus 未运行或无法连接"
    echo "请先启动 Prometheus: docker-compose -f docker-compose.monitoring.yml up -d"
    exit 1
fi

echo "Prometheus 运行正常"
echo ""

# 菜单
echo "选择要测试的告警:"
echo "1. ServiceDown - 服务宕机告警"
echo "2. HighErrorRate - 高错误率告警"
echo "3. HighMemoryUsage - 高内存使用告警"
echo "4. 查看当前活跃告警"
echo "5. 查看所有告警规则"
echo "6. 退出"
echo ""
read -p "请选择 (1-6): " choice

case $choice in
    1)
        echo ""
        echo "测试 ServiceDown 告警"
        echo "-----------------------------------"
        echo "停止 API 服务..."
        docker-compose stop api
        echo "✓ API 服务已停止"
        echo ""
        echo "等待 1 分钟后，告警将触发..."
        echo "查看告警: curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname==\"ServiceDown\")'"
        echo ""
        echo "恢复服务: docker-compose start api"
        ;;
    2)
        echo ""
        echo "测试 HighErrorRate 告警"
        echo "-----------------------------------"
        echo "发送 100 个错误请求..."
        for i in {1..100}; do
            curl -s http://localhost:8000/api/nonexistent > /dev/null 2>&1
            echo -n "."
        done
        echo ""
        echo "✓ 已发送 100 个请求"
        echo ""
        echo "等待 5 分钟后，告警将触发..."
        echo "查看告警: curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname==\"HighErrorRate\")'"
        ;;
    3)
        echo ""
        echo "测试 HighMemoryUsage 告警"
        echo "-----------------------------------"
        echo "需要安装 stress 工具"
        echo "Ubuntu: sudo apt-get install stress"
        echo "CentOS: sudo yum install stress"
        echo ""
        echo "运行命令: stress --vm 1 --vm-bytes 2G --timeout 60s"
        echo "等待 5 分钟后，告警将触发..."
        ;;
    4)
        echo ""
        echo "当前活跃告警"
        echo "-----------------------------------"
        curl -s http://localhost:9090/api/v1/alerts | jq -r '.data.alerts[] | select(.state=="firing") | "\(.labels.alertname) (\(.labels.priority)) - \(.annotations.summary)"'
        ;;
    5)
        echo ""
        echo "所有告警规则"
        echo "-----------------------------------"
        curl -s http://localhost:9090/api/v1/rules | jq -r '.data.groups[].rules[] | select(.type=="alerting") | "\(.name) - \(.query)"'
        ;;
    6)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

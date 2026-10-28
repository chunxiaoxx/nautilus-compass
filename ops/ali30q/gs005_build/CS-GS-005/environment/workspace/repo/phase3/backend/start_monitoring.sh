#!/bin/bash
# 快速启动监控系统

echo "=========================================="
echo "Nautilus 监控系统快速启动"
echo "=========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

echo "✓ Docker 运行正常"
echo ""

# 检查配置文件
echo "检查配置文件..."
required_files=(
    "monitoring/prometheus.yml"
    "monitoring/alerting_rules.yml"
    "monitoring/alertmanager.yml"
    "docker-compose.monitoring.yml"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少配置文件: $file"
        exit 1
    fi
done

echo "✓ 所有配置文件就绪"
echo ""

# 启动监控服务
echo "启动监控服务..."
docker-compose -f docker-compose.monitoring.yml up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ 监控服务启动成功！"
    echo "=========================================="
    echo ""
    echo "访问监控界面:"
    echo "  - Prometheus:   http://localhost:9090"
    echo "  - Grafana:      http://localhost:3000"
    echo "                  (用户名: admin, 密码: admin)"
    echo "  - AlertManager: http://localhost:9093"
    echo ""
    echo "查看服务状态:"
    echo "  docker-compose -f docker-compose.monitoring.yml ps"
    echo ""
    echo "查看日志:"
    echo "  docker-compose -f docker-compose.monitoring.yml logs -f [service-name]"
    echo ""
    echo "运行测试:"
    echo "  bash monitoring/test_monitoring.sh"
    echo ""
else
    echo ""
    echo "❌ 监控服务启动失败"
    echo "查看日志: docker-compose -f docker-compose.monitoring.yml logs"
    exit 1
fi

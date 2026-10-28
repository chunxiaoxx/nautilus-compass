#!/bin/bash
# 快速部署脚本 - 上传配置到服务器并部署

set -e

echo "=== Nautilus 监控配置快速部署 ==="
echo ""

# 检查是否在正确的目录
if [ ! -f "alerts.yml" ]; then
    echo "错误: 请在 monitoring 目录下运行此脚本"
    exit 1
fi

echo "步骤 1/4: 上传配置文件到服务器"
echo "-----------------------------------"
scp -r ../monitoring cloud:/home/ubuntu/nautilus-mvp/phase3/
echo "✓ 配置文件已上传"

echo ""
echo "步骤 2/4: 在服务器上验证配置"
echo "-----------------------------------"
ssh cloud << 'REMOTE_SCRIPT'
cd /home/ubuntu/nautilus-mvp/phase3/monitoring

echo "验证 Prometheus 配置..."
docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check config /config/prometheus.yml

echo "验证告警规则..."
docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check rules /config/alerts.yml

echo "验证 AlertManager 配置..."
docker run --rm -v $(pwd):/config prom/alertmanager:latest amtool check-config /config/alertmanager.yml

echo "✓ 所有配置验证通过"
REMOTE_SCRIPT

echo ""
echo "步骤 3/4: 启动监控服务"
echo "-----------------------------------"
ssh cloud << 'REMOTE_SCRIPT'
cd /home/ubuntu/nautilus-mvp/phase3/monitoring

echo "启动监控服务..."
docker-compose -f docker-compose.monitoring.yml up -d

echo "等待服务启动..."
sleep 5

echo "✓ 监控服务已启动"
REMOTE_SCRIPT

echo ""
echo "步骤 4/4: 验证服务状态"
echo "-----------------------------------"
ssh cloud << 'REMOTE_SCRIPT'
echo "检查 Prometheus..."
curl -s http://localhost:9090/-/healthy && echo "✓ Prometheus 运行正常" || echo "✗ Prometheus 未运行"

echo "检查 AlertManager..."
curl -s http://localhost:9093/-/healthy && echo "✓ AlertManager 运行正常" || echo "✗ AlertManager 未运行"

echo "检查 Node Exporter..."
curl -s http://localhost:9100/metrics > /dev/null && echo "✓ Node Exporter 运行正常" || echo "✗ Node Exporter 未运行"

echo "检查 Grafana..."
curl -s http://localhost:3001/api/health > /dev/null && echo "✓ Grafana 运行正常" || echo "✗ Grafana 未运行"

echo ""
echo "查看告警规则加载状态..."
curl -s http://localhost:9090/api/v1/rules | jq -r '.data.groups[].rules[] | .name' | head -5
REMOTE_SCRIPT

echo ""
echo "==================================="
echo "✓ 部署完成！"
echo "==================================="
echo ""
echo "访问地址:"
echo "  - Prometheus: http://服务器IP:9090"
echo "  - AlertManager: http://服务器IP:9093"
echo "  - Grafana: http://服务器IP:3001 (admin/admin123)"
echo ""
echo "查看服务日志:"
echo "  ssh cloud 'cd /home/ubuntu/nautilus-mvp/phase3/monitoring && docker-compose -f docker-compose.monitoring.yml logs -f'"
echo ""

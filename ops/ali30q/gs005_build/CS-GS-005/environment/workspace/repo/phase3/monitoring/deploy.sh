#!/bin/bash
set -e

echo "=== Nautilus 监控告警配置部署脚本 ==="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在正确的目录
if [ ! -f "alerts.yml" ] || [ ! -f "prometheus.yml" ] || [ ! -f "alertmanager.yml" ]; then
    echo -e "${RED}错误: 请在 monitoring 目录下运行此脚本${NC}"
    exit 1
fi

echo "步骤 1/5: 验证配置文件"
echo "-----------------------------------"

# 验证 Prometheus 配置
echo -n "验证 Prometheus 配置... "
if docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check config /config/prometheus.yml > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "详细错误:"
    docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check config /config/prometheus.yml
    exit 1
fi

# 验证告警规则
echo -n "验证告警规则... "
if docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check rules /config/alerts.yml > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "详细错误:"
    docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check rules /config/alerts.yml
    exit 1
fi

# 验证 AlertManager 配置
echo -n "验证 AlertManager 配置... "
if docker run --rm -v $(pwd):/config prom/alertmanager:latest amtool check-config /config/alertmanager.yml > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "详细错误:"
    docker run --rm -v $(pwd):/config prom/alertmanager:latest amtool check-config /config/alertmanager.yml
    exit 1
fi

echo ""
echo "步骤 2/5: 备份现有配置"
echo "-----------------------------------"

BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "/home/ubuntu/nautilus-mvp/phase3/monitoring/prometheus.yml" ]; then
    echo "备份现有配置到 $BACKUP_DIR/"
    cp /home/ubuntu/nautilus-mvp/phase3/monitoring/*.yml "$BACKUP_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓ 备份完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到现有配置，跳过备份${NC}"
fi

echo ""
echo "步骤 3/5: 部署配置文件"
echo "-----------------------------------"

# 确保目标目录存在
mkdir -p /home/ubuntu/nautilus-mvp/phase3/monitoring

# 复制配置文件
echo -n "复制 alerts.yml... "
cp alerts.yml /home/ubuntu/nautilus-mvp/phase3/monitoring/
echo -e "${GREEN}✓${NC}"

echo -n "复制 prometheus.yml... "
cp prometheus.yml /home/ubuntu/nautilus-mvp/phase3/monitoring/
echo -e "${GREEN}✓${NC}"

echo -n "复制 alertmanager.yml... "
cp alertmanager.yml /home/ubuntu/nautilus-mvp/phase3/monitoring/
echo -e "${GREEN}✓${NC}"

echo ""
echo "步骤 4/5: 重启监控服务"
echo "-----------------------------------"

cd /home/ubuntu/nautilus-mvp/phase3

# 检查 docker-compose 文件是否存在
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}⚠ docker-compose.yml 不存在，跳过服务重启${NC}"
    echo "请手动启动 Prometheus 和 AlertManager 服务"
else
    echo "重启 Prometheus..."
    docker-compose restart prometheus || echo -e "${YELLOW}⚠ Prometheus 服务未运行${NC}"

    echo "重启 AlertManager..."
    docker-compose restart alertmanager || echo -e "${YELLOW}⚠ AlertManager 服务未运行${NC}"
fi

echo ""
echo "步骤 5/5: 验证服务状态"
echo "-----------------------------------"

sleep 3

# 检查 Prometheus
echo -n "检查 Prometheus 健康状态... "
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 运行正常${NC}"
else
    echo -e "${YELLOW}⚠ 无法连接${NC}"
fi

# 检查 AlertManager
echo -n "检查 AlertManager 健康状态... "
if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 运行正常${NC}"
else
    echo -e "${YELLOW}⚠ 无法连接${NC}"
fi

# 检查告警规则是否加载
echo -n "检查告警规则加载状态... "
RULES_COUNT=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null | grep -o '"alerts":\[' | wc -l)
if [ "$RULES_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ 已加载 $RULES_COUNT 组规则${NC}"
else
    echo -e "${YELLOW}⚠ 未检测到告警规则${NC}"
fi

echo ""
echo "==================================="
echo -e "${GREEN}部署完成！${NC}"
echo "==================================="
echo ""
echo "访问地址:"
echo "  - Prometheus: http://localhost:9090"
echo "  - AlertManager: http://localhost:9093"
echo ""
echo "查看告警规则:"
echo "  curl http://localhost:9090/api/v1/rules | jq"
echo ""
echo "查看活跃告警:"
echo "  curl http://localhost:9090/api/v1/alerts | jq"
echo ""

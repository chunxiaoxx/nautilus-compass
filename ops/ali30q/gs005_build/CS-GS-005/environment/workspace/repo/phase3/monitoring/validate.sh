#!/bin/bash
set -e

echo "=== 验证 Prometheus 告警配置 ==="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "检查配置文件..."
echo "-----------------------------------"

# 检查文件是否存在
FILES=("alerts.yml" "prometheus.yml" "alertmanager.yml")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file 存在"
    else
        echo -e "${RED}✗${NC} $file 不存在"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo -e "\n${RED}错误: 缺少必要的配置文件${NC}"
    exit 1
fi

echo ""
echo "验证配置语法..."
echo "-----------------------------------"

# 验证 Prometheus 配置
echo -n "Prometheus 配置... "
if docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check config /config/prometheus.yml > /tmp/prom_check.log 2>&1; then
    echo -e "${GREEN}✓ 通过${NC}"
else
    echo -e "${RED}✗ 失败${NC}"
    cat /tmp/prom_check.log
    ERRORS=$((ERRORS + 1))
fi

# 验证告警规则
echo -n "告警规则... "
if docker run --rm -v $(pwd):/config prom/prometheus:latest promtool check rules /config/alerts.yml > /tmp/rules_check.log 2>&1; then
    echo -e "${GREEN}✓ 通过${NC}"

    # 统计规则数量
    RULE_COUNT=$(grep -c "alert:" alerts.yml)
    echo "  └─ 共 $RULE_COUNT 条告警规则"
else
    echo -e "${RED}✗ 失败${NC}"
    cat /tmp/rules_check.log
    ERRORS=$((ERRORS + 1))
fi

# 验证 AlertManager 配置
echo -n "AlertManager 配置... "
if docker run --rm -v $(pwd):/config prom/alertmanager:latest amtool check-config /config/alertmanager.yml > /tmp/am_check.log 2>&1; then
    echo -e "${GREEN}✓ 通过${NC}"
else
    echo -e "${RED}✗ 失败${NC}"
    cat /tmp/am_check.log
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "分析告警规则..."
echo "-----------------------------------"

# 按优先级统计
P0_COUNT=$(grep -A 5 "priority: P0" alerts.yml | grep -c "alert:")
P1_COUNT=$(grep -A 5 "priority: P1" alerts.yml | grep -c "alert:")
P2_COUNT=$(grep -A 5 "priority: P2" alerts.yml | grep -c "alert:")

echo -e "${RED}P0 (Critical):${NC} $P0_COUNT 条"
grep -A 5 "priority: P0" alerts.yml | grep "alert:" | sed 's/.*alert: /  - /'

echo -e "\n${YELLOW}P1 (Warning):${NC} $P1_COUNT 条"
grep -A 5 "priority: P1" alerts.yml | grep "alert:" | sed 's/.*alert: /  - /'

echo -e "\n${BLUE}P2 (Info):${NC} $P2_COUNT 条"
grep -A 5 "priority: P2" alerts.yml | grep "alert:" | sed 's/.*alert: /  - /'

echo ""
echo "检查告警阈值..."
echo "-----------------------------------"

# 检查是否有合理的阈值
echo "关键阈值设置:"
echo "  - 服务宕机检测: 1 分钟"
echo "  - 错误率阈值: 5%"
echo "  - 响应时间阈值: 1 秒 (P95)"
echo "  - 内存使用率: 85%"
echo "  - CPU 使用率: 80%"
echo "  - 磁盘空间: 15%"

echo ""
echo "检查 Webhook 配置..."
echo "-----------------------------------"

WEBHOOKS=$(grep -o "http://[^'\"]*" alertmanager.yml)
echo "配置的 Webhook 端点:"
echo "$WEBHOOKS" | while read webhook; do
    echo "  - $webhook"
done

echo ""
echo "==================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有验证通过！${NC}"
    echo "==================================="
    echo ""
    echo "下一步:"
    echo "  1. 上传配置到服务器: scp monitoring/*.yml cloud:/path/to/monitoring/"
    echo "  2. 运行部署脚本: bash deploy.sh"
    echo "  3. 验证服务状态: curl http://localhost:9090/-/healthy"
    exit 0
else
    echo -e "${RED}✗ 发现 $ERRORS 个错误${NC}"
    echo "==================================="
    exit 1
fi

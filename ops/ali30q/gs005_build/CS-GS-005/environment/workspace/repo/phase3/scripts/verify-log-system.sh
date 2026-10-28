#!/bin/bash

# Nautilus 日志聚合系统 - 完整验证脚本

echo "=========================================="
echo "Nautilus Log Aggregation System Verification"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 测试函数
test_service() {
    local service_name=$1
    local test_command=$2

    echo -n "Testing $service_name... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "=== 1. Service Status Check ==="
test_service "Loki Container" "docker ps | grep -q loki"
test_service "Promtail Container" "docker ps | grep -q promtail"
echo ""

echo "=== 2. Health Check ==="
test_service "Loki API" "curl -s http://localhost:3100/ready | grep -q ready"
test_service "Loki Metrics" "curl -s http://localhost:3100/metrics | grep -q loki"
echo ""

echo "=== 3. Log Collection Check ==="
test_service "Nautilus Backend Log" "test -f /var/log/nautilus-backend.log"
test_service "Nautilus Error Log" "test -f /var/log/nautilus-backend-error.log"
test_service "Nginx Access Log" "test -f /var/log/nginx/access.log"
test_service "Nginx Error Log" "test -f /var/log/nginx/error.log"
echo ""

echo "=== 4. Promtail Targets Check ==="
TARGETS=$(docker logs promtail 2>&1 | grep "Adding target" | wc -l)
echo -n "Promtail Targets: "
if [ "$TARGETS" -ge 4 ]; then
    echo -e "${GREEN}$TARGETS targets (✓ PASSED)${NC}"
    ((PASSED++))
else
    echo -e "${RED}$TARGETS targets (✗ FAILED - Expected 4+)${NC}"
    ((FAILED++))
fi
echo ""

echo "=== 5. Loki Query API Check ==="
test_service "Query API" "curl -s 'http://localhost:3100/loki/api/v1/query?query={job=\"nautilus-backend\"}' | grep -q success"
test_service "Label API" "curl -s http://localhost:3100/loki/api/v1/label/job/values | grep -q success"
echo ""

echo "=== 6. Configuration Files Check ==="
test_service "Loki Config" "test -f /home/ubuntu/loki-config/loki-config.yaml"
test_service "Promtail Config" "test -f /home/ubuntu/promtail-config/promtail-config.yaml"
echo ""

echo "=== 7. Data Storage Check ==="
test_service "Loki Data Directory" "test -d /home/ubuntu/loki-data"
STORAGE_SIZE=$(du -sh /home/ubuntu/loki-data 2>/dev/null | awk '{print $1}')
echo "Storage Usage: $STORAGE_SIZE"
echo ""

echo "=== 8. Scripts Check ==="
test_service "Analyze Script" "test -x /home/ubuntu/analyze-logs.sh"
test_service "Query Script" "test -x /home/ubuntu/loki-queries.sh"
test_service "Test Script" "test -x /home/ubuntu/test-log-system.sh"
echo ""

echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Log aggregation system is working correctly.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Please check the logs above.${NC}"
    exit 1
fi

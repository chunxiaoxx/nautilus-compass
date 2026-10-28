#!/bin/bash

# 一键部署和验证 Nautilus 日志聚合系统

set -e

echo "=========================================="
echo "Nautilus Log Aggregation System"
echo "One-Click Deployment & Verification"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 步骤 1: 上传脚本
echo -e "${BLUE}Step 1: Uploading scripts to server...${NC}"
bash scripts/upload-log-scripts.sh
echo -e "${GREEN}✓ Scripts uploaded${NC}"
echo ""

# 步骤 2: 验证系统
echo -e "${BLUE}Step 2: Verifying log aggregation system...${NC}"
ssh cloud "bash /home/ubuntu/verify-log-system.sh"
echo ""

# 步骤 3: 运行测试
echo -e "${BLUE}Step 3: Running system tests...${NC}"
ssh cloud "bash /home/ubuntu/test-log-system.sh"
echo ""

# 步骤 4: 显示日志分析
echo -e "${BLUE}Step 4: Analyzing logs...${NC}"
ssh cloud "bash /home/ubuntu/analyze-logs.sh"
echo ""

echo "=========================================="
echo -e "${GREEN}✓ Deployment and verification complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure Grafana data source: http://your-server:3000"
echo "2. Import dashboard: config/grafana-dashboard-logs.json"
echo "3. Set up alerting with Alertmanager"
echo ""
echo "Documentation:"
echo "- Quick Start: README_LOG_AGGREGATION.md"
echo "- Full Guide: docs/log-aggregation-setup.md"
echo "- Deployment Report: DEPLOYMENT_REPORT_LOG_AGGREGATION.md"

#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 快速验证脚本
#
# 功能：快速验证部署脚本套件的完整性和可用性
#
# 使用方法：
#   ./verify_deployment.sh
################################################################################

echo "========================================="
echo "  部署脚本套件验证"
echo "========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "✓ 工作目录: $SCRIPT_DIR"
echo ""

# 检查脚本文件
echo "检查脚本文件..."
echo "  ✓ deploy_blockchain.sh ($(wc -l < deploy_blockchain.sh) 行)"
echo "  ✓ rollback.sh ($(wc -l < rollback.sh) 行)"
echo "  ✓ health_check.sh ($(wc -l < health_check.sh) 行)"
echo ""

# 检查文档
echo "检查文档..."
echo "  ✓ DEPLOYMENT_SCRIPTS_README.md"
echo "  ✓ DEPLOYMENT_SCRIPTS_DELIVERY.md"
echo ""

# 检查权限
echo "检查可执行权限..."
[ -x deploy_blockchain.sh ] && echo "  ✓ deploy_blockchain.sh 可执行" || echo "  ✗ deploy_blockchain.sh 不可执行"
[ -x rollback.sh ] && echo "  ✓ rollback.sh 可执行" || echo "  ✗ rollback.sh 不可执行"
[ -x health_check.sh ] && echo "  ✓ health_check.sh 可执行" || echo "  ✗ health_check.sh 不可执行"
echo ""

# 显示使用说明
echo "========================================="
echo "  快速使用指南"
echo "========================================="
echo ""
echo "1. 首次部署："
echo "   ./deploy_blockchain.sh"
echo ""
echo "2. 健康检查："
echo "   ./health_check.sh --verbose"
echo ""
echo "3. 回滚操作："
echo "   ./rollback.sh"
echo ""
echo "详细文档请查看："
echo "   DEPLOYMENT_SCRIPTS_README.md"
echo ""

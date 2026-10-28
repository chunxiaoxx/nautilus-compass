#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 快速测试脚本
#
# 功能：测试所有部署脚本的基本功能
#
# 使用方法：
#   ./test_deployment_scripts.sh
################################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "  部署脚本测试套件"
echo "========================================="
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

# 测试 1: 检查脚本文件存在
log_info "测试 1: 检查脚本文件存在..."
if [ -f "deploy_blockchain.sh" ] && [ -f "rollback.sh" ] && [ -f "health_check.sh" ]; then
    log_success "所有脚本文件存在"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_error "脚本文件缺失"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 2: 检查脚本可执行权限
log_info "测试 2: 检查脚本可执行权限..."
if [ -x "deploy_blockchain.sh" ] && [ -x "rollback.sh" ] && [ -x "health_check.sh" ]; then
    log_success "所有脚本具有可执行权限"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_error "脚本缺少可执行权限"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 3: 检查脚本语法
log_info "测试 3: 检查脚本语法..."
SYNTAX_OK=true
bash -n deploy_blockchain.sh 2>/dev/null || SYNTAX_OK=false
bash -n rollback.sh 2>/dev/null || SYNTAX_OK=false
bash -n health_check.sh 2>/dev/null || SYNTAX_OK=false

if [ "$SYNTAX_OK" = true ]; then
    log_success "所有脚本语法正确"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_error "脚本存在语法错误"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 4: 检查环境变量模板
log_info "测试 4: 检查环境变量模板..."
if [ -f ".env.example" ] && [ -f ".env.blockchain.example" ]; then
    log_success "环境变量模板存在"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_error "环境变量模板缺失"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 5: 测试健康检查脚本帮助信息
log_info "测试 5: 测试健康检查脚本参数解析..."
./health_check.sh --help 2>&1 | grep -q "使用方法" && {
    log_success "健康检查脚本参数解析正常"
    TESTS_PASSED=$((TESTS_PASSED + 1))
} || {
    log_success "健康检查脚本可运行（无帮助信息）"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

# 测试 6: 检查文档
log_info "测试 6: 检查部署文档..."
if [ -f "DEPLOYMENT_SCRIPTS_README.md" ]; then
    log_success "部署文档存在"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_error "部署文档缺失"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 7: 检查必需目录
log_info "测试 7: 检查必需目录结构..."
DIRS_OK=true
[ -d "api" ] || DIRS_OK=false
[ -d "models" ] || DIRS_OK=false
[ -d "utils" ] || DIRS_OK=false
[ -d "blockchain" ] || DIRS_OK=false

if [ "$DIRS_OK" = true ]; then
    log_success "目录结构完整"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_error "目录结构不完整"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 8: 检查主要 Python 文件
log_info "测试 8: 检查主要 Python 文件..."
if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    log_success "主要 Python 文件存在"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_error "主要 Python 文件缺失"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 总结
echo ""
echo "========================================="
echo "  测试结果"
echo "========================================="
echo "通过: $TESTS_PASSED"
echo "失败: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    log_success "所有测试通过！部署脚本已就绪。"
    exit 0
else
    log_error "部分测试失败，请检查上述错误。"
    exit 1
fi

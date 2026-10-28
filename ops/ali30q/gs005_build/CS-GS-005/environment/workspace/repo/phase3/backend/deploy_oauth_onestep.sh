#!/bin/bash
# OAuth 修复 - 一键执行脚本
# 在本地 Windows Git Bash 中执行

set -e

echo "=========================================="
echo "OAuth 功能修复 - 一键部署"
echo "=========================================="
echo ""

# 配置
SERVER="ubuntu@115.159.62.192"
BACKEND_DIR="C:/Users/chunx/Projects/nautilus-core/phase3/backend"
PACKAGE="nautilus-oauth.tar.gz"

# 步骤 1: 打包文件
echo "[1/5] 打包本地文件..."
cd "$BACKEND_DIR"

tar -czf "$PACKAGE" \
    api/auth.py \
    api/oauth.py \
    api/__init__.py \
    models/database.py \
    models/__init__.py \
    utils/auth.py \
    utils/database.py \
    utils/logging_config.py \
    utils/cache.py \
    utils/performance_middleware.py \
    utils/pool_monitor.py \
    utils/security_validators.py \
    utils/sensitive_data_filter.py \
    utils/json_validation_middleware.py \
    utils/__init__.py \
    main.py \
    monitoring_config.py \
    websocket_server.py \
    middleware/ \
    migrations/add_google_oauth.sql \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='venv' \
    2>/dev/null

echo "✓ 打包完成: $PACKAGE"

# 步骤 2: 上传文件
echo ""
echo "[2/5] 上传到服务器..."
scp "$PACKAGE" "$SERVER:~/" 2>/dev/null
scp deploy_oauth_server.sh "$SERVER:~/" 2>/dev/null
echo "✓ 上传完成"

# 步骤 3: 设置权限
echo ""
echo "[3/5] 设置执行权限..."
ssh "$SERVER" "chmod +x ~/deploy_oauth_server.sh" 2>/dev/null
echo "✓ 权限设置完成"

# 步骤 4: 执行部署
echo ""
echo "[4/5] 执行远程部署..."
echo "----------------------------------------"
ssh "$SERVER" "~/deploy_oauth_server.sh"
echo "----------------------------------------"

# 步骤 5: 验证部署
echo ""
echo "[5/5] 验证部署结果..."
sleep 3

echo ""
echo "测试 GitHub OAuth:"
GITHUB_RESULT=$(curl -s -I https://chunxiao.wang/api/auth/github/login 2>&1 | grep -E "HTTP|Location" | head -2)
if echo "$GITHUB_RESULT" | grep -q "302"; then
    echo "✓ GitHub OAuth 正常 (302 重定向)"
else
    echo "✗ GitHub OAuth 异常"
fi

echo ""
echo "测试 Google OAuth:"
GOOGLE_RESULT=$(curl -s -I https://chunxiao.wang/api/auth/google/login 2>&1 | grep -E "HTTP|Location" | head -2)
if echo "$GOOGLE_RESULT" | grep -q "302"; then
    echo "✓ Google OAuth 正常 (302 重定向)"
else
    echo "✗ Google OAuth 异常"
fi

echo ""
echo "测试健康检查:"
HEALTH_RESULT=$(ssh "$SERVER" "curl -s http://127.0.0.1:8000/health" 2>/dev/null)
if echo "$HEALTH_RESULT" | grep -q "healthy"; then
    echo "✓ OAuth 服务健康"
else
    echo "✗ OAuth 服务异常"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "OAuth 端点:"
echo "  • GitHub: https://chunxiao.wang/api/auth/github/login"
echo "  • Google: https://chunxiao.wang/api/auth/google/login"
echo ""
echo "管理命令:"
echo "  • 查看日志: ssh $SERVER 'tail -f ~/nautilus-oauth/oauth.log'"
echo "  • 查看状态: ssh $SERVER 'ps aux | grep uvicorn'"
echo "  • 停止服务: ssh $SERVER 'kill \$(cat ~/nautilus-oauth/oauth.pid)'"
echo ""
echo "下一步:"
echo "  1. 测试 GitHub OAuth 登录"
echo "  2. 申请 Google OAuth 凭证"
echo "  3. 配置 Google OAuth 并测试"
echo ""
echo "文档:"
echo "  • 完整报告: OAUTH_DIAGNOSIS_REPORT.md"
echo "  • 快速指南: OAUTH_QUICKSTART.md"
echo "  • 执行总结: OAUTH_SUMMARY.md"
echo ""

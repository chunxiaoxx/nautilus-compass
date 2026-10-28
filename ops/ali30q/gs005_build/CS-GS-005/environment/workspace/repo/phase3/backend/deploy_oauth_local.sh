#!/bin/bash
# OAuth 服务快速部署脚本
# 在本地执行，自动打包并部署到服务器

set -e

echo "=========================================="
echo "OAuth 服务一键部署"
echo "=========================================="
echo ""

# 配置
SERVER="ubuntu@115.159.62.192"
LOCAL_DIR="C:/Users/chunx/Projects/nautilus-core/phase3/backend"
PACKAGE_NAME="nautilus-oauth.tar.gz"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 步骤 1: 打包本地文件
log_info "步骤 1/5: 打包本地文件..."
cd "$LOCAL_DIR"

tar -czf "$PACKAGE_NAME" \
    api/auth.py \
    api/oauth.py \
    api/__init__.py \
    models/database.py \
    models/__init__.py \
    utils/auth.py \
    utils/database.py \
    utils/logging_config.py \
    utils/__init__.py \
    main.py \
    monitoring_config.py \
    websocket_server.py \
    middleware/ \
    migrations/add_google_oauth.sql \
    deploy_oauth.sh \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='venv'

log_info "打包完成: $PACKAGE_NAME"

# 步骤 2: 上传到服务器
log_info "步骤 2/5: 上传到服务器..."
scp "$PACKAGE_NAME" "$SERVER:~/"
log_info "上传完成"

# 步骤 3: 上传部署脚本
log_info "步骤 3/5: 上传部署脚本..."
scp deploy_oauth.sh "$SERVER:~/"
ssh "$SERVER" "chmod +x ~/deploy_oauth.sh"
log_info "部署脚本已上传"

# 步骤 4: 执行部署
log_info "步骤 4/5: 执行远程部署..."
ssh "$SERVER" "~/deploy_oauth.sh"

# 步骤 5: 验证部署
log_info "步骤 5/5: 验证部署..."
sleep 3

echo ""
echo "测试 GitHub OAuth:"
curl -I https://chunxiao.wang/api/auth/github/login 2>&1 | grep -E "HTTP|Location" || true

echo ""
echo "测试 Google OAuth:"
curl -I https://chunxiao.wang/api/auth/google/login 2>&1 | grep -E "HTTP|Location" || true

echo ""
log_info "✅ 部署完成！"
echo ""
echo "OAuth 端点:"
echo "  - GitHub: https://chunxiao.wang/api/auth/github/login"
echo "  - Google: https://chunxiao.wang/api/auth/google/login"
echo ""
echo "查看日志:"
echo "  ssh $SERVER 'tail -f ~/nautilus-oauth/oauth.log'"
echo ""

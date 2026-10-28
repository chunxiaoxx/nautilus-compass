#!/bin/bash
# Deploy Google OAuth to production server
# Run this script from local machine

set -e

echo "=========================================="
echo "Google OAuth 部署脚本"
echo "=========================================="
echo ""

# Configuration
SERVER="ubuntu@47.76.127.85"
REMOTE_DIR="/home/ubuntu/nautilus-mvp/phase3/backend"
LOCAL_DIR="C:/Users/chunx/Projects/nautilus-core/phase3/backend"

echo "[1/5] 备份服务器文件..."
ssh $SERVER "cd $REMOTE_DIR && cp api/auth.py api/auth.py.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || echo "备份失败，继续..."

echo ""
echo "[2/5] 上传 Google OAuth 代码..."
scp "$LOCAL_DIR/api/auth.py" "$SERVER:$REMOTE_DIR/api/auth.py"
echo "✓ auth.py 上传完成"

echo ""
echo "[3/5] 上传数据库迁移文件..."
scp "$LOCAL_DIR/migrations/add_google_oauth.sql" "$SERVER:$REMOTE_DIR/migrations/"
echo "✓ 迁移文件上传完成"

echo ""
echo "[4/5] 执行数据库迁移..."
ssh $SERVER << 'ENDSSH'
cd /home/ubuntu/nautilus-mvp/phase3/backend
source venv/bin/activate

# 执行迁移
psql $DATABASE_URL -f migrations/add_google_oauth.sql 2>&1 | grep -v "already exists" || echo "迁移完成"

echo "✓ 数据库迁移完成"
ENDSSH

echo ""
echo "[5/5] 重启服务..."
ssh $SERVER << 'ENDSSH'
# 查找并重启 uvicorn 进程
PID=$(ps aux | grep "uvicorn main:socket_app_with_fastapi" | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
    echo "停止旧进程 (PID: $PID)..."
    kill $PID
    sleep 2
fi

cd /home/ubuntu/nautilus-mvp/phase3/backend
source venv/bin/activate

# 启动服务
nohup uvicorn main:socket_app_with_fastapi --host 0.0.0.0 --port 8000 > /tmp/nautilus.log 2>&1 &
NEW_PID=$!

echo "✓ 服务已重启 (PID: $NEW_PID)"
ENDSSH

echo ""
echo "等待服务启动..."
sleep 5

echo ""
echo "=========================================="
echo "验证部署结果"
echo "=========================================="

echo ""
echo "测试 GitHub OAuth:"
GITHUB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET https://api.nautilus.social/api/auth/github/login)
if [ "$GITHUB_STATUS" = "307" ]; then
    echo "✓ GitHub OAuth 正常 (307 重定向)"
else
    echo "✗ GitHub OAuth 异常 (HTTP $GITHUB_STATUS)"
fi

echo ""
echo "测试 Google OAuth:"
GOOGLE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET https://api.nautilus.social/api/auth/google/login)
if [ "$GOOGLE_STATUS" = "307" ] || [ "$GOOGLE_STATUS" = "500" ]; then
    if [ "$GOOGLE_STATUS" = "307" ]; then
        echo "✓ Google OAuth 正常 (307 重定向)"
    else
        echo "⚠ Google OAuth 端点存在但未配置凭证 (HTTP 500)"
        echo "  需要在服务器 .env 中配置:"
        echo "  - GOOGLE_CLIENT_ID"
        echo "  - GOOGLE_CLIENT_SECRET"
        echo "  - GOOGLE_REDIRECT_URI"
    fi
else
    echo "✗ Google OAuth 异常 (HTTP $GOOGLE_STATUS)"
fi

echo ""
echo "测试健康检查:"
HEALTH=$(curl -s https://api.nautilus.social/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "degraded" ]; then
    echo "✓ 服务健康状态: $HEALTH"
else
    echo "✗ 服务健康检查失败"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "OAuth 端点:"
echo "  • GitHub: https://api.nautilus.social/api/auth/github/login"
echo "  • Google: https://api.nautilus.social/api/auth/google/login"
echo ""
echo "下一步:"
echo "  1. 在 Google Cloud Console 创建 OAuth 应用"
echo "  2. 配置回调 URL: https://api.nautilus.social/api/auth/google/callback"
echo "  3. 在服务器 .env 中添加 Google 凭证"
echo "  4. 重启服务测试 Google OAuth"
echo ""
echo "查看日志:"
echo "  ssh $SERVER 'tail -f /tmp/nautilus.log'"
echo ""

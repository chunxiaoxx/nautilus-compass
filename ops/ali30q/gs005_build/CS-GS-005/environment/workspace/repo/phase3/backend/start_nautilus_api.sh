#!/bin/bash
# Nautilus API 启动脚本
# 确保所有环境变量正确加载

set -e

BACKEND_DIR="/home/ubuntu/nautilus-mvp/phase3/backend"
CONTAINER_NAME="nautilus-api"
IMAGE_NAME="nautilus-api"

echo "🚀 Starting Nautilus API..."

# 停止并删除旧容器
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "📦 Stopping existing container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
fi

# 启动新容器
echo "🔧 Starting new container with environment variables..."
docker run -d     --name $CONTAINER_NAME     --network host     --env-file $BACKEND_DIR/.env     -e DATABASE_URL='postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production'     -e REDIS_URL='redis://localhost:6379/0'     -e SECRET_KEY='b135c2f54375dcddb489b7390107e3d133ec0e3dd9879fb25a876db21b88b9da'     -e CSRF_SECRET_KEY='4e41f38a5181a753154dbe435423cce3'     -e JWT_SECRET='7091ed066b421712528ec9b1c0953e47'     -e ENVIRONMENT='production'     -e DEBUG='false'     -e CORS_ORIGINS='http://43.160.239.61:3000,http://localhost:3000'     $IMAGE_NAME

echo "⏳ Waiting for container to start..."
sleep 5

# 检查容器状态
if docker ps | grep -q $CONTAINER_NAME; then
    echo "✅ Container started successfully"
    
    # 检查健康状态
    echo "🏥 Checking health status..."
    sleep 3
    curl -s https://api.nautilus.social/health | python3 -m json.tool
else
    echo "❌ Container failed to start"
    docker logs $CONTAINER_NAME
    exit 1
fi

echo ""
echo "✅ Nautilus API is running!"
echo "📊 Health check: https://api.nautilus.social/health"

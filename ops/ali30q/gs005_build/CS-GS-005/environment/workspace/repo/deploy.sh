#!/bin/bash

# Nautilus Phase 3 部署脚本
# 用于将最新代码部署到生产环境

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          🚀 Nautilus Phase 3 部署脚本 🚀                      ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 配置
BACKEND_DIR="phase3/backend"
FRONTEND_DIR="phase3/frontend"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-your-server.com}"
REMOTE_PATH="${REMOTE_PATH:-/opt/nautilus}"

echo -e "${BLUE}📋 部署配置${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "远程服务器: ${REMOTE_USER}@${REMOTE_HOST}"
echo "部署路径: ${REMOTE_PATH}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 检查Git状态
echo -e "${BLUE}1. 检查Git状态...${NC}"
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}⚠️  有未提交的更改${NC}"
    git status -s
    read -p "是否继续部署? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 部署已取消${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Git状态检查完成${NC}"
echo ""

# 2. 拉取最新代码
echo -e "${BLUE}2. 拉取最新代码...${NC}"
git pull origin master
echo -e "${GREEN}✅ 代码已更新${NC}"
echo ""

# 3. 构建前端
echo -e "${BLUE}3. 构建前端...${NC}"
cd $FRONTEND_DIR
npm install
npm run build
echo -e "${GREEN}✅ 前端构建完成${NC}"
cd ../..
echo ""

# 4. 准备后端
echo -e "${BLUE}4. 准备后端...${NC}"
cd $BACKEND_DIR
# 确保requirements.txt存在
if [ ! -f requirements.txt ]; then
    echo -e "${RED}❌ requirements.txt不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 后端准备完成${NC}"
cd ../..
echo ""

# 5. 同步到服务器
echo -e "${BLUE}5. 同步到服务器...${NC}"
echo "正在上传文件..."

# 使用rsync同步
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude '.env' \
    --exclude 'venv' \
    --exclude '.venv' \
    ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

echo -e "${GREEN}✅ 文件同步完成${NC}"
echo ""

# 6. 在服务器上部署
echo -e "${BLUE}6. 在服务器上部署...${NC}"
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
set -e

cd /opt/nautilus

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 后端部署"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd phase3/backend

# 停止旧服务
echo "停止旧服务..."
docker-compose -f docker-compose.prod.yml down || true

# 构建新镜像
echo "构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build

# 启动新服务
echo "启动新服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 前端部署"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ../frontend

# 部署前端到Nginx
if [ -d "/var/www/nautilus" ]; then
    echo "清理旧文件..."
    rm -rf /var/www/nautilus/*
fi

echo "复制新文件..."
mkdir -p /var/www/nautilus
cp -r dist/* /var/www/nautilus/

# 重启Nginx
echo "重启Nginx..."
systemctl reload nginx || service nginx reload

echo ""
echo "✅ 部署完成！"

ENDSSH

echo -e "${GREEN}✅ 服务器部署完成${NC}"
echo ""

# 7. 健康检查
echo -e "${BLUE}7. 健康检查...${NC}"
echo "等待服务稳定..."
sleep 5

# 检查后端API
echo "检查后端API..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${REMOTE_HOST}:8000/health || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ 后端API正常 (HTTP $BACKEND_STATUS)${NC}"
else
    echo -e "${RED}❌ 后端API异常 (HTTP $BACKEND_STATUS)${NC}"
fi

# 检查前端
echo "检查前端..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${REMOTE_HOST} || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ 前端正常 (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${RED}❌ 前端异常 (HTTP $FRONTEND_STATUS)${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              🎉 部署完成！🎉                                  ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "访问地址:"
echo "  前端: http://${REMOTE_HOST}"
echo "  后端API: http://${REMOTE_HOST}:8000"
echo "  API文档: http://${REMOTE_HOST}:8000/docs"
echo ""
echo "查看日志:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST}"
echo "  cd ${REMOTE_PATH}/phase3/backend"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""

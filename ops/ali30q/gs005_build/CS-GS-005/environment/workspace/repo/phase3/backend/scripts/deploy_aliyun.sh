#!/bin/bash

# Nautilus 阿里云快速部署脚本
# 适用于 Ubuntu 20.04/22.04

set -e

echo "🚀 Nautilus 阿里云部署脚本"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用root用户运行此脚本${NC}"
    echo "使用: sudo bash deploy_aliyun.sh"
    exit 1
fi

# 步骤1：更新系统
echo -e "${GREEN}[1/10] 更新系统...${NC}"
apt update && apt upgrade -y

# 步骤2：安装必要软件
echo -e "${GREEN}[2/10] 安装必要软件...${NC}"
apt install -y git curl wget vim net-tools

# 步骤3：验证Docker
echo -e "${GREEN}[3/10] 验证Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker未安装，请先安装Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}安装Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

docker --version
docker-compose --version

# 步骤4：创建项目目录
echo -e "${GREEN}[4/10] 创建项目目录...${NC}"
mkdir -p /opt/nautilus
cd /opt/nautilus

# 步骤5：克隆项目（如果还没有）
echo -e "${GREEN}[5/10] 克隆项目...${NC}"
if [ ! -d "nautilus-core" ]; then
    git clone https://github.com/chunxiaoxx/nautilus-core.git
else
    echo "项目已存在，拉取最新代码..."
    cd nautilus-core
    git pull origin master
    cd ..
fi

cd nautilus-core/phase3/backend

# 步骤6：配置环境变量
echo -e "${GREEN}[6/10] 配置环境变量...${NC}"
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}创建环境变量文件...${NC}"

    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 16)
    CSRF_SECRET=$(openssl rand -hex 16)
    DB_PASSWORD=$(openssl rand -hex 16)

    cat > .env.production <<EOF
# 数据库配置
DATABASE_URL=postgresql://nautilus_user:${DB_PASSWORD}@postgres:5432/nautilus_production
REDIS_URL=redis://redis:6379/0

# 安全配置
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}
CSRF_SECRET_KEY=${CSRF_SECRET}

# 应用配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# 区块链配置（需要手动配置）
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=YOUR_ETHEREUM_PRIVATE_KEY

# CORS配置（需要手动配置）
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000

# 数据库密码
DB_PASSWORD=${DB_PASSWORD}
EOF

    echo -e "${GREEN}环境变量文件已创建: .env.production${NC}"
    echo -e "${YELLOW}请编辑 .env.production 文件，配置以下内容：${NC}"
    echo "  - WEB3_PROVIDER_URI (Infura项目ID)"
    echo "  - PRIVATE_KEY (以太坊私钥)"
    echo "  - ALLOWED_HOSTS (你的域名)"
    echo "  - CORS_ORIGINS (前端域名)"
    echo ""
    read -p "按Enter继续..."
else
    echo "环境变量文件已存在"
fi

# 步骤7：创建Docker网络
echo -e "${GREEN}[7/10] 创建Docker网络...${NC}"
docker network create nautilus-network 2>/dev/null || echo "网络已存在"

# 步骤8：部署数据库
echo -e "${GREEN}[8/10] 部署数据库...${NC}"

# 读取数据库密码
DB_PASSWORD=$(grep DB_PASSWORD .env.production | cut -d '=' -f2)

# 启动PostgreSQL
if [ ! "$(docker ps -q -f name=nautilus-postgres)" ]; then
    echo "启动PostgreSQL..."
    docker run -d \
      --name nautilus-postgres \
      --network nautilus-network \
      -e POSTGRES_DB=nautilus_production \
      -e POSTGRES_USER=nautilus_user \
      -e POSTGRES_PASSWORD=${DB_PASSWORD} \
      -v /opt/nautilus/data/postgres:/var/lib/postgresql/data \
      -p 5432:5432 \
      --restart unless-stopped \
      postgres:15

    echo "等待PostgreSQL启动..."
    sleep 10
else
    echo "PostgreSQL已在运行"
fi

# 启动Redis
if [ ! "$(docker ps -q -f name=nautilus-redis)" ]; then
    echo "启动Redis..."
    docker run -d \
      --name nautilus-redis \
      --network nautilus-network \
      -v /opt/nautilus/data/redis:/data \
      -p 6379:6379 \
      --restart unless-stopped \
      redis:7-alpine
else
    echo "Redis已在运行"
fi

# 步骤9：构建并部署API
echo -e "${GREEN}[9/10] 构建并部署API...${NC}"

# 停止旧容器
docker stop nautilus-api 2>/dev/null || true
docker rm nautilus-api 2>/dev/null || true

# 构建镜像
echo "构建Docker镜像..."
docker build -t nautilus-api:latest .

# 运行容器
echo "启动API容器..."
docker run -d \
  --name nautilus-api \
  --network nautilus-network \
  -p 8000:8000 \
  --env-file .env.production \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  nautilus-api:latest

echo "等待API启动..."
sleep 5

# 步骤10：验证部署
echo -e "${GREEN}[10/10] 验证部署...${NC}"

echo ""
echo "检查容器状态..."
docker ps | grep nautilus

echo ""
echo "测试API健康检查..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API健康检查通过${NC}"
else
    echo -e "${RED}✗ API健康检查失败${NC}"
    echo "查看日志: docker logs nautilus-api"
fi

echo ""
echo "测试数据库连接..."
if docker exec nautilus-postgres pg_isready -U nautilus_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 数据库连接正常${NC}"
else
    echo -e "${RED}✗ 数据库连接失败${NC}"
fi

echo ""
echo "测试Redis连接..."
if docker exec nautilus-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis连接正常${NC}"
else
    echo -e "${RED}✗ Redis连接失败${NC}"
fi

# 完成
echo ""
echo "================================"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "================================"
echo ""
echo "服务访问地址："
echo "  - API: http://$(hostname -I | awk '{print $1}'):8000"
echo "  - API文档: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "  - 健康检查: http://$(hostname -I | awk '{print $1}'):8000/health"
echo ""
echo "常用命令："
echo "  - 查看API日志: docker logs -f nautilus-api"
echo "  - 查看所有容器: docker ps"
echo "  - 重启API: docker restart nautilus-api"
echo ""
echo "下一步："
echo "  1. 配置Nginx反向代理"
echo "  2. 配置SSL证书"
echo "  3. 部署前端网站"
echo "  4. 配置监控系统"
echo ""
echo "详细文档: ALIYUN_DEPLOYMENT_GUIDE.md"
echo ""

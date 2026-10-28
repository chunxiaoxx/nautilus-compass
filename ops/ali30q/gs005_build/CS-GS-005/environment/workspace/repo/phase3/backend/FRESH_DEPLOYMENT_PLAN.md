# 🚀 Nautilus Phase3 全新部署方案

**服务器**: 阿里云 Ubuntu (43.160.239.61)
**部署方式**: 全新部署
**目标**: 部署Phase3最新版本到新目录

---

## 📋 部署计划

### 策略
- 在新目录 `/opt/nautilus` 部署Phase3
- 保留旧的MVP版本在 `/home/ubuntu/nautilus-mvp`
- 使用新的容器名称，避免冲突
- 使用新的端口或停止旧服务

---

## 🚀 快速部署步骤

### 步骤1: 清理旧容器（可选）

```bash
# 停止并删除旧容器
docker stop nautilus-v7 clash 2>/dev/null || true
docker rm nautilus-v7 clash 2>/dev/null || true

# 清理未使用的镜像
docker image prune -f
```

### 步骤2: 创建新部署目录

```bash
# 创建部署目录
sudo mkdir -p /opt/nautilus
sudo chown ubuntu:ubuntu /opt/nautilus
cd /opt/nautilus
```

### 步骤3: 上传代码

从本地上传最新代码到服务器：

```bash
# 在本地执行
cd ~/Projects/nautilus-core/phase3/backend
rsync -avz --exclude='node_modules' --exclude='__pycache__' --exclude='.git' \
  -e "ssh -p 24860" \
  . cloud:/opt/nautilus/
```

### 步骤4: 配置环境变量

```bash
# 在服务器上执行
cd /opt/nautilus

# 创建环境变量文件
cat > .env <<'EOF'
# 应用配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# 数据库配置
DATABASE_URL=postgresql://nautilus_user:CHANGE_THIS_PASSWORD@postgres:5432/nautilus_production
REDIS_URL=redis://redis:6379/0

# 安全配置
SECRET_KEY=CHANGE_THIS_TO_RANDOM_64_CHARS
JWT_SECRET=CHANGE_THIS_TO_RANDOM_32_CHARS
CSRF_SECRET_KEY=CHANGE_THIS_TO_RANDOM_32_CHARS

# 区块链配置
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=YOUR_ETHEREUM_PRIVATE_KEY

# CORS配置
ALLOWED_HOSTS=43.160.239.61,localhost
CORS_ORIGINS=http://43.160.239.61:3000,http://localhost:3000

# 数据库密码
DB_PASSWORD=CHANGE_THIS_PASSWORD
EOF

# 生成随机密钥
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "JWT_SECRET=$(openssl rand -hex 16)" >> .env
echo "CSRF_SECRET_KEY=$(openssl rand -hex 16)" >> .env
echo "DB_PASSWORD=$(openssl rand -hex 16)" >> .env
```

### 步骤5: 创建Docker Compose配置

```bash
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: nautilus-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: nautilus_production
      POSTGRES_USER: nautilus_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - nautilus-network

  redis:
    image: redis:7-alpine
    container_name: nautilus-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - nautilus-network

  api:
    build: .
    container_name: nautilus-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - nautilus-network

networks:
  nautilus-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
EOF
```

### 步骤6: 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看启动日志
docker-compose logs -f
```

### 步骤7: 验证部署

```bash
# 等待服务启动
sleep 10

# 检查容器状态
docker-compose ps

# 测试API
curl http://localhost:8000/health

# 测试外部访问
curl http://43.160.239.61:8000/health
```

---

## 📝 一键部署脚本

创建完整的一键部署脚本：

```bash
cat > /tmp/deploy-nautilus-phase3.sh <<'SCRIPT'
#!/bin/bash
set -e

echo "🚀 Nautilus Phase3 全新部署脚本"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 步骤1: 清理旧容器
echo -e "${GREEN}[1/7] 清理旧容器...${NC}"
docker stop nautilus-v7 clash 2>/dev/null || true
docker rm nautilus-v7 clash 2>/dev/null || true

# 步骤2: 创建部署目录
echo -e "${GREEN}[2/7] 创建部署目录...${NC}"
sudo mkdir -p /opt/nautilus
sudo chown ubuntu:ubuntu /opt/nautilus
cd /opt/nautilus

# 步骤3: 等待代码上传
echo -e "${YELLOW}[3/7] 等待代码上传...${NC}"
echo "请在本地执行以下命令上传代码："
echo "cd ~/Projects/nautilus-core/phase3/backend"
echo "rsync -avz --exclude='node_modules' --exclude='__pycache__' -e 'ssh -p 24860' . cloud:/opt/nautilus/"
echo ""
read -p "代码上传完成后按Enter继续..."

# 步骤4: 配置环境变量
echo -e "${GREEN}[4/7] 配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    echo "创建环境变量文件..."
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 16)
    CSRF_SECRET=$(openssl rand -hex 16)
    DB_PASSWORD=$(openssl rand -hex 16)

    cat > .env <<EOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://nautilus_user:${DB_PASSWORD}@postgres:5432/nautilus_production
REDIS_URL=redis://redis:6379/0
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}
CSRF_SECRET_KEY=${CSRF_SECRET}
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=YOUR_ETHEREUM_PRIVATE_KEY
ALLOWED_HOSTS=43.160.239.61,localhost
CORS_ORIGINS=http://43.160.239.61:3000
DB_PASSWORD=${DB_PASSWORD}
EOF
    echo "环境变量已生成"
else
    echo "环境变量文件已存在"
fi

# 步骤5: 创建Docker Compose配置
echo -e "${GREEN}[5/7] 创建Docker Compose配置...${NC}"
if [ ! -f "docker-compose.yml" ]; then
    echo "Docker Compose配置文件不存在，请确保已上传"
    exit 1
fi

# 步骤6: 启动服务
echo -e "${GREEN}[6/7] 启动服务...${NC}"
docker-compose up -d --build

echo "等待服务启动..."
sleep 15

# 步骤7: 验证部署
echo -e "${GREEN}[7/7] 验证部署...${NC}"
echo ""
echo "容器状态："
docker-compose ps

echo ""
echo "测试API健康检查..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API健康检查通过${NC}"
else
    echo -e "${RED}❌ API健康检查失败${NC}"
    echo "查看日志："
    docker-compose logs --tail=50 api
    exit 1
fi

echo ""
echo "================================"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "================================"
echo ""
echo "访问地址："
echo "  - API: http://43.160.239.61:8000"
echo "  - API文档: http://43.160.239.61:8000/docs"
echo "  - 健康检查: http://43.160.239.61:8000/health"
echo ""
echo "常用命令："
echo "  - 查看日志: docker-compose logs -f"
echo "  - 重启服务: docker-compose restart"
echo "  - 停止服务: docker-compose down"
echo ""
SCRIPT

chmod +x /tmp/deploy-nautilus-phase3.sh
```

---

## 🎯 执行部署

### 在本地执行：

```bash
# 1. 上传部署脚本
scp -P 24860 /tmp/deploy-nautilus-phase3.sh cloud:/tmp/

# 2. 上传代码
cd ~/Projects/nautilus-core/phase3/backend
rsync -avz --exclude='node_modules' --exclude='__pycache__' --exclude='.git' \
  -e "ssh -p 24860" \
  . cloud:/opt/nautilus/

# 3. 执行部署
ssh cloud -p 24860 "bash /tmp/deploy-nautilus-phase3.sh"
```

---

## ✅ 部署后检查

```bash
# 检查所有容器
docker ps

# 查看API日志
docker logs nautilus-api

# 查看数据库日志
docker logs nautilus-postgres

# 测试API
curl http://43.160.239.61:8000/health
curl http://43.160.239.61:8000/docs
```

---

## 🔧 故障排查

### API无法启动

```bash
# 查看详细日志
docker logs nautilus-api

# 检查环境变量
docker exec nautilus-api env | grep -E "DATABASE|REDIS|SECRET"

# 重启API
docker-compose restart api
```

### 数据库连接失败

```bash
# 检查数据库状态
docker logs nautilus-postgres

# 测试数据库连接
docker exec nautilus-postgres psql -U nautilus_user -d nautilus_production -c "SELECT 1;"
```

---

**准备好开始全新部署了吗？** 🚀

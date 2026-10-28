# 🚀 Nautilus阿里云部署指南

**目标服务器**: 阿里云 Ubuntu 20.04/22.04
**Docker状态**: 已安装
**部署内容**: 全套服务（后端+数据库+前端+监控）

---

## 📋 部署前准备

### 1. 服务器要求

**最低配置**：
- CPU: 2核
- 内存: 4GB
- 磁盘: 40GB
- 带宽: 1Mbps

**推荐配置**：
- CPU: 4核
- 内存: 8GB
- 磁盘: 100GB
- 带宽: 5Mbps

### 2. 需要的信息

- [ ] 服务器IP地址
- [ ] SSH登录信息（用户名/密码或密钥）
- [ ] 域名（如果有）
- [ ] 数据库密码
- [ ] JWT密钥

---

## 🔧 步骤1：连接服务器

```bash
# SSH连接到服务器
ssh root@your-server-ip

# 或使用密钥
ssh -i your-key.pem root@your-server-ip
```

---

## 📦 步骤2：安装必要软件

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y git curl wget vim

# 验证Docker
docker --version
docker-compose --version

# 如果没有docker-compose，安装它
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 📥 步骤3：克隆项目

```bash
# 创建项目目录
mkdir -p /opt/nautilus
cd /opt/nautilus

# 克隆项目
git clone https://github.com/chunxiaoxx/nautilus-core.git
cd nautilus-core/phase3/backend
```

---

## 🔐 步骤4：配置环境变量

```bash
# 复制环境变量模板
cp .env.production.template .env.production

# 编辑环境变量
vim .env.production
```

**必须修改的配置**：

```bash
# 数据库配置
DATABASE_URL=postgresql://nautilus_user:YOUR_STRONG_PASSWORD@postgres:5432/nautilus_production
REDIS_URL=redis://redis:6379/0

# 安全配置
SECRET_KEY=YOUR_RANDOM_SECRET_KEY_AT_LEAST_64_CHARS
JWT_SECRET=YOUR_JWT_SECRET_AT_LEAST_32_CHARS
CSRF_SECRET_KEY=YOUR_CSRF_SECRET_AT_LEAST_32_CHARS

# 区块链配置
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=YOUR_ETHEREUM_PRIVATE_KEY

# 应用配置
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=your-domain.com,your-server-ip
CORS_ORIGINS=https://your-domain.com
```

**生成随机密钥**：

```bash
# 生成SECRET_KEY（64字符）
openssl rand -hex 32

# 生成JWT_SECRET（32字符）
openssl rand -hex 16

# 生成CSRF_SECRET_KEY（32字符）
openssl rand -hex 16
```

---

## 🗄️ 步骤5：部署数据库

```bash
# 创建Docker网络
docker network create nautilus-network

# 启动PostgreSQL
docker run -d \
  --name nautilus-postgres \
  --network nautilus-network \
  -e POSTGRES_DB=nautilus_production \
  -e POSTGRES_USER=nautilus_user \
  -e POSTGRES_PASSWORD=YOUR_STRONG_PASSWORD \
  -v /opt/nautilus/data/postgres:/var/lib/postgresql/data \
  -p 5432:5432 \
  --restart unless-stopped \
  postgres:15

# 启动Redis
docker run -d \
  --name nautilus-redis \
  --network nautilus-network \
  -v /opt/nautilus/data/redis:/data \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7-alpine

# 验证数据库
docker ps | grep nautilus
```

---

## 🚀 步骤6：部署后端API

### 方法A：使用Docker Compose（推荐）

```bash
# 创建docker-compose.production.yml
cat > docker-compose.production.yml <<'EOF'
version: '3.8'

services:
  api:
    build: .
    container_name: nautilus-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    networks:
      - nautilus-network
    volumes:
      - ./logs:/app/logs

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
    networks:
      - nautilus-network

  redis:
    image: redis:7-alpine
    container_name: nautilus-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - nautilus-network

networks:
  nautilus-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
EOF

# 启动所有服务
docker-compose -f docker-compose.production.yml up -d

# 查看日志
docker-compose -f docker-compose.production.yml logs -f
```

### 方法B：单独构建

```bash
# 构建Docker镜像
docker build -t nautilus-api:latest .

# 运行容器
docker run -d \
  --name nautilus-api \
  --network nautilus-network \
  -p 8000:8000 \
  --env-file .env.production \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  nautilus-api:latest

# 查看日志
docker logs -f nautilus-api
```

---

## 🌐 步骤7：配置Nginx反向代理

```bash
# 安装Nginx
sudo apt install -y nginx

# 创建Nginx配置
sudo vim /etc/nginx/sites-available/nautilus
```

**Nginx配置内容**：

```nginx
# API服务器配置
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 前端网站配置
server {
    listen 80;
    server_name www.your-domain.com your-domain.com;

    root /opt/nautilus/nautilus-core/phase3/website/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/nautilus /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

---

## 🔒 步骤8：配置SSL证书

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d api.your-domain.com -d www.your-domain.com -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 🎨 步骤9：部署前端网站

```bash
# 进入网站目录
cd /opt/nautilus/nautilus-core/phase3/website

# 安装依赖
npm install

# 配置环境变量
cat > .env.production <<EOF
VITE_API_URL=https://api.your-domain.com
EOF

# 构建生产版本
npm run build

# 构建完成后，dist目录会被Nginx服务
```

---

## 📊 步骤10：部署监控系统

```bash
# 进入监控目录
cd /opt/nautilus/nautilus-core/phase3/backend/monitoring

# 启动监控服务
docker-compose up -d

# 访问监控面板
# Prometheus: http://your-server-ip:9090
# Grafana: http://your-server-ip:3001
```

---

## ✅ 步骤11：验证部署

```bash
# 1. 检查所有容器状态
docker ps

# 2. 测试API健康检查
curl http://localhost:8000/health

# 3. 测试数据库连接
docker exec -it nautilus-postgres psql -U nautilus_user -d nautilus_production -c "SELECT 1;"

# 4. 测试Redis连接
docker exec -it nautilus-redis redis-cli ping

# 5. 查看API日志
docker logs nautilus-api

# 6. 测试外部访问
curl https://api.your-domain.com/health
curl https://www.your-domain.com
```

---

## 🔥 步骤12：配置防火墙

```bash
# 安装UFW
sudo apt install -y ufw

# 配置防火墙规则
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

---

## 📝 步骤13：设置自动备份

```bash
# 创建备份脚本
sudo vim /opt/nautilus/backup.sh
```

**备份脚本内容**：

```bash
#!/bin/bash
BACKUP_DIR="/opt/nautilus/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec nautilus-postgres pg_dump -U nautilus_user nautilus_production > $BACKUP_DIR/db_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/db_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
```

```bash
# 添加执行权限
sudo chmod +x /opt/nautilus/backup.sh

# 添加到crontab（每天凌晨2点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/nautilus/backup.sh") | crontab -
```

---

## 🎯 常用命令

### 查看服务状态

```bash
# 查看所有容器
docker ps -a

# 查看容器日志
docker logs -f nautilus-api
docker logs -f nautilus-postgres
docker logs -f nautilus-redis

# 查看资源使用
docker stats
```

### 重启服务

```bash
# 重启API
docker restart nautilus-api

# 重启数据库
docker restart nautilus-postgres

# 重启Redis
docker restart nautilus-redis

# 重启Nginx
sudo systemctl restart nginx
```

### 更新代码

```bash
# 拉取最新代码
cd /opt/nautilus/nautilus-core
git pull origin master

# 重新构建并部署
cd phase3/backend
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --build
```

---

## 🐛 故障排查

### API无法访问

```bash
# 检查容器状态
docker ps | grep nautilus-api

# 查看日志
docker logs nautilus-api

# 检查端口
netstat -tlnp | grep 8000

# 测试本地访问
curl http://localhost:8000/health
```

### 数据库连接失败

```bash
# 检查数据库容器
docker ps | grep postgres

# 测试连接
docker exec -it nautilus-postgres psql -U nautilus_user -d nautilus_production

# 查看日志
docker logs nautilus-postgres
```

### 网站无法访问

```bash
# 检查Nginx状态
sudo systemctl status nginx

# 测试Nginx配置
sudo nginx -t

# 查看Nginx日志
sudo tail -f /var/log/nginx/error.log
```

---

## 📚 相关文档

- **PRODUCTION_DEPLOYMENT_STEPS.md** - 详细部署步骤
- **SERVER_REQUIREMENTS.md** - 服务器要求
- **DEPLOYMENT_CHECKLIST.md** - 部署检查清单

---

## 🎉 部署完成

部署完成后，你可以访问：

- **API文档**: https://api.your-domain.com/docs
- **网站**: https://www.your-domain.com
- **Prometheus**: http://your-server-ip:9090
- **Grafana**: http://your-server-ip:3001

---

**祝部署顺利！** 🚀

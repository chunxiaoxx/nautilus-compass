# 🚀 Nautilus Phase 3 部署指南

## 📋 部署前准备

### 1. 服务器要求

**最低配置**:
- CPU: 2核
- 内存: 4GB
- 硬盘: 20GB
- 操作系统: Ubuntu 20.04+ / CentOS 7+

**推荐配置**:
- CPU: 4核
- 内存: 8GB
- 硬盘: 50GB
- 操作系统: Ubuntu 22.04

### 2. 必需软件

```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Nginx
sudo apt update
sudo apt install nginx -y

# Node.js (用于构建前端)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

---

## 🔧 快速部署

### 方法1: 使用部署脚本（推荐）

1. **配置环境变量**

```bash
# 在本地设置服务器信息
export REMOTE_USER="root"
export REMOTE_HOST="your-server.com"
export REMOTE_PATH="/opt/nautilus"
```

2. **运行部署脚本**

```bash
chmod +x deploy.sh
./deploy.sh
```

### 方法2: 手动部署

#### 步骤1: 准备代码

```bash
# 1. 拉取最新代码
git pull origin master

# 2. 构建前端
cd phase3/frontend
npm install
npm run build
cd ../..
```

#### 步骤2: 上传到服务器

```bash
# 使用rsync同步
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.git' \
    ./ root@your-server.com:/opt/nautilus/
```

#### 步骤3: 在服务器上部署

```bash
# SSH到服务器
ssh root@your-server.com

# 进入项目目录
cd /opt/nautilus

# 部署后端
cd phase3/backend
docker-compose -f docker-compose.prod.yml up -d --build

# 部署前端
cd ../frontend
mkdir -p /var/www/nautilus
cp -r dist/* /var/www/nautilus/
systemctl reload nginx
```

---

## 🌐 Nginx配置

创建 `/etc/nginx/sites-available/nautilus`:

```nginx
# 前端
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/nautilus;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}

# 后端API
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持 (Nexus Protocol)
    location /nexus {
        proxy_pass http://localhost:8000/nexus;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/nautilus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 SSL证书配置（可选但推荐）

使用Let's Encrypt免费SSL证书:

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 🔧 环境变量配置

在服务器上创建 `/opt/nautilus/phase3/backend/.env`:

```bash
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/nautilus
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 区块链
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/your-project-id
CONTRACT_ADDRESS=0x...
PRIVATE_KEY=0x...

# CORS
CORS_ORIGINS=https://your-domain.com

# 环境
ENVIRONMENT=production
LOG_LEVEL=warning

# Nexus Protocol
MAX_AGENTS=200
MAX_QUEUE_SIZE=2000

# 任务自动分配
TASK_AUTO_ASSIGN_ENABLED=true
TASK_AUTO_ASSIGN_INTERVAL=30

# 区块链事件监听
BLOCKCHAIN_EVENT_LISTENER_ENABLED=true
```

---

## 📊 监控和日志

### 查看服务状态

```bash
cd /opt/nautilus/phase3/backend
docker-compose -f docker-compose.prod.yml ps
```

### 查看日志

```bash
# 所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务日志
docker-compose -f docker-compose.prod.yml logs -f api

# 最近100行
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Prometheus监控

访问: `http://your-server:9090`

### Grafana仪表板

访问: `http://your-server:3000`
默认账号: admin/admin

---

## 🔄 更新部署

### 快速更新

```bash
# 本地
git pull origin master
./deploy.sh
```

### 手动更新

```bash
# 在服务器上
cd /opt/nautilus
git pull origin master

# 重新构建和启动
cd phase3/backend
docker-compose -f docker-compose.prod.yml up -d --build

# 更新前端
cd ../frontend
npm install
npm run build
cp -r dist/* /var/www/nautilus/
```

---

## 🐛 故障排查

### 后端无法启动

```bash
# 检查日志
docker-compose -f docker-compose.prod.yml logs api

# 检查端口占用
sudo netstat -tulpn | grep 8000

# 重启服务
docker-compose -f docker-compose.prod.yml restart
```

### 前端无法访问

```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查Nginx配置
sudo nginx -t

# 查看Nginx日志
sudo tail -f /var/log/nginx/error.log
```

### 数据库连接失败

```bash
# 检查PostgreSQL
docker-compose -f docker-compose.prod.yml logs postgres

# 检查连接
docker-compose -f docker-compose.prod.yml exec postgres psql -U nautilus -d nautilus
```

### WebSocket连接失败

```bash
# 检查Nexus服务
docker-compose -f docker-compose.prod.yml logs nexus-server

# 检查Nginx WebSocket配置
sudo nginx -T | grep -A 10 "location /nexus"
```

---

## 🔒 安全建议

1. **防火墙配置**

```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

2. **定期更新**

```bash
# 系统更新
sudo apt update && sudo apt upgrade -y

# Docker镜像更新
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

3. **备份数据库**

```bash
# 创建备份脚本
cat > /opt/nautilus/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f /opt/nautilus/phase3/backend/docker-compose.prod.yml exec -T postgres \
    pg_dump -U nautilus nautilus > /opt/nautilus/backups/nautilus_$DATE.sql
# 保留最近7天的备份
find /opt/nautilus/backups -name "nautilus_*.sql" -mtime +7 -delete
EOF

chmod +x /opt/nautilus/backup.sh

# 添加到crontab (每天凌晨2点备份)
echo "0 2 * * * /opt/nautilus/backup.sh" | crontab -
```

---

## 📈 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_publisher ON tasks(publisher_id);
CREATE INDEX idx_agents_owner ON agents(owner);
```

### 2. Redis缓存

确保Redis配置正确:

```bash
# 检查Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### 3. CDN加速（可选）

使用Cloudflare或其他CDN服务加速静态资源。

---

## ✅ 部署检查清单

部署完成后，检查以下项目:

- [ ] 前端可以访问
- [ ] 后端API可以访问
- [ ] API文档可以访问 (/docs)
- [ ] 用户可以注册和登录
- [ ] 可以创建任务
- [ ] 可以查看任务列表
- [ ] WebSocket通知正常工作
- [ ] 搜索功能正常
- [ ] 性能监控正常
- [ ] 日志记录正常
- [ ] SSL证书有效（如果配置）
- [ ] 数据库备份正常

---

## 📞 支持

如有问题，请查看:
- 项目文档: `/docs`
- 日志文件: `docker-compose logs`
- GitHub Issues: https://github.com/your-repo/nautilus-core/issues

---

**部署完成后，访问你的域名即可使用Nautilus系统！** 🎉

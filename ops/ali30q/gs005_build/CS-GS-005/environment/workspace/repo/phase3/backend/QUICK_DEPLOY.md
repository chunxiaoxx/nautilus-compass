# 🚀 Nautilus 快速部署指南

**一键部署到阿里云Ubuntu服务器**

---

## 📋 前置要求

- ✅ 阿里云Ubuntu 20.04/22.04服务器
- ✅ Docker已安装
- ✅ Root权限
- ✅ 至少4GB内存

---

## ⚡ 快速部署（5分钟）

### 1. 连接服务器

```bash
ssh root@your-server-ip
```

### 2. 下载部署脚本

```bash
# 方法A：直接下载
wget https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/phase3/backend/scripts/deploy_aliyun.sh

# 方法B：克隆项目
git clone https://github.com/chunxiaoxx/nautilus-core.git
cd nautilus-core/phase3/backend/scripts
```

### 3. 运行部署脚本

```bash
chmod +x deploy_aliyun.sh
sudo bash deploy_aliyun.sh
```

脚本会自动完成：
- ✅ 更新系统
- ✅ 安装必要软件
- ✅ 验证Docker
- ✅ 克隆项目
- ✅ 配置环境变量
- ✅ 部署数据库（PostgreSQL + Redis）
- ✅ 构建并部署API
- ✅ 验证部署

### 4. 配置环境变量

脚本会自动生成 `.env.production` 文件，但你需要手动配置：

```bash
cd /opt/nautilus/nautilus-core/phase3/backend
vim .env.production
```

**必须配置的项**：
```bash
# 区块链配置
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=YOUR_ETHEREUM_PRIVATE_KEY

# 域名配置
ALLOWED_HOSTS=your-domain.com,your-server-ip
CORS_ORIGINS=https://your-domain.com
```

配置完成后重启API：
```bash
docker restart nautilus-api
```

---

## 🌐 配置Nginx（可选但推荐）

### 1. 安装Nginx

```bash
sudo apt install -y nginx
```

### 2. 创建配置文件

```bash
sudo vim /etc/nginx/sites-available/nautilus
```

**配置内容**：

```nginx
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
```

### 3. 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/nautilus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 配置SSL

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.your-domain.com
```

---

## ✅ 验证部署

```bash
# 1. 检查容器状态
docker ps

# 2. 测试API
curl http://localhost:8000/health

# 3. 查看日志
docker logs nautilus-api

# 4. 测试外部访问
curl http://your-server-ip:8000/health
```

---

## 📊 部署监控系统（可选）

```bash
cd /opt/nautilus/nautilus-core/phase3/backend/monitoring
docker-compose up -d
```

访问：
- Prometheus: http://your-server-ip:9090
- Grafana: http://your-server-ip:3001

---

## 🎨 部署前端网站（可选）

```bash
# 1. 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 2. 构建网站
cd /opt/nautilus/nautilus-core/phase3/website
npm install
npm run build

# 3. 配置Nginx
sudo vim /etc/nginx/sites-available/nautilus
```

添加网站配置：

```nginx
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
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔧 常用命令

### 查看状态

```bash
# 查看所有容器
docker ps

# 查看API日志
docker logs -f nautilus-api

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
```

### 更新代码

```bash
cd /opt/nautilus/nautilus-core
git pull origin master
cd phase3/backend
docker stop nautilus-api
docker rm nautilus-api
docker build -t nautilus-api:latest .
docker run -d \
  --name nautilus-api \
  --network nautilus-network \
  -p 8000:8000 \
  --env-file .env.production \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  nautilus-api:latest
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

---

## 📚 详细文档

- **ALIYUN_DEPLOYMENT_GUIDE.md** - 完整部署指南
- **PRODUCTION_DEPLOYMENT_STEPS.md** - 详细部署步骤
- **SERVER_REQUIREMENTS.md** - 服务器要求

---

## 🎉 部署完成

部署完成后，你可以访问：

- **API**: http://your-server-ip:8000
- **API文档**: http://your-server-ip:8000/docs
- **健康检查**: http://your-server-ip:8000/health

---

**祝部署顺利！** 🚀

如有问题，请查看详细文档或联系技术支持。

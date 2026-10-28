# Nautilus Phase 3 Backend - 生产环境部署指南

**版本**: 3.0.0
**日期**: 2026-02-26
**目标环境**: Production

---

## 📖 目录

1. [部署概述](#部署概述)
2. [系统要求](#系统要求)
3. [部署前准备](#部署前准备)
4. [详细部署步骤](#详细部署步骤)
5. [环境配置说明](#环境配置说明)
6. [常见问题解决](#常见问题解决)
7. [监控配置](#监控配置)
8. [维护和运维](#维护和运维)

---

## 部署概述

### 架构说明

Nautilus Phase 3 Backend 是一个基于 FastAPI 的分布式 AI Agent 协作平台，集成了区块链技术用于任务管理和奖励分配。

**核心组件**：
- FastAPI Web 服务器
- PostgreSQL 数据库
- Redis 缓存
- 区块链集成（Ethereum/Sepolia）
- WebSocket 实时通信
- Prometheus 监控

**部署架构**：
```
Internet
    ↓
[Nginx反向代理] (443/80)
    ↓
[FastAPI应用] (8000)
    ↓
[PostgreSQL] (5432) + [Redis] (6379)
    ↓
[区块链网络] (Infura/Alchemy)
```

### 部署策略

- **蓝绿部署**: 推荐用于零停机部署
- **滚动更新**: 适用于多实例环境
- **金丝雀发布**: 适用于重大更新

---

## 系统要求

### 硬件要求

**最小配置**：
- CPU: 2核心
- 内存: 4GB RAM
- 磁盘: 50GB SSD
- 网络: 100Mbps

**推荐配置**：
- CPU: 4核心或更多
- 内存: 8GB RAM 或更多
- 磁盘: 100GB SSD
- 网络: 1Gbps

### 软件要求

**操作系统**：
- Ubuntu 20.04 LTS 或更高版本
- CentOS 8 或更高版本
- Debian 11 或更高版本

**必需软件**：
- Python 3.8+
- PostgreSQL 12+
- Redis 6.0+
- Nginx 1.18+
- Git 2.25+

**可选软件**：
- Docker 20.10+ (容器化部署)
- Prometheus (监控)
- Grafana (可视化)

---

## 部署前准备

### 1. 服务器准备

#### 1.1 创建部署用户
```bash
# 创建nautilus用户
sudo useradd -m -s /bin/bash nautilus

# 设置密码
sudo passwd nautilus

# 添加sudo权限（可选）
sudo usermod -aG sudo nautilus

# 切换到nautilus用户
su - nautilus
```

#### 1.2 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
  postgresql postgresql-contrib redis-server nginx \
  git curl wget build-essential libpq-dev

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-devel \
  postgresql-server postgresql-contrib redis nginx \
  git curl wget gcc postgresql-devel
```

#### 1.3 配置系统参数
```bash
# 提高文件描述符限制
sudo tee -a /etc/security/limits.conf <<EOF
nautilus soft nofile 65535
nautilus hard nofile 65535
EOF

# 优化网络参数
sudo tee -a /etc/sysctl.conf <<EOF
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.ip_local_port_range = 10000 65000
EOF

sudo sysctl -p
```

### 2. 数据库准备

#### 2.1 安装和配置PostgreSQL
```bash
# 初始化数据库（CentOS）
sudo postgresql-setup --initdb

# 启动PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql <<EOF
CREATE DATABASE nautilus_production;
CREATE USER nautilus_user WITH ENCRYPTED PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE nautilus_production TO nautilus_user;
\q
EOF
```

#### 2.2 配置PostgreSQL访问
```bash
# 编辑 pg_hba.conf
sudo nano /etc/postgresql/12/main/pg_hba.conf

# 添加以下行（允许本地密码认证）
# local   all             nautilus_user                           md5
# host    all             nautilus_user   127.0.0.1/32            md5

# 重启PostgreSQL
sudo systemctl restart postgresql
```

#### 2.3 优化PostgreSQL性能
```bash
# 编辑 postgresql.conf
sudo nano /etc/postgresql/12/main/postgresql.conf

# 推荐配置（根据服务器资源调整）
# shared_buffers = 2GB
# effective_cache_size = 6GB
# maintenance_work_mem = 512MB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB
# default_statistics_target = 100
# random_page_cost = 1.1
# effective_io_concurrency = 200
# work_mem = 10MB
# min_wal_size = 1GB
# max_wal_size = 4GB
# max_connections = 200

# 重启PostgreSQL
sudo systemctl restart postgresql
```

### 3. Redis准备

#### 3.1 安装和配置Redis
```bash
# 启动Redis
sudo systemctl start redis
sudo systemctl enable redis

# 配置Redis密码
sudo nano /etc/redis/redis.conf

# 设置密码
# requirepass your_redis_password

# 设置最大内存
# maxmemory 2gb
# maxmemory-policy allkeys-lru

# 启用持久化
# appendonly yes
# appendfsync everysec

# 重启Redis
sudo systemctl restart redis
```

#### 3.2 测试Redis连接
```bash
redis-cli
AUTH your_redis_password
PING
# 应返回 PONG
```

### 4. 获取代码

#### 4.1 克隆仓库
```bash
# 切换到nautilus用户
su - nautilus

# 克隆代码
cd ~
git clone https://github.com/your-org/nautilus-core.git
cd nautilus-core/phase3/backend

# 检出生产分支
git checkout main
```

#### 4.2 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

#### 4.3 安装依赖
```bash
# 安装Python依赖
pip install -r requirements.txt

# 验证安装
pip list | grep -E "fastapi|uvicorn|sqlalchemy|web3"
```

---

## 详细部署步骤

### 步骤1: 环境配置

#### 1.1 创建生产环境配置
```bash
# 复制配置模板
cp .env.production.example .env.production

# 编辑配置文件
nano .env.production
```

#### 1.2 生成密钥
```bash
# 生成JWT密钥
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# 生成CSRF密钥
python3 -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(32))"

# 将生成的密钥添加到 .env.production
```

#### 1.3 配置关键参数
```bash
# 必须修改的配置项
ENVIRONMENT=production
DEBUG=false
FORCE_HTTPS=true

# 数据库配置
DATABASE_URL=postgresql://nautilus_user:your_password@localhost:5432/nautilus_production

# Redis配置
REDIS_URL=redis://:your_redis_password@localhost:6379/0

# CORS配置
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 区块链配置
BLOCKCHAIN_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
INFURA_PROJECT_ID=YOUR_PROJECT_ID
```

#### 1.4 配置私钥管理
```bash
# 选择方式1: 加密文件存储（推荐）
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=/home/nautilus/keys/encrypted_key.json
KEY_ENCRYPTION_PASSWORD=your_encryption_password

# 创建密钥目录
mkdir -p /home/nautilus/keys
chmod 700 /home/nautilus/keys

# 运行密钥设置脚本
python3 setup_key_management.py
```

#### 1.5 设置文件权限
```bash
# 保护配置文件
chmod 600 .env.production

# 保护密钥文件
chmod 600 /home/nautilus/keys/*
```

### 步骤2: 数据库初始化

#### 2.1 运行数据库迁移
```bash
# 设置环境变量
export ENVIRONMENT=production
source .env.production

# 检查数据库连接
python3 -c "from utils.database import engine; print(engine.url)"

# 运行迁移
alembic upgrade head

# 验证表创建
psql "$DATABASE_URL" -c "\dt"
```

#### 2.2 创建初始数据（可选）
```bash
# 创建管理员账户
python3 -c "
from utils.database import SessionLocal
from models.database import User
from utils.auth import hash_password

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@yourdomain.com',
    password_hash=hash_password('your_admin_password'),
    is_admin=True
)
db.add(admin)
db.commit()
print('Admin user created')
"
```

### 步骤3: SSL证书配置

#### 3.1 使用Let's Encrypt获取证书
```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 验证证书
sudo certbot certificates
```

#### 3.2 配置自动续期
```bash
# 测试续期
sudo certbot renew --dry-run

# 设置自动续期（cron已自动配置）
sudo systemctl status certbot.timer
```

### 步骤4: Nginx配置

#### 4.1 创建Nginx配置
```bash
sudo nano /etc/nginx/sites-available/nautilus
```

添加以下配置：
```nginx
# HTTP重定向到HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS配置
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL证书
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # 安全头部
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 日志
    access_log /var/log/nginx/nautilus_access.log;
    error_log /var/log/nginx/nautilus_error.log;

    # 客户端最大请求体大小
    client_max_body_size 10M;

    # API代理
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket超时
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # 健康检查（不记录日志）
    location /health {
        proxy_pass http://localhost:8000;
        access_log off;
    }

    # 禁止访问敏感文件
    location ~ /\. {
        deny all;
    }
}
```

#### 4.2 启用配置
```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/nautilus /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 步骤5: 配置Systemd服务

#### 5.1 创建服务文件
```bash
sudo nano /etc/systemd/system/nautilus-backend.service
```

添加以下内容：
```ini
[Unit]
Description=Nautilus Phase 3 Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=nautilus
Group=nautilus
WorkingDirectory=/home/nautilus/nautilus-core/phase3/backend
Environment="PATH=/home/nautilus/nautilus-core/phase3/backend/venv/bin"
Environment="ENVIRONMENT=production"
EnvironmentFile=/home/nautilus/nautilus-core/phase3/backend/.env.production

ExecStart=/home/nautilus/nautilus-core/phase3/backend/venv/bin/uvicorn main:socket_app_with_fastapi \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

Restart=always
RestartSec=10
StandardOutput=append:/var/log/nautilus/app.log
StandardError=append:/var/log/nautilus/error.log

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/nautilus/nautilus-core/phase3/backend/logs
ReadWritePaths=/var/log/nautilus

[Install]
WantedBy=multi-user.target
```

#### 5.2 创建日志目录
```bash
sudo mkdir -p /var/log/nautilus
sudo chown nautilus:nautilus /var/log/nautilus
```

#### 5.3 启用和启动服务
```bash
# 重载systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable nautilus-backend

# 启动服务
sudo systemctl start nautilus-backend

# 检查状态
sudo systemctl status nautilus-backend
```

### 步骤6: 配置日志轮转

#### 6.1 创建logrotate配置
```bash
sudo nano /etc/logrotate.d/nautilus
```

添加以下内容：
```
/var/log/nautilus/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nautilus nautilus
    sharedscripts
    postrotate
        systemctl reload nautilus-backend > /dev/null 2>&1 || true
    endscript
}
```

#### 6.2 测试logrotate
```bash
sudo logrotate -d /etc/logrotate.d/nautilus
```

### 步骤7: 部署验证

#### 7.1 健康检查
```bash
# 检查服务状态
curl https://yourdomain.com/health

# 预期输出
{
  "status": "healthy",
  "version": "3.0.0",
  "environment": "production",
  "database": "healthy",
  "redis": "healthy",
  "blockchain": "healthy"
}
```

#### 7.2 功能测试
```bash
# 测试根端点
curl https://yourdomain.com/

# 测试API端点
curl https://yourdomain.com/api/agents

# 测试认证
curl -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

#### 7.3 性能测试
```bash
# 安装ab工具
sudo apt install apache2-utils

# 简单压力测试
ab -n 1000 -c 10 https://yourdomain.com/health
```

---

## 环境配置说明

### 核心配置项

#### 数据库配置
```bash
# PostgreSQL连接
DATABASE_URL=postgresql://user:password@host:port/database

# 连接池配置
DB_POOL_SIZE=20              # 连接池大小
DB_MAX_OVERFLOW=40           # 最大溢出连接
DB_POOL_TIMEOUT=30           # 连接超时（秒）
DB_POOL_RECYCLE=3600         # 连接回收时间（秒）
```

#### Redis配置
```bash
# Redis连接
REDIS_URL=redis://:password@host:port/db

# Redis详细配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
```

#### 安全配置
```bash
# JWT配置
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# CSRF配置
CSRF_SECRET_KEY=your_csrf_key

# CORS配置
ALLOWED_ORIGINS=https://domain1.com,https://domain2.com

# HTTPS配置
FORCE_HTTPS=true
HSTS_MAX_AGE=31536000
```

#### 区块链配置
```bash
# 网络配置
BLOCKCHAIN_NETWORK=mainnet
BLOCKCHAIN_RPC_URL=https://mainnet.infura.io/v3/PROJECT_ID

# 合约地址
IDENTITY_CONTRACT_ADDRESS=0x...
TASK_CONTRACT_ADDRESS=0x...
REWARD_CONTRACT_ADDRESS=0x...

# Gas配置
MAX_GAS_PRICE=100000000000
GAS_LIMIT=500000
```

---

## 常见问题解决

### 问题1: 服务无法启动

**症状**: systemctl start 失败

**排查步骤**:
```bash
# 查看服务状态
sudo systemctl status nautilus-backend

# 查看日志
sudo journalctl -u nautilus-backend -n 50

# 检查配置文件
python3 -c "from main import app; print('OK')"
```

**常见原因**:
- 环境变量未正确加载
- 数据库连接失败
- 端口被占用
- 权限问题

### 问题2: 数据库连接失败

**症状**: 健康检查显示数据库不健康

**排查步骤**:
```bash
# 测试数据库连接
psql "$DATABASE_URL" -c "SELECT 1;"

# 检查PostgreSQL状态
sudo systemctl status postgresql

# 查看PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-12-main.log
```

**解决方案**:
- 检查DATABASE_URL格式
- 验证数据库用户权限
- 检查pg_hba.conf配置
- 确认PostgreSQL正在运行

### 问题3: Redis连接失败

**症状**: 速率限制不工作或缓存失效

**排查步骤**:
```bash
# 测试Redis连接
redis-cli -u "$REDIS_URL" ping

# 检查Redis状态
sudo systemctl status redis

# 查看Redis日志
sudo tail -f /var/log/redis/redis-server.log
```

**解决方案**:
- 检查REDIS_URL格式
- 验证Redis密码
- 确认Redis正在运行
- 检查防火墙规则

### 问题4: SSL证书问题

**症状**: HTTPS访问失败或证书警告

**排查步骤**:
```bash
# 检查证书
sudo certbot certificates

# 测试SSL配置
openssl s_client -connect yourdomain.com:443

# 检查Nginx配置
sudo nginx -t
```

**解决方案**:
- 续期过期证书: `sudo certbot renew`
- 检查证书路径
- 验证域名DNS解析
- 重启Nginx

### 问题5: 性能问题

**症状**: 响应慢或超时

**排查步骤**:
```bash
# 检查系统资源
top
free -h
df -h

# 检查数据库性能
psql "$DATABASE_URL" -c "SELECT * FROM pg_stat_activity;"

# 检查慢查询
tail -f /var/log/nautilus/app.log | grep "slow"
```

**解决方案**:
- 增加Worker数量
- 优化数据库查询
- 增加连接池大小
- 启用缓存
- 升级服务器配置

---

## 监控配置

### Prometheus配置

#### 1. 安装Prometheus
```bash
# 下载Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# 创建配置文件
nano prometheus.yml
```

#### 2. 配置Prometheus
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nautilus-backend'
    static_configs:
      - targets: ['localhost:9090']
```

#### 3. 启动Prometheus
```bash
./prometheus --config.file=prometheus.yml
```

### Grafana配置

#### 1. 安装Grafana
```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
```

#### 2. 启动Grafana
```bash
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

#### 3. 访问Grafana
- URL: http://localhost:3001
- 默认用户名/密码: admin/admin

---

## 维护和运维

### 日常维护

#### 查看日志
```bash
# 应用日志
tail -f /var/log/nautilus/app.log

# 错误日志
tail -f /var/log/nautilus/error.log

# Systemd日志
sudo journalctl -u nautilus-backend -f
```

#### 重启服务
```bash
sudo systemctl restart nautilus-backend
```

#### 更新代码
```bash
cd /home/nautilus/nautilus-core/phase3/backend
git pull origin main
pip install -r requirements.txt
sudo systemctl restart nautilus-backend
```

### 备份策略

#### 数据库备份
```bash
# 手动备份
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d).sql

# 自动备份（cron）
0 2 * * * pg_dump "$DATABASE_URL" > /backups/nautilus_$(date +\%Y\%m\%d).sql
```

#### 配置备份
```bash
# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env.production keys/
```

---

**文档版本**: 1.0
**最后更新**: 2026-02-26

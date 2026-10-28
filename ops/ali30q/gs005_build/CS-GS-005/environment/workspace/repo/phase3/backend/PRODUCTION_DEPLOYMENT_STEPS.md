# Nautilus Phase 3 Backend - 生产部署步骤

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-02-27
- **最后更新**: 2026-02-27
- **状态**: 生产就绪

---

## 目录
1. [部署前准备](#1-部署前准备)
2. [服务器环境配置](#2-服务器环境配置)
3. [数据库部署](#3-数据库部署)
4. [应用部署](#4-应用部署)
5. [部署验证](#5-部署验证)
6. [回滚流程](#6-回滚流程)
7. [故障排查](#7-故障排查)
8. [常见问题](#8-常见问题)

---

## 1. 部署前准备

### 1.1 检查清单

在开始部署前，请确认以下事项：

- [ ] 已阅读并理解 `PRODUCTION_DEPLOYMENT_PLAN.md`
- [ ] 已准备好所有服务器（参考 `SERVER_REQUIREMENTS.md`）
- [ ] 已获取所有必需的访问权限
- [ ] 已准备好所有密钥和证书
- [ ] 已通知相关团队和用户
- [ ] 已准备好回滚方案
- [ ] 团队成员已就位

### 1.2 准备配置文件

```bash
# 1. 复制环境变量模板
cd /opt/nautilus/backend
cp .env.production.template .env.production

# 2. 编辑配置文件
vim .env.production

# 3. 生成随机密钥
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(64))"

# 4. 验证配置文件
./scripts/deploy/validate_config.sh .env.production
```

### 1.3 准备SSL证书

```bash
# 方式1: 使用Let's Encrypt
sudo certbot certonly --standalone -d api.yourdomain.com

# 方式2: 使用商业证书
sudo mkdir -p /etc/ssl/certs /etc/ssl/private
sudo cp yourdomain.crt /etc/ssl/certs/
sudo cp yourdomain.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/yourdomain.key
```

### 1.4 准备Docker镜像

```bash
# 1. 登录Docker Registry
docker login registry.yourdomain.com

# 2. 构建镜像
cd /opt/nautilus/backend
docker build -t nexus-server:1.0.0 .

# 3. 推送镜像
docker tag nexus-server:1.0.0 registry.yourdomain.com/nexus-server:1.0.0
docker push registry.yourdomain.com/nexus-server:1.0.0
```

---

## 2. 服务器环境配置

### 2.1 系统初始化

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 设置主机名
sudo hostnamectl set-hostname nautilus-prod-01

# 3. 配置时区
sudo timedatectl set-timezone Asia/Shanghai

# 4. 同步时间
sudo apt install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp
```

### 2.2 安装Docker

```bash
# 1. 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. 启动Docker
sudo systemctl enable docker
sudo systemctl start docker

# 3. 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 验证安装
docker --version
docker-compose --version
```

### 2.3 创建应用用户

```bash
# 1. 创建nautilus用户
sudo useradd -m -s /bin/bash nautilus
sudo usermod -aG docker nautilus

# 2. 创建应用目录
sudo mkdir -p /opt/nautilus/backend
sudo mkdir -p /var/log/nautilus
sudo mkdir -p /var/backups/nautilus

# 3. 设置权限
sudo chown -R nautilus:nautilus /opt/nautilus
sudo chown -R nautilus:nautilus /var/log/nautilus
sudo chown -R nautilus:nautilus /var/backups/nautilus
```

### 2.4 配置防火墙

```bash
# 1. 启用UFW
sudo ufw enable

# 2. 允许SSH（修改为实际管理IP）
sudo ufw allow from 192.168.1.0/24 to any port 22

# 3. 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 4. 允许内网访问
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw allow from 10.0.0.0/8 to any port 8001

# 5. 查看规则
sudo ufw status numbered
```

### 2.5 系统优化

```bash
# 1. 编辑系统参数
sudo vim /etc/sysctl.conf

# 添加以下内容：
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 10000 65535
fs.file-max = 2097152

# 2. 应用配置
sudo sysctl -p

# 3. 配置文件描述符限制
sudo vim /etc/security/limits.conf

# 添加以下内容：
nautilus soft nofile 65535
nautilus hard nofile 65535
nautilus soft nproc 65535
nautilus hard nproc 65535
```

---

## 3. 数据库部署

### 3.1 安装PostgreSQL

```bash
# 1. 添加PostgreSQL仓库
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# 2. 安装PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-contrib-16

# 3. 启动服务
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 4. 验证安装
sudo -u postgres psql --version
```

### 3.2 配置PostgreSQL

```bash
# 1. 切换到postgres用户
sudo -u postgres psql

# 2. 创建数据库和用户
CREATE USER nautilus_user WITH PASSWORD 'your_strong_password';
CREATE DATABASE nautilus_production OWNER nautilus_user;
GRANT ALL PRIVILEGES ON DATABASE nautilus_production TO nautilus_user;

# 3. 启用扩展
\c nautilus_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

# 4. 退出
\q
```

### 3.3 优化PostgreSQL配置

```bash
# 1. 编辑配置文件
sudo vim /etc/postgresql/16/main/postgresql.conf

# 修改以下参数（根据服务器配置调整）：
max_connections = 200
shared_buffers = 8GB                    # 25% of RAM
effective_cache_size = 24GB             # 75% of RAM
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 20MB
min_wal_size = 1GB
max_wal_size = 4GB

# 2. 配置连接
sudo vim /etc/postgresql/16/main/pg_hba.conf

# 添加以下内容（允许内网访问）：
host    nautilus_production    nautilus_user    10.0.0.0/8    md5

# 3. 重启PostgreSQL
sudo systemctl restart postgresql
```

### 3.4 配置数据库备份

```bash
# 1. 创建备份脚本
sudo vim /opt/nautilus/scripts/backup/backup_database.sh

# 脚本内容：
#!/bin/bash
BACKUP_DIR="/var/backups/nautilus/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/nautilus_${TIMESTAMP}.sql"

mkdir -p "${BACKUP_DIR}"
pg_dump -h localhost -U nautilus_user nautilus_production | gzip > "${BACKUP_FILE}.gz"
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +30 -delete

# 2. 设置权限
sudo chmod +x /opt/nautilus/scripts/backup/backup_database.sh

# 3. 配置定时任务
sudo crontab -e -u nautilus

# 添加以下内容（每天凌晨2点备份）：
0 2 * * * /opt/nautilus/scripts/backup/backup_database.sh
```

### 3.5 安装和配置Redis

```bash
# 1. 安装Redis
sudo apt install -y redis-server

# 2. 配置Redis
sudo vim /etc/redis/redis.conf

# 修改以下参数：
bind 127.0.0.1 10.0.0.10              # 绑定内网IP
requirepass your_redis_password        # 设置密码
maxmemory 8gb                          # 最大内存
maxmemory-policy allkeys-lru           # 内存淘汰策略
save 900 1                             # 持久化配置
save 300 10
save 60 10000

# 3. 重启Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# 4. 测试连接
redis-cli -a your_redis_password ping
```

---

## 4. 应用部署

### 4.1 部署应用代码

```bash
# 1. 切换到nautilus用户
sudo su - nautilus

# 2. 克隆代码（或上传代码）
cd /opt/nautilus
git clone https://github.com/yourusername/nautilus-backend.git backend
cd backend

# 3. 切换到指定版本
git checkout v1.0.0

# 4. 复制配置文件
cp .env.production.template .env.production
vim .env.production  # 编辑配置
```

### 4.2 执行数据库迁移

```bash
# 1. 安装Python依赖（如果需要）
pip3 install alembic psycopg2-binary

# 2. 检查迁移状态
alembic current

# 3. 执行迁移
alembic upgrade head

# 4. 验证迁移
psql -h localhost -U nautilus_user -d nautilus_production -c "\dt"
```

### 4.3 使用部署脚本部署

```bash
# 1. 赋予执行权限
chmod +x scripts/deploy/deploy_production.sh
chmod +x scripts/deploy/check_deployment.sh

# 2. 执行部署（模拟运行）
./scripts/deploy/deploy_production.sh --dry-run --version 1.0.0

# 3. 执行实际部署
./scripts/deploy/deploy_production.sh --version 1.0.0

# 部署过程会自动执行：
# - 环境检查
# - 系统资源检查
# - 网络连接检查
# - 备份当前部署
# - 拉取/构建Docker镜像
# - 启动服务
# - 健康检查
```

### 4.4 手动部署（如果不使用脚本）

```bash
# 1. 构建Docker镜像
docker build -t nexus-server:1.0.0 .

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 4. 检查容器状态
docker-compose -f docker-compose.prod.yml ps
```

---

## 5. 部署验证

### 5.1 使用检查脚本

```bash
# 1. 执行部署检查
./scripts/deploy/check_deployment.sh

# 2. 详细检查
./scripts/deploy/check_deployment.sh --verbose

# 3. JSON格式输出
./scripts/deploy/check_deployment.sh --json

# 4. 检查远程服务器
./scripts/deploy/check_deployment.sh --host production.yourdomain.com --port 8001
```

### 5.2 手动验证步骤

#### 5.2.1 检查服务状态

```bash
# 1. 检查Docker容器
docker ps | grep nexus-server

# 2. 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' nexus-server-prod

# 3. 查看容器日志
docker logs --tail 100 nexus-server-prod
```

#### 5.2.2 检查API端点

```bash
# 1. 健康检查
curl -s http://localhost:8001/health | jq '.'

# 预期输出：
{
  "status": "healthy",
  "timestamp": "2026-02-27T10:00:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "blockchain": "ok"
  }
}

# 2. 状态检查
curl -s http://localhost:8001/api/v1/status | jq '.'

# 3. 测试API响应时间
time curl -s http://localhost:8001/health > /dev/null
```

#### 5.2.3 检查数据库连接

```bash
# 1. 测试数据库连接
psql -h localhost -U nautilus_user -d nautilus_production -c "SELECT version();"

# 2. 检查数据库表
psql -h localhost -U nautilus_user -d nautilus_production -c "\dt"

# 3. 检查数据库连接数
psql -h localhost -U nautilus_user -d nautilus_production -c "SELECT count(*) FROM pg_stat_activity;"
```

#### 5.2.4 检查Redis连接

```bash
# 1. 测试Redis连接
redis-cli -a your_redis_password ping

# 2. 检查Redis信息
redis-cli -a your_redis_password info

# 3. 检查Redis内存使用
redis-cli -a your_redis_password info memory
```

#### 5.2.5 检查区块链连接

```bash
# 1. 测试RPC连接
curl -X POST http://localhost:8001/api/v1/blockchain/test-connection

# 2. 获取当前区块号
curl -X POST http://localhost:8001/api/v1/blockchain/block-number
```

### 5.3 性能测试

```bash
# 1. 安装ab（Apache Bench）
sudo apt install -y apache2-utils

# 2. 简单压力测试
ab -n 1000 -c 10 http://localhost:8001/health

# 3. 使用wrk进行压力测试
sudo apt install -y wrk
wrk -t4 -c100 -d30s http://localhost:8001/health
```

### 5.4 监控检查

```bash
# 1. 检查Prometheus指标
curl -s http://localhost:9090/metrics | grep nautilus

# 2. 访问Grafana（如果已配置）
# 浏览器访问: http://monitoring.yourdomain.com:3000
```

---

## 6. 回滚流程

### 6.1 快速回滚（应用层）

```bash
# 1. 使用部署脚本回滚
./scripts/deploy/deploy_production.sh --rollback

# 2. 手动回滚
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.old.yml up -d

# 3. 验证回滚
./scripts/deploy/check_deployment.sh
```

### 6.2 数据库回滚

```bash
# 1. 停止应用
docker-compose -f docker-compose.prod.yml down

# 2. 备份当前数据库
pg_dump -h localhost -U nautilus_user nautilus_production > /var/backups/nautilus/rollback_$(date +%Y%m%d_%H%M%S).sql

# 3. 恢复到之前的备份
gunzip -c /var/backups/nautilus/database/nautilus_20260227_020000.sql.gz | \
    psql -h localhost -U nautilus_user nautilus_production

# 4. 验证数据
psql -h localhost -U nautilus_user -d nautilus_production -c "SELECT COUNT(*) FROM users;"

# 5. 重启应用
docker-compose -f docker-compose.prod.yml up -d
```

### 6.3 完整回滚流程

```bash
# 1. 通知团队
echo "开始回滚操作" | mail -s "紧急：生产环境回滚" ops@yourdomain.com

# 2. 获取最新备份路径
BACKUP_PATH=$(cat /var/backups/nautilus/latest_backup.txt)

# 3. 停止服务
docker-compose -f docker-compose.prod.yml down

# 4. 恢复配置文件
cp ${BACKUP_PATH}/.env.production /opt/nautilus/backend/

# 5. 恢复数据库
gunzip -c ${BACKUP_PATH}/database_backup.sql.gz | \
    psql -h localhost -U nautilus_user nautilus_production

# 6. 启动旧版本
docker-compose -f docker-compose.prod.old.yml up -d

# 7. 验证服务
./scripts/deploy/check_deployment.sh

# 8. 通知完成
echo "回滚完成" | mail -s "生产环境回滚完成" ops@yourdomain.com
```

---

## 7. 故障排查

### 7.1 服务无法启动

#### 问题：Docker容器无法启动

```bash
# 1. 查看容器日志
docker logs nexus-server-prod

# 2. 检查配置文件
cat /opt/nautilus/backend/.env.production

# 3. 检查端口占用
netstat -tuln | grep 8001

# 4. 检查磁盘空间
df -h

# 5. 检查内存
free -h
```

#### 问题：数据库连接失败

```bash
# 1. 检查PostgreSQL状态
sudo systemctl status postgresql

# 2. 检查PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# 3. 测试数据库连接
psql -h localhost -U nautilus_user -d nautilus_production

# 4. 检查防火墙
sudo ufw status

# 5. 检查pg_hba.conf配置
sudo cat /etc/postgresql/16/main/pg_hba.conf
```

#### 问题：Redis连接失败

```bash
# 1. 检查Redis状态
sudo systemctl status redis-server

# 2. 检查Redis日志
sudo tail -f /var/log/redis/redis-server.log

# 3. 测试Redis连接
redis-cli -a your_redis_password ping

# 4. 检查Redis配置
sudo cat /etc/redis/redis.conf | grep -E "bind|requirepass"
```

### 7.2 性能问题

#### 问题：响应时间过长

```bash
# 1. 检查系统负载
top
htop

# 2. 检查数据库性能
psql -h localhost -U nautilus_user -d nautilus_production -c "SELECT * FROM pg_stat_activity;"

# 3. 检查慢查询
psql -h localhost -U nautilus_user -d nautilus_production -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 4. 检查Redis性能
redis-cli -a your_redis_password --latency

# 5. 检查网络延迟
ping -c 10 blockchain-rpc-server
```

#### 问题：内存使用过高

```bash
# 1. 检查容器内存使用
docker stats nexus-server-prod

# 2. 检查系统内存
free -h

# 3. 检查进程内存
ps aux --sort=-%mem | head -10

# 4. 重启服务（如果必要）
docker-compose -f docker-compose.prod.yml restart
```

### 7.3 区块链连接问题

#### 问题：无法连接到区块链RPC

```bash
# 1. 测试RPC连接
curl -X POST ${BLOCKCHAIN_RPC_URL} \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 2. 检查网络连接
ping mainnet.infura.io

# 3. 检查DNS解析
nslookup mainnet.infura.io

# 4. 尝试备用RPC
# 编辑 .env.production，更换BLOCKCHAIN_RPC_URL

# 5. 检查API密钥
echo $INFURA_PROJECT_ID
```

### 7.4 SSL证书问题

#### 问题：SSL证书过期或无效

```bash
# 1. 检查证书有效期
openssl x509 -in /etc/ssl/certs/yourdomain.crt -noout -dates

# 2. 检查证书详情
openssl x509 -in /etc/ssl/certs/yourdomain.crt -noout -text

# 3. 更新Let's Encrypt证书
sudo certbot renew

# 4. 重启Nginx
sudo systemctl restart nginx

# 5. 验证HTTPS
curl -I https://api.yourdomain.com
```

---

## 8. 常见问题

### Q1: 部署后API返回502错误

**原因**: 应用未正常启动或健康检查失败

**解决方案**:
```bash
# 1. 检查容器状态
docker ps -a | grep nexus-server

# 2. 查看日志
docker logs nexus-server-prod

# 3. 检查健康检查
curl http://localhost:8001/health

# 4. 重启服务
docker-compose -f docker-compose.prod.yml restart
```

### Q2: 数据库迁移失败

**原因**: 数据库版本不匹配或权限问题

**解决方案**:
```bash
# 1. 检查当前迁移版本
alembic current

# 2. 查看迁移历史
alembic history

# 3. 回滚到上一个版本
alembic downgrade -1

# 4. 重新执行迁移
alembic upgrade head
```

### Q3: Docker镜像拉取失败

**原因**: 网络问题或认证失败

**解决方案**:
```bash
# 1. 检查Docker登录状态
docker login registry.yourdomain.com

# 2. 手动拉取镜像
docker pull registry.yourdomain.com/nexus-server:1.0.0

# 3. 如果失败，本地构建
docker build -t nexus-server:1.0.0 .
```

### Q4: 内存不足导致服务崩溃

**原因**: 资源配置不足

**解决方案**:
```bash
# 1. 增加Docker内存限制
# 编辑 docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G

# 2. 优化数据库连接池
# 编辑 .env.production
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# 3. 重启服务
docker-compose -f docker-compose.prod.yml up -d
```

### Q5: 区块链同步延迟

**原因**: RPC节点响应慢或网络问题

**解决方案**:
```bash
# 1. 切换到备用RPC
# 编辑 .env.production
BLOCKCHAIN_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY

# 2. 调整同步间隔
BLOCKCHAIN_SYNC_INTERVAL=60

# 3. 重启服务
docker-compose -f docker-compose.prod.yml restart
```

---

## 9. 部署后维护

### 9.1 日常监控

```bash
# 1. 每日检查服务状态
./scripts/deploy/check_deployment.sh

# 2. 查看日志
docker logs --tail 100 nexus-server-prod

# 3. 检查磁盘空间
df -h

# 4. 检查系统负载
uptime
```

### 9.2 定期维护

```bash
# 每周任务：
# 1. 清理Docker资源
docker system prune -a --volumes -f

# 2. 检查备份
ls -lh /var/backups/nautilus/database/

# 3. 更新系统
sudo apt update && sudo apt upgrade -y

# 每月任务：
# 1. 审查日志
sudo logrotate -f /etc/logrotate.d/nautilus

# 2. 性能测试
wrk -t4 -c100 -d30s http://localhost:8001/health

# 3. 安全扫描
sudo rkhunter --check
```

### 9.3 更新部署

```bash
# 1. 拉取新版本
./scripts/deploy/deploy_production.sh --version 1.1.0

# 2. 验证部署
./scripts/deploy/check_deployment.sh

# 3. 如果有问题，回滚
./scripts/deploy/deploy_production.sh --rollback
```

---

## 10. 联系支持

如遇到无法解决的问题，请联系：

- **技术支持邮箱**: support@yourdomain.com
- **运维团队**: ops@yourdomain.com
- **紧急热线**: +86-xxx-xxxx-xxxx
- **文档**: https://docs.yourdomain.com

---

## 附录

### A. 相关文档
- [生产部署计划](PRODUCTION_DEPLOYMENT_PLAN.md)
- [服务器配置清单](SERVER_REQUIREMENTS.md)
- [生产环境安全指南](PRODUCTION_SECURITY_GUIDE.md)
- [监控配置指南](MONITORING_GUIDE.md)

### B. 有用的命令

```bash
# 查看所有容器
docker ps -a

# 查看容器资源使用
docker stats

# 进入容器
docker exec -it nexus-server-prod bash

# 查看容器网络
docker network ls

# 查看容器卷
docker volume ls

# 导出容器日志
docker logs nexus-server-prod > /tmp/container.log 2>&1
```

---

**文档结束**

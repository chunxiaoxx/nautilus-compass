# 安全加固指南

**项目**: Nautilus Phase 3 Backend
**版本**: 1.0
**最后更新**: 2026-02-26

---

## 目录

1. [系统加固](#1-系统加固)
2. [网络安全配置](#2-网络安全配置)
3. [应用安全配置](#3-应用安全配置)
4. [数据库安全加固](#4-数据库安全加固)
5. [容器安全加固](#5-容器安全加固)
6. [监控和日志](#6-监控和日志)
7. [备份和恢复](#7-备份和恢复)
8. [合规性配置](#8-合规性配置)

---

## 1. 系统加固

### 1.1 操作系统加固

#### Linux系统加固

**1. 更新系统**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

**2. 禁用不必要的服务**
```bash
# 列出所有服务
systemctl list-unit-files --type=service

# 禁用不需要的服务
sudo systemctl disable <service-name>
sudo systemctl stop <service-name>
```

**3. 配置防火墙**
```bash
# 使用UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 使用firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**4. SSH加固**
```bash
# 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 推荐配置
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# 重启SSH服务
sudo systemctl restart sshd
```

**5. 配置自动安全更新**
```bash
# Ubuntu/Debian
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 1.2 用户和权限管理

**1. 创建专用用户**
```bash
# 创建应用用户
sudo useradd -r -s /bin/bash -d /opt/nautilus nautilus

# 设置目录权限
sudo chown -R nautilus:nautilus /opt/nautilus
sudo chmod 750 /opt/nautilus
```

**2. 配置sudo权限**
```bash
# 编辑sudoers文件
sudo visudo

# 添加应用用户（仅必要命令）
nautilus ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nautilus
```

**3. 密码策略**
```bash
# 编辑密码策略
sudo nano /etc/security/pwquality.conf

# 推荐配置
minlen = 12
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1
```

### 1.3 文件系统安全

**1. 设置文件权限**
```bash
# 应用文件
chmod 640 /opt/nautilus/*.py
chmod 750 /opt/nautilus/*.sh

# 配置文件
chmod 600 /opt/nautilus/.env
chmod 600 /opt/nautilus/keys/*

# 日志目录
chmod 750 /var/log/nautilus
```

**2. 配置文件完整性监控**
```bash
# 安装AIDE
sudo apt install aide

# 初始化数据库
sudo aideinit

# 配置定期检查
echo "0 2 * * * root /usr/bin/aide --check" | sudo tee -a /etc/crontab
```

---

## 2. 网络安全配置

### 2.1 防火墙配置

**1. 应用层防火墙规则**
```bash
# 仅允许必要端口
sudo ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL (内网)
sudo ufw allow from 10.0.0.0/8 to any port 6379  # Redis (内网)
sudo ufw allow 8000/tcp                           # API (公网)
sudo ufw allow 8001/tcp                           # WebSocket (公网)
```

**2. 速率限制**
```bash
# 使用iptables限制连接速率
sudo iptables -A INPUT -p tcp --dport 8000 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 8000 -m state --state NEW -m recent --update --seconds 60 --hitcount 100 -j DROP
```

### 2.2 DDoS防护

**1. 配置连接限制**
```bash
# 限制并发连接数
sudo iptables -A INPUT -p tcp --syn --dport 8000 -m connlimit --connlimit-above 50 -j REJECT

# 限制新连接速率
sudo iptables -A INPUT -p tcp --dport 8000 -m state --state NEW -m limit --limit 50/minute --limit-burst 100 -j ACCEPT
```

**2. 使用Fail2Ban**
```bash
# 安装Fail2Ban
sudo apt install fail2ban

# 配置Fail2Ban
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nautilus-api]
enabled = true
port = 8000
filter = nautilus-api
logpath = /var/log/nautilus/access.log
maxretry = 10
```

### 2.3 SSL/TLS配置

**1. 获取SSL证书**
```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --standalone -d api.nautilus.example.com
```

**2. 配置Nginx反向代理**
```nginx
# /etc/nginx/sites-available/nautilus
server {
    listen 80;
    server_name api.nautilus.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.nautilus.example.com;

    # SSL配置
    ssl_certificate /etc/letsencrypt/live/api.nautilus.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.nautilus.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # 安全头
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 代理配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket支持
    location /socket.io/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 限制请求大小
    client_max_body_size 10M;
}
```

**3. 自动续期证书**
```bash
# 添加cron任务
echo "0 0 * * * root certbot renew --quiet && systemctl reload nginx" | sudo tee -a /etc/crontab
```

---

## 3. 应用安全配置

### 3.1 环境变量配置

**1. 生产环境配置模板**
```bash
# /opt/nautilus/.env.production

# 环境配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=warning

# 服务器配置
HOST=127.0.0.1
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://nautilus_user:STRONG_PASSWORD_HERE@localhost:5432/nautilus_production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis配置
REDIS_URL=redis://:STRONG_PASSWORD_HERE@localhost:6379/0

# JWT配置
JWT_SECRET=$(openssl rand -base64 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# CSRF配置
CSRF_SECRET_KEY=$(openssl rand -base64 32)

# CORS配置
CORS_ORIGINS=https://app.nautilus.example.com
ALLOWED_ORIGINS=https://app.nautilus.example.com

# HTTPS配置
FORCE_HTTPS=true
HSTS_MAX_AGE=31536000

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis

# 区块链配置
BLOCKCHAIN_NETWORK=mainnet
BLOCKCHAIN_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=your-kms-key-id
```

**2. 生成强密钥**
```bash
# 生成JWT密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成CSRF密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成数据库密码
openssl rand -base64 24
```

### 3.2 密钥管理配置

**1. 使用加密文件存储**
```bash
# 创建密钥目录
sudo mkdir -p /opt/nautilus/keys
sudo chmod 700 /opt/nautilus/keys

# 生成加密密钥
python3 /opt/nautilus/setup_key_management.py \
    --source encrypted_file \
    --key-file /opt/nautilus/keys/blockchain_key.json \
    --password "$(openssl rand -base64 32)"
```

**2. 使用AWS KMS**
```bash
# 创建KMS密钥
aws kms create-key --description "Nautilus Blockchain Key"

# 加密私钥
aws kms encrypt \
    --key-id alias/nautilus-blockchain \
    --plaintext fileb://private_key.txt \
    --output text \
    --query CiphertextBlob | base64 -d > encrypted_key.bin

# 配置环境变量
export AWS_KMS_KEY_ID=arn:aws:kms:region:account:key/key-id
export BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=$(base64 encrypted_key.bin)
```

### 3.3 日志配置

**1. 配置日志轮转**
```bash
# /etc/logrotate.d/nautilus
/var/log/nautilus/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nautilus nautilus
    sharedscripts
    postrotate
        systemctl reload nautilus
    endscript
}
```

**2. 配置日志过滤**
```python
# logging_config.py 添加敏感信息过滤器
import re

class SensitiveDataFilter(logging.Filter):
    """过滤敏感信息"""

    PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', 'password=***'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', 'token=***'),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', 'secret=***'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', 'api_key=***'),
        (r'0x[a-fA-F0-9]{64}', '0x***'),  # 私钥
    ]

    def filter(self, record):
        message = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        record.msg = message
        return True
```

---

## 4. 数据库安全加固

### 4.1 PostgreSQL加固

**1. 配置认证**
```bash
# 编辑pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# 推荐配置
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
host    nautilus_production  nautilus_user  127.0.0.1/32         scram-sha-256
host    all             all             0.0.0.0/0               reject
```

**2. 配置SSL连接**
```bash
# 生成SSL证书
sudo openssl req -new -x509 -days 365 -nodes -text \
    -out /etc/postgresql/14/main/server.crt \
    -keyout /etc/postgresql/14/main/server.key

# 设置权限
sudo chmod 600 /etc/postgresql/14/main/server.key
sudo chown postgres:postgres /etc/postgresql/14/main/server.*

# 编辑postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# 启用SSL
ssl = on
ssl_cert_file = '/etc/postgresql/14/main/server.crt'
ssl_key_file = '/etc/postgresql/14/main/server.key'
```

**3. 配置连接限制**
```sql
-- 限制最大连接数
ALTER SYSTEM SET max_connections = 100;

-- 限制用户连接数
ALTER ROLE nautilus_user CONNECTION LIMIT 50;

-- 设置超时
ALTER SYSTEM SET statement_timeout = '30s';
ALTER SYSTEM SET idle_in_transaction_session_timeout = '60s';
```

**4. 配置审计日志**
```bash
# 编辑postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# 审计配置
log_connections = on
log_disconnections = on
log_duration = on
log_statement = 'mod'  # 记录所有修改操作
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### 4.2 数据加密

**1. 启用透明数据加密**
```sql
-- 创建加密表空间
CREATE TABLESPACE encrypted_space
    LOCATION '/var/lib/postgresql/14/encrypted'
    WITH (encryption = on);

-- 将敏感表移到加密表空间
ALTER TABLE users SET TABLESPACE encrypted_space;
```

**2. 列级加密**
```sql
-- 安装pgcrypto扩展
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 加密敏感列
ALTER TABLE users ADD COLUMN email_encrypted BYTEA;
UPDATE users SET email_encrypted = pgp_sym_encrypt(email, 'encryption_key');
```

---

## 5. 容器安全加固

### 5.1 Docker安全配置

**1. 优化Dockerfile**
```dockerfile
# 使用官方基础镜像
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r nautilus && useradd -r -g nautilus nautilus

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=nautilus:nautilus . .

# 切换到非root用户
USER nautilus

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 启动命令
CMD ["uvicorn", "main:socket_app_with_fastapi", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Docker Compose安全配置**
```yaml
version: '3.8'

services:
  api:
    build: .
    restart: unless-stopped
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    tmpfs:
      - /tmp
    volumes:
      - ./logs:/app/logs:rw
    environment:
      - ENVIRONMENT=production
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres:
    image: postgres:14-alpine
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password
    networks:
      - backend

networks:
  backend:
    driver: bridge
    internal: true

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  postgres_data:
```

### 5.2 容器扫描

**1. 使用Trivy扫描镜像**
```bash
# 安装Trivy
sudo apt install trivy

# 扫描镜像
trivy image nautilus-backend:latest

# 扫描并生成报告
trivy image --severity HIGH,CRITICAL --format json -o scan-report.json nautilus-backend:latest
```

**2. 集成到CI/CD**
```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build image
        run: docker build -t nautilus-backend:${{ github.sha }} .

      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: nautilus-backend:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## 6. 监控和日志

### 6.1 Prometheus监控配置

**1. 配置Prometheus**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nautilus-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
```

**2. 配置告警规则**
```yaml
# alerts.yml
groups:
  - name: nautilus_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLoginFailures
        expr: rate(login_attempts_total{success="false"}[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High login failure rate"
```

### 6.2 日志聚合

**1. 配置ELK Stack**
```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=changeme
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=changeme
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

---

## 7. 备份和恢复

### 7.1 数据库备份

**1. 自动备份脚本**
```bash
#!/bin/bash
# /opt/nautilus/scripts/backup_database.sh

BACKUP_DIR="/var/backups/nautilus"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nautilus_$DATE.sql.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -U nautilus_user nautilus_production | gzip > $BACKUP_FILE

# 加密备份
gpg --encrypt --recipient backup@nautilus.example.com $BACKUP_FILE

# 上传到S3
aws s3 cp $BACKUP_FILE.gpg s3://nautilus-backups/database/

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.sql.gz*" -mtime +30 -delete

# 验证备份
if [ -f "$BACKUP_FILE.gpg" ]; then
    echo "Backup successful: $BACKUP_FILE.gpg"
else
    echo "Backup failed!" | mail -s "Backup Failed" admin@nautilus.example.com
fi
```

**2. 配置定时备份**
```bash
# 添加cron任务
sudo crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/nautilus/scripts/backup_database.sh
```

### 7.2 恢复流程

**1. 数据库恢复**
```bash
#!/bin/bash
# 从S3下载备份
aws s3 cp s3://nautilus-backups/database/nautilus_20260226_020000.sql.gz.gpg .

# 解密备份
gpg --decrypt nautilus_20260226_020000.sql.gz.gpg > nautilus_20260226_020000.sql.gz

# 解压
gunzip nautilus_20260226_020000.sql.gz

# 恢复数据库
psql -U nautilus_user nautilus_production < nautilus_20260226_020000.sql
```

---

## 8. 合规性配置

### 8.1 GDPR合规

**1. 实现数据导出**
```python
# api/gdpr.py
@router.get("/gdpr/export")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出用户数据"""
    user_data = {
        "personal_info": {
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat()
        },
        "tasks": [task.to_dict() for task in current_user.tasks],
        "agents": [agent.to_dict() for agent in current_user.agents]
    }

    return JSONResponse(content=user_data)
```

**2. 实现数据删除**
```python
@router.delete("/gdpr/delete")
async def delete_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户数据（被遗忘权）"""
    # 匿名化而非删除（保持数据完整性）
    current_user.username = f"deleted_user_{current_user.id}"
    current_user.email = f"deleted_{current_user.id}@deleted.local"
    current_user.is_active = False

    db.commit()

    return {"message": "User data deleted successfully"}
```

---

## 总结

本指南提供了全面的安全加固措施，涵盖系统、网络、应用、数据库等多个层面。建议按照优先级逐步实施：

**P0 - 立即实施**:
- 系统更新和补丁
- 防火墙配置
- SSL/TLS配置
- 强密码策略

**P1 - 本周实施**:
- SSH加固
- 数据库安全配置
- 日志配置
- 备份策略

**P2 - 本月实施**:
- 监控和告警
- 容器安全
- 自动化扫描
- 合规性配置

定期审查和更新安全配置，确保系统始终处于最佳安全状态。

# Nautilus Phase 3 Backend - 服务器配置清单

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-02-27
- **最后更新**: 2026-02-27
- **状态**: 生产就绪

---

## 1. 硬件要求

### 1.1 最小配置（小规模部署）

#### 应用服务器
- **CPU**: 4核心 (推荐 Intel Xeon 或 AMD EPYC)
- **内存**: 8GB RAM
- **存储**: 100GB SSD
- **网络**: 1Gbps 网卡
- **数量**: 1台（单节点）

#### 数据库服务器
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 200GB SSD
- **网络**: 1Gbps 网卡
- **数量**: 1台

**适用场景**: 开发环境、测试环境、小规模生产环境（< 100并发用户）

---

### 1.2 推荐配置（中等规模部署）

#### 应用服务器
- **CPU**: 8核心 @ 2.5GHz+
- **内存**: 16GB RAM (推荐 32GB)
- **存储**:
  - 系统盘: 100GB SSD
  - 数据盘: 500GB SSD (用于日志和临时文件)
- **网络**: 10Gbps 网卡
- **数量**: 2台（主备模式）

#### 数据库服务器
- **CPU**: 8核心 @ 3.0GHz+
- **内存**: 32GB RAM
- **存储**:
  - 系统盘: 100GB SSD
  - 数据盘: 1TB NVMe SSD (RAID 10)
- **网络**: 10Gbps 网卡
- **数量**: 2台（主从复制）

#### Redis服务器
- **CPU**: 4核心
- **内存**: 16GB RAM
- **存储**: 100GB SSD
- **网络**: 10Gbps 网卡
- **数量**: 3台（哨兵模式）

**适用场景**: 中等规模生产环境（100-1000并发用户）

---

### 1.3 高性能配置（大规模部署）

#### 应用服务器
- **CPU**: 16核心 @ 3.0GHz+
- **内存**: 64GB RAM
- **存储**:
  - 系统盘: 200GB NVMe SSD
  - 数据盘: 2TB NVMe SSD
- **网络**: 25Gbps 网卡
- **数量**: 4台+（负载均衡）

#### 数据库服务器
- **CPU**: 32核心 @ 3.5GHz+
- **内存**: 128GB RAM
- **存储**:
  - 系统盘: 200GB NVMe SSD
  - 数据盘: 4TB NVMe SSD (RAID 10)
- **网络**: 25Gbps 网卡
- **数量**: 3台+（主从复制 + 读副本）

#### Redis服务器
- **CPU**: 8核心
- **内存**: 32GB RAM
- **存储**: 200GB NVMe SSD
- **网络**: 25Gbps 网卡
- **数量**: 6台（哨兵集群）

#### 负载均衡器
- **CPU**: 8核心
- **内存**: 16GB RAM
- **存储**: 100GB SSD
- **网络**: 40Gbps 网卡
- **数量**: 2台（主备）

**适用场景**: 大规模生产环境（1000+并发用户）

---

### 1.4 存储要求详细说明

#### 磁盘类型
- **系统盘**: SSD (推荐 NVMe)
- **数据库**: NVMe SSD (RAID 10 用于生产环境)
- **日志**: SSD 或 HDD (取决于日志量)
- **备份**: HDD 或对象存储 (S3/OSS)

#### IOPS要求
- **应用服务器**: 5,000+ IOPS
- **数据库服务器**: 20,000+ IOPS (推荐 50,000+)
- **Redis服务器**: 10,000+ IOPS

#### 磁盘空间规划
```
应用服务器:
├── /                    50GB   (系统)
├── /var/log            20GB   (日志)
├── /var/lib/docker     30GB   (Docker镜像和容器)
└── /data              500GB   (应用数据)

数据库服务器:
├── /                    50GB   (系统)
├── /var/log            20GB   (日志)
├── /var/lib/postgresql 800GB  (数据库数据)
└── /backup            100GB   (本地备份)
```

---

## 2. 软件要求

### 2.1 操作系统

#### 推荐操作系统
- **Ubuntu 22.04 LTS** (推荐)
- **Ubuntu 20.04 LTS**
- **Debian 11 (Bullseye)**
- **CentOS Stream 9**
- **Rocky Linux 9**
- **Red Hat Enterprise Linux 9**

#### 内核版本
- **最低**: Linux Kernel 5.4+
- **推荐**: Linux Kernel 5.15+

#### 系统架构
- **x86_64** (AMD64)
- **ARM64** (可选，需要测试)

---

### 2.2 容器运行时

#### Docker
- **版本**: Docker CE 24.0+ 或 Docker EE 24.0+
- **安装方式**: 官方仓库安装

```bash
# Ubuntu/Debian 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 验证安装
docker --version
```

#### Docker Compose
- **版本**: Docker Compose 2.20+

```bash
# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

---

### 2.3 数据库

#### PostgreSQL
- **版本**: PostgreSQL 15+ (推荐 16+)
- **扩展**:
  - `pg_stat_statements` (性能监控)
  - `pgcrypto` (加密)
  - `uuid-ossp` (UUID生成)

```bash
# Ubuntu 安装 PostgreSQL 16
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo apt install -y postgresql-16 postgresql-contrib-16

# 验证安装
psql --version
```

#### 配置要求
- **最大连接数**: 200+
- **共享缓冲区**: 25% 系统内存
- **工作内存**: 根据并发查询调整
- **WAL配置**: 启用归档和复制

---

### 2.4 缓存

#### Redis
- **版本**: Redis 7.0+
- **模式**:
  - 单机模式（开发/测试）
  - 哨兵模式（生产环境推荐）
  - 集群模式（大规模部署）

```bash
# Ubuntu 安装 Redis 7
sudo apt install -y lsb-release curl gpg
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt update
sudo apt install -y redis

# 验证安装
redis-server --version
```

---

### 2.5 Web服务器/反向代理

#### Nginx (推荐)
- **版本**: Nginx 1.24+

```bash
# Ubuntu 安装 Nginx
sudo apt install -y nginx

# 验证安装
nginx -v
```

#### HAProxy (可选)
- **版本**: HAProxy 2.8+

---

### 2.6 监控工具

#### Prometheus
- **版本**: Prometheus 2.45+

#### Grafana
- **版本**: Grafana 10.0+

#### Node Exporter
- **版本**: Node Exporter 1.6+

---

### 2.7 系统工具

#### 必需工具
```bash
# Ubuntu/Debian
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    iotop \
    net-tools \
    dnsutils \
    jq \
    bc \
    openssl \
    ca-certificates \
    gnupg \
    lsb-release
```

#### 性能分析工具
```bash
sudo apt install -y \
    sysstat \
    iftop \
    nethogs \
    iperf3 \
    stress-ng
```

---

## 3. 网络要求

### 3.1 端口配置

#### 入站端口（需要开放）

| 端口 | 协议 | 服务 | 来源 | 说明 |
|------|------|------|------|------|
| 80 | TCP | HTTP | 0.0.0.0/0 | HTTP流量（重定向到HTTPS） |
| 443 | TCP | HTTPS | 0.0.0.0/0 | HTTPS流量 |
| 8000 | TCP | API | 内网 | API服务（内部） |
| 8001 | TCP | Nexus | 内网 | Nexus协议（内部） |
| 22 | TCP | SSH | 管理IP | SSH管理访问 |

#### 内部端口（仅内网访问）

| 端口 | 协议 | 服务 | 说明 |
|------|------|------|------|
| 5432 | TCP | PostgreSQL | 数据库连接 |
| 6379 | TCP | Redis | 缓存连接 |
| 26379 | TCP | Redis Sentinel | Redis哨兵 |
| 9090 | TCP | Prometheus | 监控指标 |
| 3000 | TCP | Grafana | 监控面板 |
| 9100 | TCP | Node Exporter | 系统指标 |

---

### 3.2 防火墙配置

#### UFW配置（Ubuntu）

```bash
# 启用UFW
sudo ufw enable

# 允许SSH（修改为实际管理IP）
sudo ufw allow from 192.168.1.0/24 to any port 22

# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许内网访问数据库
sudo ufw allow from 10.0.0.0/8 to any port 5432
sudo ufw allow from 10.0.0.0/8 to any port 6379

# 查看规则
sudo ufw status numbered
```

#### iptables配置

```bash
# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许本地回环
iptables -A INPUT -i lo -j ACCEPT

# 允许SSH（限制IP）
iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport 22 -j ACCEPT

# 允许HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 默认拒绝
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 保存规则
iptables-save > /etc/iptables/rules.v4
```

---

### 3.3 网络性能优化

#### 系统参数调优

```bash
# 编辑 /etc/sysctl.conf
cat >> /etc/sysctl.conf << EOF

# 网络性能优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 10000 65535

# 文件描述符限制
fs.file-max = 2097152

EOF

# 应用配置
sudo sysctl -p
```

---

### 3.4 DNS配置

#### 域名要求
- **主域名**: `api.yourdomain.com`
- **备用域名**: `api-backup.yourdomain.com`
- **监控域名**: `monitoring.yourdomain.com`

#### DNS记录配置

```
# A记录
api.yourdomain.com.           IN  A     203.0.113.10
api-backup.yourdomain.com.    IN  A     203.0.113.11

# AAAA记录（IPv6，可选）
api.yourdomain.com.           IN  AAAA  2001:db8::10

# CNAME记录
www.api.yourdomain.com.       IN  CNAME api.yourdomain.com.

# TXT记录（SPF，可选）
yourdomain.com.               IN  TXT   "v=spf1 ip4:203.0.113.10 -all"
```

---

### 3.5 负载均衡配置

#### Nginx负载均衡示例

```nginx
upstream backend_servers {
    least_conn;
    server 10.0.1.10:8001 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8001 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    location / {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 4. 安全要求

### 4.1 SSL/TLS证书

#### 证书要求
- **类型**:
  - Let's Encrypt（免费，推荐用于测试）
  - 商业证书（推荐用于生产）
  - EV证书（企业级）
- **加密强度**: RSA 2048位+ 或 ECC 256位+
- **有效期**: 至少90天
- **自动续期**: 必须配置

#### 获取Let's Encrypt证书

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d api.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

---

### 4.2 SSH安全配置

#### SSH配置 (/etc/ssh/sshd_config)

```bash
# 禁用root登录
PermitRootLogin no

# 禁用密码认证
PasswordAuthentication no
PubkeyAuthentication yes

# 修改默认端口（可选）
Port 2222

# 限制用户
AllowUsers nautilus admin

# 启用严格模式
StrictModes yes

# 禁用空密码
PermitEmptyPasswords no

# 设置超时
ClientAliveInterval 300
ClientAliveCountMax 2
```

重启SSH服务：
```bash
sudo systemctl restart sshd
```

---

### 4.3 用户和权限

#### 创建专用用户

```bash
# 创建nautilus用户
sudo useradd -m -s /bin/bash nautilus
sudo usermod -aG docker nautilus

# 设置密码
sudo passwd nautilus

# 配置sudo权限（可选）
echo "nautilus ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose" | sudo tee /etc/sudoers.d/nautilus
```

#### 文件权限

```bash
# 应用目录权限
sudo chown -R nautilus:nautilus /opt/nautilus
sudo chmod -R 750 /opt/nautilus

# 日志目录权限
sudo chown -R nautilus:nautilus /var/log/nautilus
sudo chmod -R 750 /var/log/nautilus

# 配置文件权限
sudo chmod 600 /opt/nautilus/.env.production
```

---

### 4.4 系统加固

#### 禁用不必要的服务

```bash
# 列出所有服务
systemctl list-unit-files --type=service

# 禁用不必要的服务
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl disable avahi-daemon
```

#### 安装安全工具

```bash
# 安装fail2ban
sudo apt install -y fail2ban

# 配置fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 安装rkhunter（rootkit检测）
sudo apt install -y rkhunter
sudo rkhunter --update
sudo rkhunter --check
```

---

### 4.5 审计和日志

#### 配置审计日志

```bash
# 安装auditd
sudo apt install -y auditd

# 启用审计
sudo systemctl enable auditd
sudo systemctl start auditd

# 查看审计日志
sudo ausearch -m USER_LOGIN
```

#### 日志轮转配置

```bash
# 创建 /etc/logrotate.d/nautilus
cat > /etc/logrotate.d/nautilus << EOF
/var/log/nautilus/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nautilus nautilus
    sharedscripts
    postrotate
        systemctl reload nautilus || true
    endscript
}
EOF
```

---

## 5. 备份要求

### 5.1 备份策略

#### 数据库备份
- **频率**: 每天一次（凌晨2点）
- **保留期**: 30天
- **方式**:
  - 全量备份（每天）
  - 增量备份（每小时，可选）
  - WAL归档（实时）

#### 配置文件备份
- **频率**: 每次修改后
- **保留期**: 永久
- **方式**: Git版本控制

#### 应用数据备份
- **频率**: 每天一次
- **保留期**: 7天
- **方式**: 文件系统快照或rsync

---

### 5.2 备份脚本

#### 数据库备份脚本

```bash
#!/bin/bash
# /opt/nautilus/scripts/backup/backup_database.sh

BACKUP_DIR="/var/backups/nautilus/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/nautilus_${TIMESTAMP}.sql"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 执行备份
pg_dump -h localhost -U nautilus_user nautilus_production | gzip > "${BACKUP_FILE}.gz"

# 清理旧备份
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +30 -delete

# 上传到S3（可选）
# aws s3 cp "${BACKUP_FILE}.gz" s3://nautilus-backups/database/
```

---

### 5.3 灾难恢复

#### 恢复流程

```bash
# 1. 停止应用
sudo systemctl stop nautilus

# 2. 恢复数据库
gunzip -c /var/backups/nautilus/database/nautilus_20260227_020000.sql.gz | \
    psql -h localhost -U nautilus_user nautilus_production

# 3. 验证数据
psql -h localhost -U nautilus_user -d nautilus_production -c "SELECT COUNT(*) FROM users;"

# 4. 启动应用
sudo systemctl start nautilus
```

---

## 6. 监控要求

### 6.1 系统监控指标

#### 必须监控的指标
- **CPU使用率**: < 80%
- **内存使用率**: < 85%
- **磁盘使用率**: < 80%
- **磁盘I/O**: IOPS和吞吐量
- **网络流量**: 入站/出站带宽
- **系统负载**: Load Average

---

### 6.2 应用监控指标

#### 必须监控的指标
- **请求响应时间**: P50, P95, P99
- **请求成功率**: > 99.9%
- **错误率**: < 0.1%
- **并发连接数**
- **队列长度**
- **数据库连接池使用率**

---

### 6.3 告警配置

#### 告警级别

| 级别 | 响应时间 | 通知方式 |
|------|----------|----------|
| P0 - 紧急 | 立即 | 电话 + 短信 + 邮件 |
| P1 - 严重 | 15分钟内 | 短信 + 邮件 |
| P2 - 警告 | 1小时内 | 邮件 |
| P3 - 信息 | 24小时内 | 邮件 |

---

## 7. 性能基准

### 7.1 性能目标

| 指标 | 目标值 |
|------|--------|
| API响应时间 (P95) | < 200ms |
| API响应时间 (P99) | < 500ms |
| 并发用户数 | 1000+ |
| 每秒请求数 (RPS) | 500+ |
| 数据库查询时间 (P95) | < 100ms |
| 缓存命中率 | > 90% |
| 系统可用性 | > 99.9% |

---

## 8. 部署检查清单

### 8.1 硬件检查
- [ ] CPU核心数满足要求
- [ ] 内存容量满足要求
- [ ] 磁盘空间充足
- [ ] 磁盘类型为SSD或NVMe
- [ ] 网络带宽满足要求

### 8.2 软件检查
- [ ] 操作系统版本正确
- [ ] Docker已安装并运行
- [ ] Docker Compose已安装
- [ ] PostgreSQL已安装并配置
- [ ] Redis已安装并配置
- [ ] Nginx已安装并配置

### 8.3 网络检查
- [ ] 防火墙规则已配置
- [ ] DNS记录已配置
- [ ] SSL证书已安装
- [ ] 端口可访问性已验证
- [ ] 负载均衡已配置

### 8.4 安全检查
- [ ] SSH密钥认证已启用
- [ ] root登录已禁用
- [ ] 防火墙已启用
- [ ] fail2ban已配置
- [ ] 审计日志已启用
- [ ] 文件权限已正确设置

### 8.5 备份检查
- [ ] 备份脚本已配置
- [ ] 备份定时任务已设置
- [ ] 备份恢复已测试
- [ ] 远程备份已配置

### 8.6 监控检查
- [ ] Prometheus已安装
- [ ] Grafana已安装
- [ ] 监控指标正常采集
- [ ] 告警规则已配置
- [ ] 告警通知已测试

---

## 9. 联系信息

如有问题，请联系：
- **技术支持**: support@yourdomain.com
- **运维团队**: ops@yourdomain.com
- **紧急联系**: +86-xxx-xxxx-xxxx

---

**文档结束**

# 生产数据库配置完整指南

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-02-27
- **维护团队**: DBA团队
- **适用环境**: 生产环境

---

## 目录

1. [快速开始](#快速开始)
2. [数据库安装](#数据库安装)
3. [初始化配置](#初始化配置)
4. [备份策略](#备份策略)
5. [性能优化](#性能优化)
6. [高可用配置](#高可用配置)
7. [监控和维护](#监控和维护)
8. [故障排查](#故障排查)
9. [安全加固](#安全加固)

---

## 快速开始

### 1. 环境准备

```bash
# 设置环境变量
export DB_NAME="nautilus_production"
export DB_USER="nautilus_user"
export DB_PASSWORD="your_secure_password_here"
export DB_READONLY_PASSWORD="readonly_password_here"
export REPLICATION_PASSWORD="replication_password_here"
```

### 2. 初始化数据库

```bash
# 赋予脚本执行权限
chmod +x scripts/init_production_db.sh

# 执行初始化
./scripts/init_production_db.sh
```

### 3. 应用配置文件

```bash
# 复制配置文件到 PostgreSQL 配置目录
sudo cp config/postgresql.production.conf /etc/postgresql/15/main/conf.d/production.conf

# 重启 PostgreSQL
sudo systemctl restart postgresql
```

### 4. 设置自动备份

```bash
# 赋予备份脚本执行权限
chmod +x scripts/backup_database.sh

# 添加到 crontab（每天凌晨2点执行）
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/scripts/backup_database.sh --type both") | crontab -
```

---

## 数据库安装

### Ubuntu/Debian 安装

```bash
# 添加 PostgreSQL 官方仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# 导入仓库签名密钥
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# 更新包列表
sudo apt update

# 安装 PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15 -y

# 验证安装
psql --version
```

### CentOS/RHEL 安装

```bash
# 安装 PostgreSQL 仓库
sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# 禁用内置 PostgreSQL 模块
sudo dnf -qy module disable postgresql

# 安装 PostgreSQL 15
sudo yum install -y postgresql15-server postgresql15-contrib

# 初始化数据库
sudo /usr/pgsql-15/bin/postgresql-15-setup initdb

# 启动服务
sudo systemctl enable postgresql-15
sudo systemctl start postgresql-15
```

---

## 初始化配置

### 配置文件说明

#### 1. postgresql.production.conf

位置: `config/postgresql.production.conf`

主要配置项：
- **连接设置**: 最大连接数 200
- **内存设置**: 基于 16GB RAM 优化
- **WAL 设置**: 支持复制和归档
- **日志设置**: 详细的日志记录
- **性能监控**: pg_stat_statements 扩展

#### 2. pg_hba.conf

配置客户端认证：

```conf
# 本地连接
local   all             postgres                                peer
local   all             all                                     scram-sha-256

# IPv4 本地连接
host    all             all             127.0.0.1/32            scram-sha-256

# 内网连接
host    all             nautilus_user   10.0.0.0/8              scram-sha-256
host    all             nautilus_user   172.16.0.0/12           scram-sha-256
host    all             nautilus_user   192.168.0.0/16          scram-sha-256

# 复制连接
host    replication     replicator      10.0.0.0/8              scram-sha-256
```

### 初始化脚本功能

`scripts/init_production_db.sh` 执行以下操作：

1. ✅ 创建生产数据库
2. ✅ 创建应用用户并授权
3. ✅ 创建只读用户（可选）
4. ✅ 创建复制用户（可选）
5. ✅ 安装必要的扩展
6. ✅ 创建 WAL 归档目录
7. ✅ 运行数据库迁移
8. ✅ 导入初始数据
9. ✅ 验证配置

---

## 备份策略

### 备份类型

#### 1. 逻辑备份（pg_dump）

**优点**:
- 可读的 SQL 格式
- 可选择性恢复
- 跨版本兼容

**使用场景**:
- 日常备份
- 数据迁移
- 部分数据恢复

**执行命令**:
```bash
./scripts/backup_database.sh --type logical
```

#### 2. 物理备份（pg_basebackup）

**优点**:
- 备份速度快
- 完整的数据库副本
- 支持时间点恢复

**使用场景**:
- 大型数据库
- 灾难恢复
- 主从复制

**执行命令**:
```bash
./scripts/backup_database.sh --type physical
```

#### 3. 连续归档（WAL 归档）

**优点**:
- 时间点恢复（PITR）
- 最小数据丢失
- 支持增量备份

**配置**:
```conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f'
```

### 备份计划

| 备份类型 | 频率 | 保留期 | 存储位置 |
|---------|------|--------|---------|
| 逻辑备份 | 每天 | 30天 | 本地 + S3 |
| 物理备份 | 每周 | 60天 | S3 |
| WAL 归档 | 实时 | 7天 | 本地 + S3 |

### 自动备份配置

```bash
# 编辑 crontab
crontab -e

# 添加以下任务
# 每天凌晨2点执行逻辑备份
0 2 * * * /path/to/scripts/backup_database.sh --type logical --s3-bucket my-backup-bucket

# 每周日凌晨3点执行物理备份
0 3 * * 0 /path/to/scripts/backup_database.sh --type physical --s3-bucket my-backup-bucket

# 每小时验证最新备份
0 * * * * /path/to/scripts/verify_backup.sh /var/backups/postgresql/logical/latest.sql.gz
```

### 备份验证

定期验证备份的完整性：

```bash
# 验证备份文件
./scripts/verify_backup.sh /var/backups/postgresql/nautilus_production_20260227.sql.gz

# 测试恢复
./scripts/restore_database.sh backup.sql.gz test_restore --mode create
```

---

## 性能优化

### 1. 索引优化

执行索引创建脚本：

```bash
psql -U nautilus_user -d nautilus_production -f scripts/create_indexes.sql
```

**索引类型**:
- **B-tree 索引**: 等值和范围查询
- **GIN 索引**: 全文搜索和 JSONB
- **部分索引**: 特定条件优化
- **唯一索引**: 数据唯一性

### 2. 查询优化

#### 启用查询统计

```sql
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 查看最慢的查询
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

#### 分析查询计划

```sql
-- 使用 EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'user@example.com';
```

### 3. 连接池配置（PgBouncer）

#### 安装 PgBouncer

```bash
sudo apt install pgbouncer -y
```

#### 配置文件

`/etc/pgbouncer/pgbouncer.ini`:

```ini
[databases]
nautilus_production = host=localhost port=5432 dbname=nautilus_production

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
max_db_connections = 100
```

#### 应用连接字符串

```python
# 使用 PgBouncer 连接
DATABASE_URL = "postgresql://nautilus_user:password@localhost:6432/nautilus_production"
```

### 4. 内存优化

基于 16GB RAM 服务器：

```conf
shared_buffers = 4GB              # 25% 系统内存
effective_cache_size = 12GB       # 75% 系统内存
maintenance_work_mem = 1GB        # 维护操作
work_mem = 20MB                   # 每个查询操作
```

### 5. VACUUM 优化

```sql
-- 手动 VACUUM
VACUUM ANALYZE;

-- 查看自动 VACUUM 状态
SELECT
    schemaname,
    tablename,
    last_vacuum,
    last_autovacuum,
    n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

---

## 高可用配置

### 1. 主从复制（Streaming Replication）

#### 主服务器配置

```conf
# postgresql.conf
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB
```

```sql
-- 创建复制用户
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'ReplicatorPassword123!';
```

```conf
# pg_hba.conf
host    replication     replicator      10.0.0.0/8              scram-sha-256
```

#### 从服务器配置

```bash
# 停止 PostgreSQL
sudo systemctl stop postgresql

# 清空数据目录
sudo rm -rf /var/lib/postgresql/15/main/*

# 从主服务器复制数据
pg_basebackup -h 10.0.1.10 -U replicator \
  -D /var/lib/postgresql/15/main \
  -Xs -P -R

# 启动从服务器
sudo systemctl start postgresql
```

#### 验证复制状态

```sql
-- 主服务器
SELECT * FROM pg_stat_replication;

-- 从服务器
SELECT pg_is_in_recovery();
SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

### 2. 自动故障转移（Patroni）

#### 安装 Patroni

```bash
sudo pip3 install patroni[etcd]
sudo apt install etcd -y
```

#### 配置文件

`/etc/patroni/patroni.yml`:

```yaml
scope: nautilus-cluster
namespace: /db/
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.1.10:8008

etcd:
  host: 10.0.1.20:2379

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.1.10:5432
  data_dir: /var/lib/postgresql/15/main
  authentication:
    replication:
      username: replicator
      password: ReplicatorPassword123!
```

---

## 监控和维护

### 1. 性能监控查询

```sql
-- 数据库连接统计
SELECT
    datname,
    count(*) AS connections,
    max(state) AS state
FROM pg_stat_activity
GROUP BY datname;

-- 缓存命中率
SELECT
    sum(heap_blks_read) AS heap_read,
    sum(heap_blks_hit) AS heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS cache_hit_ratio
FROM pg_statio_user_tables;

-- 表膨胀检查
SELECT
    schemaname,
    tablename,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

### 2. 日常维护任务

| 任务 | 频率 | 命令 |
|-----|------|------|
| ANALYZE | 每天 | `ANALYZE;` |
| VACUUM | 每周 | `VACUUM ANALYZE;` |
| REINDEX | 每月 | `REINDEX DATABASE nautilus_production;` |
| 备份验证 | 每周 | `./scripts/verify_backup.sh` |
| 日志清理 | 每周 | `find /var/log/postgresql -mtime +30 -delete` |

### 3. 监控指标

**关键指标**:
- 连接数
- 缓存命中率
- 查询响应时间
- 复制延迟
- 磁盘使用率
- 表膨胀率

---

## 故障排查

### 常见问题

#### 1. 连接数过多

**症状**: `FATAL: sorry, too many clients already`

**解决方案**:
```sql
-- 查看当前连接
SELECT * FROM pg_stat_activity;

-- 终止空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '1 hour';
```

#### 2. 磁盘空间不足

**症状**: 数据库无法写入

**解决方案**:
```bash
# 查看数据库大小
du -sh /var/lib/postgresql/15/main

# 清理 WAL 日志
pg_archivecleanup /var/lib/postgresql/15/main/pg_wal 000000010000000000000010

# VACUUM FULL 回收空间
psql -U postgres -d nautilus_production -c "VACUUM FULL;"
```

#### 3. 性能下降

**症状**: 查询变慢

**解决方案**:
```sql
-- 更新统计信息
ANALYZE;

-- 重建索引
REINDEX DATABASE nautilus_production;

-- 检查慢查询
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

#### 4. 复制延迟

**症状**: 从服务器数据滞后

**解决方案**:
```sql
-- 检查复制延迟
SELECT
    client_addr,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
FROM pg_stat_replication;

-- 检查 WAL 发送速率
SELECT * FROM pg_stat_replication;
```

---

## 安全加固

### 1. 网络安全

```conf
# 仅监听本地
listen_addresses = 'localhost'

# 或限制特定IP
listen_addresses = '10.0.1.10'
```

### 2. 认证加固

```conf
# 使用 SCRAM-SHA-256
password_encryption = scram-sha-256

# pg_hba.conf 配置
host    all             all             0.0.0.0/0               reject
```

### 3. SSL/TLS 配置

```conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
```

### 4. 审计日志

```conf
log_connections = on
log_disconnections = on
log_statement = 'ddl'
log_min_duration_statement = 1000
```

### 5. 权限最小化

```sql
-- 撤销 public schema 的公共权限
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 仅授予必要权限
GRANT USAGE ON SCHEMA public TO nautilus_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nautilus_user;
```

---

## 相关文档

- [PRODUCTION_DATABASE_GUIDE.md](PRODUCTION_DATABASE_GUIDE.md) - 详细的数据库配置指南
- [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) - 数据库迁移指南
- [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md) - 生产环境部署指南
- [MONITORING_GUIDE.md](MONITORING_GUIDE.md) - 监控配置指南

---

## 附录

### A. 配置文件清单

| 文件 | 位置 | 说明 |
|-----|------|------|
| postgresql.production.conf | config/ | 生产环境配置 |
| init_production_db.sh | scripts/ | 数据库初始化脚本 |
| backup_database.sh | scripts/ | 备份脚本 |
| verify_backup.sh | scripts/ | 备份验证脚本 |
| restore_database.sh | scripts/ | 恢复脚本 |
| create_indexes.sql | scripts/ | 索引创建脚本 |

### B. 环境变量

```bash
# 数据库配置
export DB_NAME="nautilus_production"
export DB_USER="nautilus_user"
export DB_PASSWORD="your_secure_password"
export DB_HOST="localhost"
export DB_PORT="5432"

# 备份配置
export BACKUP_DIR="/var/backups/postgresql"
export RETENTION_DAYS="30"
export S3_BUCKET="nautilus-backups"

# 通知配置
export NOTIFICATION_EMAIL="admin@example.com"
```

### C. 快速命令参考

```bash
# 启动/停止/重启
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql

# 查看状态
sudo systemctl status postgresql
pg_isready

# 连接数据库
psql -U nautilus_user -d nautilus_production

# 备份
./scripts/backup_database.sh --type logical

# 恢复
./scripts/restore_database.sh backup.sql.gz nautilus_production

# 验证备份
./scripts/verify_backup.sh backup.sql.gz
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-27
**维护团队**: DBA团队

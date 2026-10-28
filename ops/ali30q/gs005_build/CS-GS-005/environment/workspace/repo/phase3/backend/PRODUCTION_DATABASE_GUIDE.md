# 数据库生产配置指南

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-02-26
- **适用环境**: 生产环境
- **维护团队**: DBA团队

---

## 1. 概述

本指南详细说明如何配置和优化 PostgreSQL 数据库用于生产环境，包括安装、配置、备份、高可用和性能优化。

### 1.1 PostgreSQL 版本选择

推荐使用 **PostgreSQL 15** 或更高版本：
- 性能改进
- 更好的并发处理
- 改进的查询优化器
- 更强的安全特性

---

## 2. PostgreSQL 安装

### 2.1 Ubuntu/Debian 安装

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

### 2.2 CentOS/RHEL 安装

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

### 2.3 Docker 安装（开发/测试）

```bash
docker run -d \
  --name nautilus-postgres \
  -e POSTGRES_USER=nautilus_admin \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=nautilus_production \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine
```

---

## 3. 数据库初始化

### 3.1 创建数据库和用户

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 psql 中执行
CREATE DATABASE nautilus_production;

CREATE USER nautilus_user WITH ENCRYPTED PASSWORD 'YourStrongPassword123!';

GRANT ALL PRIVILEGES ON DATABASE nautilus_production TO nautilus_user;

# 授予 schema 权限
\c nautilus_production
GRANT ALL ON SCHEMA public TO nautilus_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nautilus_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nautilus_user;

# 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nautilus_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nautilus_user;

\q
```

### 3.2 创建只读用户（可选）

```sql
-- 创建只读用户
CREATE USER nautilus_readonly WITH ENCRYPTED PASSWORD 'ReadOnlyPassword123!';

-- 授予连接权限
GRANT CONNECT ON DATABASE nautilus_production TO nautilus_readonly;

-- 授予 schema 使用权限
\c nautilus_production
GRANT USAGE ON SCHEMA public TO nautilus_readonly;

-- 授予所有表的 SELECT 权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nautilus_readonly;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO nautilus_readonly;
```

---

## 4. PostgreSQL 配置优化

### 4.1 postgresql.conf 配置

配置文件位置：`/etc/postgresql/15/main/postgresql.conf`

```conf
# ============================================================================
# 连接设置
# ============================================================================
listen_addresses = 'localhost'          # 仅监听本地（生产环境）
# listen_addresses = '*'                # 监听所有接口（如需远程访问）
port = 5432
max_connections = 200                   # 最大连接数

# ============================================================================
# 内存设置（基于 16GB RAM 服务器）
# ============================================================================
shared_buffers = 4GB                    # 25% 的系统内存
effective_cache_size = 12GB             # 75% 的系统内存
maintenance_work_mem = 1GB              # 维护操作内存
work_mem = 20MB                         # 每个查询操作的内存

# ============================================================================
# 查询规划器
# ============================================================================
random_page_cost = 1.1                  # SSD 优化
effective_io_concurrency = 200          # SSD 并发 I/O

# ============================================================================
# WAL (Write-Ahead Logging) 设置
# ============================================================================
wal_level = replica                     # 支持复制
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
checkpoint_completion_target = 0.9
wal_compression = on

# ============================================================================
# 复制设置（主从复制）
# ============================================================================
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
hot_standby_feedback = on

# ============================================================================
# 日志设置
# ============================================================================
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_timezone = 'UTC'

# 慢查询日志
log_min_duration_statement = 1000       # 记录超过 1 秒的查询
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# ============================================================================
# 性能监控
# ============================================================================
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
pg_stat_statements.max = 10000

# ============================================================================
# 自动清理（VACUUM）
# ============================================================================
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 10s
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05

# ============================================================================
# 安全设置
# ============================================================================
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
password_encryption = scram-sha-256
```

### 4.2 pg_hba.conf 配置

配置文件位置：`/etc/postgresql/15/main/pg_hba.conf`

```conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# 本地连接
local   all             postgres                                peer
local   all             all                                     scram-sha-256

# IPv4 本地连接
host    all             all             127.0.0.1/32            scram-sha-256

# IPv6 本地连接
host    all             all             ::1/128                 scram-sha-256

# 内网连接（根据实际网络调整）
host    all             nautilus_user   10.0.0.0/8              scram-sha-256
host    all             nautilus_user   172.16.0.0/12           scram-sha-256
host    all             nautilus_user   192.168.0.0/16          scram-sha-256

# 复制连接
host    replication     replicator      10.0.0.0/8              scram-sha-256

# 拒绝所有其他连接
host    all             all             0.0.0.0/0               reject
```

### 4.3 应用配置后重启

```bash
# 检查配置语法
sudo -u postgres /usr/lib/postgresql/15/bin/postgres -D /var/lib/postgresql/15/main -C config_file

# 重新加载配置（不中断连接）
sudo systemctl reload postgresql

# 或完全重启
sudo systemctl restart postgresql

# 验证配置
sudo -u postgres psql -c "SHOW shared_buffers;"
sudo -u postgres psql -c "SHOW max_connections;"
```

---

## 5. 数据库备份策略

### 5.1 逻辑备份（pg_dump）

#### 5.1.1 完整备份脚本

```bash
#!/bin/bash
# /usr/local/bin/backup-postgres.sh

# 配置
DB_NAME="nautilus_production"
DB_USER="nautilus_user"
BACKUP_DIR="/var/backups/postgresql"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
echo "开始备份数据库: $DB_NAME"
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_FILE

# 检查备份是否成功
if [ $? -eq 0 ]; then
    echo "备份成功: $BACKUP_FILE"

    # 删除旧备份
    find $BACKUP_DIR -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "已删除 $RETENTION_DAYS 天前的旧备份"

    # 记录备份大小
    BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
    echo "备份大小: $BACKUP_SIZE"
else
    echo "备份失败！"
    exit 1
fi
```

#### 5.1.2 设置定时备份

```bash
# 添加执行权限
sudo chmod +x /usr/local/bin/backup-postgres.sh

# 编辑 crontab
sudo crontab -e

# 添加定时任务（每天凌晨 2 点执行）
0 2 * * * /usr/local/bin/backup-postgres.sh >> /var/log/postgres-backup.log 2>&1
```

### 5.2 物理备份（pg_basebackup）

```bash
#!/bin/bash
# 物理备份脚本

BACKUP_DIR="/var/backups/postgresql/basebackup"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

pg_basebackup -h localhost -U replicator \
  -D ${BACKUP_DIR}/${DATE} \
  -Ft -z -Xs -P

echo "物理备份完成: ${BACKUP_DIR}/${DATE}"
```

### 5.3 连续归档和时间点恢复（PITR）

#### 5.3.1 配置 WAL 归档

在 `postgresql.conf` 中添加：

```conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f'
archive_timeout = 300
```

创建归档目录：

```bash
sudo mkdir -p /var/lib/postgresql/wal_archive
sudo chown postgres:postgres /var/lib/postgresql/wal_archive
sudo chmod 700 /var/lib/postgresql/wal_archive
```

#### 5.3.2 基础备份

```bash
# 创建基础备份
pg_basebackup -h localhost -U replicator \
  -D /var/backups/postgresql/base_backup \
  -Ft -z -Xs -P
```

#### 5.3.3 恢复到特定时间点

```bash
# 1. 停止 PostgreSQL
sudo systemctl stop postgresql

# 2. 清空数据目录
sudo rm -rf /var/lib/postgresql/15/main/*

# 3. 恢复基础备份
sudo tar -xzf /var/backups/postgresql/base_backup/base.tar.gz \
  -C /var/lib/postgresql/15/main/

# 4. 创建 recovery.conf
sudo tee /var/lib/postgresql/15/main/recovery.signal << EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2026-02-26 12:00:00'
EOF

# 5. 启动 PostgreSQL
sudo systemctl start postgresql
```

### 5.4 备份到 S3（AWS）

```bash
#!/bin/bash
# 备份到 S3

DB_NAME="nautilus_production"
S3_BUCKET="s3://nautilus-backups"
DATE=$(date +%Y%m%d_%H%M%S)
TEMP_FILE="/tmp/${DB_NAME}_${DATE}.sql.gz"

# 创建备份
pg_dump -U nautilus_user $DB_NAME | gzip > $TEMP_FILE

# 上传到 S3
aws s3 cp $TEMP_FILE ${S3_BUCKET}/postgresql/${DB_NAME}_${DATE}.sql.gz

# 删除临时文件
rm $TEMP_FILE

# 设置生命周期（保留 30 天）
aws s3api put-object-lifecycle-configuration \
  --bucket nautilus-backups \
  --lifecycle-configuration file://lifecycle.json
```

lifecycle.json:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldBackups",
      "Status": "Enabled",
      "Prefix": "postgresql/",
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

### 5.5 备份验证

```bash
#!/bin/bash
# 验证备份完整性

BACKUP_FILE="/var/backups/postgresql/nautilus_production_20260226_020000.sql.gz"

# 解压并尝试恢复到测试数据库
gunzip -c $BACKUP_FILE | psql -U postgres -d test_restore

if [ $? -eq 0 ]; then
    echo "备份验证成功"
    # 删除测试数据库
    psql -U postgres -c "DROP DATABASE test_restore;"
else
    echo "备份验证失败！"
    exit 1
fi
```

---

## 6. 高可用配置

### 6.1 主从复制（Streaming Replication）

#### 6.1.1 主服务器配置

在主服务器的 `postgresql.conf`:

```conf
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB
```

创建复制用户：

```sql
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'ReplicatorPassword123!';
```

在 `pg_hba.conf` 添加：

```conf
host    replication     replicator      10.0.0.0/8              scram-sha-256
```

重启主服务器：

```bash
sudo systemctl restart postgresql
```

#### 6.1.2 从服务器配置

在从服务器上：

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

#### 6.1.3 验证复制状态

在主服务器上：

```sql
-- 查看复制状态
SELECT * FROM pg_stat_replication;

-- 查看复制延迟
SELECT
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    sync_state,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replication_lag_bytes
FROM pg_stat_replication;
```

在从服务器上：

```sql
-- 确认是否为从服务器
SELECT pg_is_in_recovery();

-- 查看复制延迟
SELECT
    now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

### 6.2 自动故障转移（使用 Patroni）

#### 6.2.1 安装 Patroni

```bash
# 安装依赖
sudo apt install python3-pip python3-dev libpq-dev -y

# 安装 Patroni
sudo pip3 install patroni[etcd]

# 安装 etcd
sudo apt install etcd -y
```

#### 6.2.2 配置 Patroni

创建 `/etc/patroni/patroni.yml`:

```yaml
scope: nautilus-cluster
namespace: /db/
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.1.10:8008

etcd:
  host: 10.0.1.20:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 200
        shared_buffers: 4GB

  initdb:
    - encoding: UTF8
    - data-checksums

  pg_hba:
    - host replication replicator 0.0.0.0/0 md5
    - host all all 0.0.0.0/0 md5

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.1.10:5432
  data_dir: /var/lib/postgresql/15/main
  bin_dir: /usr/lib/postgresql/15/bin
  authentication:
    replication:
      username: replicator
      password: ReplicatorPassword123!
    superuser:
      username: postgres
      password: PostgresPassword123!

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  nosync: false
```

#### 6.2.3 启动 Patroni

```bash
# 创建 systemd 服务
sudo tee /etc/systemd/system/patroni.service << EOF
[Unit]
Description=Patroni PostgreSQL Cluster Manager
After=syslog.target network.target

[Service]
Type=simple
User=postgres
Group=postgres
ExecStart=/usr/local/bin/patroni /etc/patroni/patroni.yml
KillMode=process
TimeoutSec=30
Restart=no

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable patroni
sudo systemctl start patroni

# 查看状态
patronictl -c /etc/patroni/patroni.yml list
```

### 6.3 连接池（PgBouncer）

#### 6.3.1 安装 PgBouncer

```bash
sudo apt install pgbouncer -y
```

#### 6.3.2 配置 PgBouncer

编辑 `/etc/pgbouncer/pgbouncer.ini`:

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
reserve_pool_timeout = 3
max_db_connections = 100
max_user_connections = 100
server_idle_timeout = 600
server_lifetime = 3600
server_connect_timeout = 15
query_timeout = 0
query_wait_timeout = 120
client_idle_timeout = 0
idle_transaction_timeout = 0
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

创建用户列表 `/etc/pgbouncer/userlist.txt`:

```
"nautilus_user" "SCRAM-SHA-256$..."
```

生成密码哈希：

```bash
# 在 PostgreSQL 中获取密码哈希
psql -U postgres -c "SELECT rolpassword FROM pg_authid WHERE rolname='nautilus_user';"
```

启动 PgBouncer:

```bash
sudo systemctl enable pgbouncer
sudo systemctl start pgbouncer
```

应用连接字符串改为：

```
postgresql://nautilus_user:password@localhost:6432/nautilus_production
```

---

## 7. 性能优化

### 7.1 创建索引

```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

-- 复合索引
CREATE INDEX idx_tasks_status_created ON tasks(status, created_at);

-- 部分索引（仅索引活跃记录）
CREATE INDEX idx_active_tasks ON tasks(id) WHERE status = 'active';

-- 表达式索引
CREATE INDEX idx_users_lower_email ON users(LOWER(email));

-- 查看索引使用情况
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 查找未使用的索引
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE 'pg_toast%';
```

### 7.2 查询优化

```sql
-- 启用 pg_stat_statements
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

-- 分析查询计划
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'user@example.com';

-- 查看表统计信息
ANALYZE users;

-- 查看表膨胀
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

### 7.3 VACUUM 和 ANALYZE

```sql
-- 手动 VACUUM
VACUUM ANALYZE users;

-- VACUUM FULL（锁表，谨慎使用）
VACUUM FULL users;

-- 查看自动 VACUUM 状态
SELECT
    schemaname,
    tablename,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables;
```

### 7.4 分区表（大表优化）

```sql
-- 创建分区表（按日期分区）
CREATE TABLE tasks_partitioned (
    id BIGSERIAL,
    title VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE tasks_2026_01 PARTITION OF tasks_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE tasks_2026_02 PARTITION OF tasks_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- 自动创建分区（使用 pg_partman 扩展）
CREATE EXTENSION pg_partman;

SELECT create_parent(
    'public.tasks_partitioned',
    'created_at',
    'native',
    'monthly'
);
```

---

## 8. 监控和维护

### 8.1 监控脚本

```bash
#!/bin/bash
# /usr/local/bin/monitor-postgres.sh

# 检查连接数
CONNECTIONS=$(psql -U postgres -t -c "SELECT count(*) FROM pg_stat_activity;")
echo "当前连接数: $CONNECTIONS"

# 检查数据库大小
psql -U postgres -c "
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;
"

# 检查复制延迟
psql -U postgres -c "
SELECT
    client_addr,
    state,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
FROM pg_stat_replication;
"

# 检查长时间运行的查询
psql -U postgres -c "
SELECT
    pid,
    now() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
AND now() - query_start > interval '5 minutes'
ORDER BY duration DESC;
"
```

### 8.2 性能监控查询

```sql
-- 数据库连接统计
SELECT
    datname,
    count(*) AS connections,
    max(state) AS state
FROM pg_stat_activity
GROUP BY datname;

-- 锁等待
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- 缓存命中率
SELECT
    sum(heap_blks_read) AS heap_read,
    sum(heap_blks_hit) AS heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS cache_hit_ratio
FROM pg_statio_user_tables;
```

---

## 9. 故障排查

### 9.1 常见问题

#### 问题1: 连接数过多

```sql
-- 查看当前连接
SELECT * FROM pg_stat_activity;

-- 终止空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '1 hour';
```

#### 问题2: 磁盘空间不足

```bash
# 查看数据库大小
du -sh /var/lib/postgresql/15/main

# 清理 WAL 日志
pg_archivecleanup /var/lib/postgresql/15/main/pg_wal 000000010000000000000010

# VACUUM FULL 回收空间
psql -U postgres -d nautilus_production -c "VACUUM FULL;"
```

#### 问题3: 性能下降

```sql
-- 更新统计信息
ANALYZE;

-- 重建索引
REINDEX DATABASE nautilus_production;

-- 检查膨胀
SELECT * FROM pgstattuple('users');
```

---

## 10. 相关文档

- [生产环境部署计划](PRODUCTION_DEPLOYMENT_PLAN.md)
- [生产环境检查清单](PRODUCTION_READINESS_CHECKLIST.md)
- [云服务部署指南](CLOUD_DEPLOYMENT_GUIDE.md)

---

**文档结束**

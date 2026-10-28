# 生产数据库配置快速参考

## 快速命令

### 数据库初始化
```bash
# 设置环境变量
export DB_NAME="nautilus_production"
export DB_USER="nautilus_user"
export DB_PASSWORD="your_secure_password"

# 执行初始化
./scripts/init_production_db.sh
```

### 备份操作
```bash
# 逻辑备份
./scripts/backup_database.sh --type logical

# 物理备份
./scripts/backup_database.sh --type physical

# 完整备份（逻辑+物理）
./scripts/backup_database.sh --type both

# 备份到 S3
./scripts/backup_database.sh --type logical --s3-bucket my-bucket
```

### 备份验证
```bash
# 验证备份文件
./scripts/verify_backup.sh /var/backups/postgresql/backup.sql.gz

# 验证并保留测试数据库
./scripts/verify_backup.sh backup.sql.gz --no-cleanup
```

### 数据恢复
```bash
# 创建新数据库
./scripts/restore_database.sh backup.sql.gz new_database --mode create

# 替换现有数据库
./scripts/restore_database.sh backup.sql.gz nautilus_production --mode replace

# 合并到现有数据库
./scripts/restore_database.sh backup.sql.gz nautilus_production --mode merge
```

### 性能监控
```bash
# 执行性能检查
./scripts/monitor_performance.sh

# 查看报告
cat /var/log/postgresql/performance/performance_report_*.txt
```

### 索引管理
```bash
# 创建所有索引
psql -U nautilus_user -d nautilus_production -f scripts/create_indexes.sql

# 重建索引
psql -U nautilus_user -d nautilus_production -c "REINDEX DATABASE nautilus_production;"
```

---

## 常用 SQL 查询

### 连接管理
```sql
-- 查看当前连接
SELECT * FROM pg_stat_activity;

-- 查看连接数统计
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

-- 终止空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND state_change < now() - interval '1 hour';

-- 终止特定用户的连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE usename = 'username';
```

### 性能分析
```sql
-- 查看缓存命中率
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    round(sum(heap_blks_hit) * 100.0 / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) as cache_hit_ratio
FROM pg_statio_user_tables;

-- 查看最慢的查询
SELECT
    substring(query, 1, 100) as query,
    calls,
    round(total_exec_time::numeric, 2) as total_time,
    round(mean_exec_time::numeric, 2) as avg_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 查看表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 索引管理
```sql
-- 查看索引使用情况
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 查找未使用的索引
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE 'pg_toast%';

-- 查看索引膨胀
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 表维护
```sql
-- 查看表膨胀
SELECT
    schemaname,
    tablename,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;

-- 手动 VACUUM
VACUUM ANALYZE tablename;

-- VACUUM 所有表
VACUUM ANALYZE;

-- 查看 VACUUM 历史
SELECT
    schemaname,
    tablename,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables;
```

### 锁监控
```sql
-- 查看当前锁
SELECT
    locktype,
    database,
    relation::regclass,
    mode,
    granted
FROM pg_locks
WHERE NOT granted;

-- 查看阻塞查询
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
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### 复制监控
```sql
-- 查看复制状态（主服务器）
SELECT * FROM pg_stat_replication;

-- 查看复制延迟
SELECT
    client_addr,
    state,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
    pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) AS lag_size
FROM pg_stat_replication;

-- 检查是否为从服务器
SELECT pg_is_in_recovery();

-- 查看复制延迟（从服务器）
SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

---

## 配置参数

### 内存配置（16GB RAM）
```conf
shared_buffers = 4GB                    # 25% 系统内存
effective_cache_size = 12GB             # 75% 系统内存
maintenance_work_mem = 1GB              # 维护操作
work_mem = 20MB                         # 每个查询操作
```

### 连接配置
```conf
max_connections = 200                   # 最大连接数
superuser_reserved_connections = 3      # 超级用户保留连接
```

### WAL 配置
```conf
wal_level = replica                     # 支持复制
wal_buffers = 16MB                      # WAL 缓冲区
min_wal_size = 1GB                      # 最小 WAL 大小
max_wal_size = 4GB                      # 最大 WAL 大小
checkpoint_completion_target = 0.9      # 检查点完成目标
```

### 查询优化
```conf
random_page_cost = 1.1                  # SSD 优化
effective_io_concurrency = 200          # SSD 并发 I/O
default_statistics_target = 100         # 统计信息采样
```

### 日志配置
```conf
log_min_duration_statement = 1000       # 记录超过 1 秒的查询
log_connections = on                    # 记录连接
log_disconnections = on                 # 记录断开
log_checkpoints = on                    # 记录检查点
log_lock_waits = on                     # 记录锁等待
```

---

## 定时任务配置

### Crontab 示例
```bash
# 编辑 crontab
crontab -e

# 每天凌晨2点执行逻辑备份
0 2 * * * /path/to/scripts/backup_database.sh --type logical >> /var/log/backup.log 2>&1

# 每周日凌晨3点执行物理备份
0 3 * * 0 /path/to/scripts/backup_database.sh --type physical >> /var/log/backup.log 2>&1

# 每小时执行性能监控
0 * * * * /path/to/scripts/monitor_performance.sh >> /var/log/performance.log 2>&1

# 每天凌晨4点执行 ANALYZE
0 4 * * * psql -U postgres -d nautilus_production -c "ANALYZE;" >> /var/log/maintenance.log 2>&1

# 每周一凌晨5点执行 VACUUM
0 5 * * 1 psql -U postgres -d nautilus_production -c "VACUUM ANALYZE;" >> /var/log/maintenance.log 2>&1

# 每月1号凌晨6点执行 REINDEX
0 6 1 * * psql -U postgres -d nautilus_production -c "REINDEX DATABASE nautilus_production;" >> /var/log/maintenance.log 2>&1
```

---

## 环境变量

### 必需变量
```bash
export DB_NAME="nautilus_production"
export DB_USER="nautilus_user"
export DB_PASSWORD="your_secure_password"
export DB_HOST="localhost"
export DB_PORT="5432"
```

### 可选变量
```bash
export DB_READONLY_USER="nautilus_readonly"
export DB_READONLY_PASSWORD="readonly_password"
export REPLICATION_USER="replicator"
export REPLICATION_PASSWORD="replication_password"
export BACKUP_DIR="/var/backups/postgresql"
export RETENTION_DAYS="30"
export S3_BUCKET="nautilus-backups"
export NOTIFICATION_EMAIL="admin@example.com"
```

---

## 故障排查清单

### 连接问题
- [ ] 检查 PostgreSQL 服务状态
- [ ] 检查端口是否开放
- [ ] 检查 pg_hba.conf 配置
- [ ] 检查防火墙规则
- [ ] 检查连接数是否达到上限

### 性能问题
- [ ] 检查缓存命中率
- [ ] 检查慢查询日志
- [ ] 检查表膨胀情况
- [ ] 检查索引使用情况
- [ ] 检查系统资源使用

### 磁盘空间问题
- [ ] 检查数据目录大小
- [ ] 检查 WAL 日志大小
- [ ] 清理旧备份文件
- [ ] 执行 VACUUM FULL
- [ ] 检查临时文件

### 复制问题
- [ ] 检查复制状态
- [ ] 检查复制延迟
- [ ] 检查 WAL 发送进程
- [ ] 检查网络连接
- [ ] 检查复制槽状态

---

## 安全检查清单

### 网络安全
- [ ] 限制监听地址
- [ ] 配置防火墙规则
- [ ] 启用 SSL/TLS
- [ ] 使用 VPN 或专用网络

### 认证安全
- [ ] 使用强密码
- [ ] 启用 SCRAM-SHA-256
- [ ] 定期更换密码
- [ ] 限制登录尝试次数

### 权限安全
- [ ] 最小权限原则
- [ ] 定期审查权限
- [ ] 撤销不必要的权限
- [ ] 使用角色管理权限

### 审计安全
- [ ] 启用详细日志
- [ ] 记录所有 DDL 操作
- [ ] 监控异常活动
- [ ] 定期审查日志

---

## 性能优化清单

### 查询优化
- [ ] 创建适当的索引
- [ ] 优化慢查询
- [ ] 使用 EXPLAIN ANALYZE
- [ ] 更新统计信息

### 配置优化
- [ ] 调整内存参数
- [ ] 优化 WAL 配置
- [ ] 配置连接池
- [ ] 启用并行查询

### 维护优化
- [ ] 定期执行 VACUUM
- [ ] 定期执行 ANALYZE
- [ ] 定期重建索引
- [ ] 清理死元组

### 硬件优化
- [ ] 使用 SSD 存储
- [ ] 增加内存
- [ ] 使用多核 CPU
- [ ] 优化网络带宽

---

## 监控指标

### 关键指标
| 指标 | 目标值 | 告警阈值 |
|-----|--------|---------|
| 缓存命中率 | > 95% | < 90% |
| 查询响应时间 | < 100ms | > 1s |
| 连接数 | < 160 | > 180 |
| 复制延迟 | < 1s | > 5s |
| 磁盘使用率 | < 80% | > 85% |
| 表膨胀率 | < 20% | > 30% |

---

## 联系信息

### 技术支持
- **DBA 团队**: dba@example.com
- **运维团队**: ops@example.com
- **紧急联系**: +86-xxx-xxxx-xxxx

### 相关文档
- [PRODUCTION_DATABASE_SETUP.md](PRODUCTION_DATABASE_SETUP.md)
- [PRODUCTION_DATABASE_GUIDE.md](PRODUCTION_DATABASE_GUIDE.md)
- [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md)

---

**最后更新**: 2026-02-27

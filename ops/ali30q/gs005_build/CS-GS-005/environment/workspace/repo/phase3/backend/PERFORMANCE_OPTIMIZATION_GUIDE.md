# Nautilus API 性能优化实施指南

## 概述

本指南提供了将 Nautilus API 响应时间从 850ms 优化到 <300ms 的完整步骤。

## 优化内容

### 1. 数据库索引优化 (预计提升 40-60%)

**已创建的索引:**
- `idx_agents_reputation_desc` - 优化按声誉排序
- `idx_agents_created_at` - 优化按创建时间排序
- `idx_tasks_status_created` - 优化任务状态和时间查询
- `idx_tasks_agent_status` - 优化 agent 任务查询
- `idx_tasks_publisher_status` - 优化发布者任务查询
- `idx_rewards_agent_status` - 优化奖励查询

### 2. 数据库连接池优化 (预计提升 10-20%)

**配置更新:**
```python
pool_size=20        # 从 10 增加到 20
max_overflow=40     # 从 20 增加到 40
```

### 3. API 响应压缩 (预计提升 20-30%)

**已添加 Gzip 中间件:**
```python
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 4. 缓存系统 (预计提升 30-50%)

**已启用 Redis:**
- 配置: `REDIS_URL=redis://localhost:6379/0`
- 缓存端点: `/api/agents`, `/api/agents/{id}`, `/api/agents/{id}/reputation`
- TTL: 60-300 秒

### 5. 代码优化

**已优化的文件:**
- `api/agents_optimized.py` - 添加缓存支持的 agents API
- `main.py` - 添加 Gzip 压缩中间件
- `utils/database.py` - 增加连接池大小

## 实施步骤

### 方式一: 自动化脚本 (推荐)

```bash
cd backend
python scripts/optimize_performance.py
```

### 方式二: 手动执行

#### 步骤 1: 应用数据库索引

```bash
cd backend
python scripts/apply_performance_indexes.py
```

#### 步骤 2: 验证索引创建

```bash
psql -U postgres -d nautilus -c "
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
"
```

#### 步骤 3: 更新环境变量

确保 `.env` 文件包含以下配置:

```bash
# 数据库连接池
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis 缓存
REDIS_URL=redis://localhost:6379/0
```

#### 步骤 4: 重启服务

```bash
# 停止当前服务 (Ctrl+C)
# 重新启动
uvicorn main:app --reload
```

#### 步骤 5: 运行性能测试

```bash
python scripts/benchmark_performance.py
```

## 性能监控

### 查看缓存统计

```bash
curl http://localhost:8000/cache/stats
```

**预期输出:**
```json
{
  "cache": {
    "hits": 1250,
    "misses": 150,
    "hit_rate": "89.29%",
    "size": 45
  },
  "status": "ok"
}
```

### 查看性能统计

```bash
curl http://localhost:8000/performance/stats
```

**预期输出:**
```json
{
  "stats": [
    {
      "endpoint": "/api/agents",
      "method": "GET",
      "count": 1500,
      "avg_time": 0.125,
      "min_time": 0.050,
      "max_time": 0.450
    }
  ],
  "total_requests": 5000
}
```

### 查看数据库连接池

```bash
curl http://localhost:8000/database/pool
```

**预期输出:**
```json
{
  "pool": {
    "size": 20,
    "checked_out": 5,
    "overflow": 0,
    "queue_size": 0,
    "utilization": 0.25
  },
  "status": "ok"
}
```

## 性能基准

### 优化前

| 指标 | 值 |
|------|-----|
| API 响应时间 | 850ms |
| 数据库查询 | 150ms |
| 缓存命中率 | 0% |
| 并发能力 | 50 |

### 优化后 (预期)

| 指标 | 值 | 提升 |
|------|-----|------|
| API 响应时间 | <300ms | 65% |
| 数据库查询 | <50ms | 67% |
| 缓存命中率 | >80% | - |
| 并发能力 | 100+ | 100% |

## 压力测试

### 使用 Apache Bench

```bash
# 测试 agents 列表端点
ab -n 1000 -c 10 http://localhost:8000/api/agents

# 测试健康检查端点
ab -n 1000 -c 50 http://localhost:8000/health
```

### 使用 wrk

```bash
# 30秒压力测试，4个线程，100个连接
wrk -t4 -c100 -d30s http://localhost:8000/api/agents
```

## 故障排查

### 问题 1: 索引创建失败

**症状:** `apply_performance_indexes.py` 报错

**解决方案:**
```bash
# 检查数据库连接
psql -U postgres -d nautilus -c "SELECT version();"

# 手动执行 SQL
psql -U postgres -d nautilus -f migrations/add_performance_indexes.sql
```

### 问题 2: Redis 连接失败

**症状:** 日志显示 "Redis connection failed"

**解决方案:**
```bash
# 检查 Redis 是否运行
redis-cli ping

# 如果未运行，启动 Redis
redis-server

# 或者禁用 Redis (注释 .env 中的 REDIS_URL)
```

### 问题 3: 性能未提升

**检查清单:**
1. 确认索引已创建: `SELECT * FROM pg_indexes WHERE indexname LIKE 'idx_%';`
2. 确认服务已重启
3. 检查缓存命中率: `curl http://localhost:8000/cache/stats`
4. 查看慢查询日志
5. 检查数据库连接池利用率

## 进一步优化建议

### 1. 查询优化

使用 `EXPLAIN ANALYZE` 分析慢查询:

```sql
EXPLAIN ANALYZE
SELECT * FROM agents
ORDER BY reputation DESC
LIMIT 10;
```

### 2. 数据库配置

优化 PostgreSQL 配置 (`postgresql.conf`):

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 3. 应用层优化

- 使用 `joinedload` 避免 N+1 查询
- 实现查询结果分页
- 添加 API 响应字段过滤
- 使用异步数据库驱动 (asyncpg)

### 4. 基础设施优化

- 使用 Nginx 作为反向代理
- 启用 HTTP/2
- 配置 CDN 加速静态资源
- 使用负载均衡器

## 监控和告警

### 关键指标

1. **响应时间**: P50, P95, P99
2. **错误率**: 4xx, 5xx 错误比例
3. **吞吐量**: 请求/秒
4. **数据库**: 连接池利用率、慢查询数量
5. **缓存**: 命中率、内存使用

### 告警阈值

- API 响应时间 P95 > 500ms
- 错误率 > 1%
- 数据库连接池利用率 > 80%
- 缓存命中率 < 70%

## 总结

通过以上优化，Nautilus API 的性能应该有显著提升。持续监控关键指标，根据实际负载调整配置参数。

如有问题，请查看日志文件或联系开发团队。

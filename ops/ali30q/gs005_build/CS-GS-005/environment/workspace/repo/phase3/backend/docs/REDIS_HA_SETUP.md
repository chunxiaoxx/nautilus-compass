# Redis 高可用配置指南

## 概述

本文档介绍如何为 Nautilus API 配置 Redis 高可用方案，包括 Redis Sentinel 和 Redis Cluster 两种方案。

## 方案选择

### Redis Sentinel (推荐用于中小规模)

**优点**：
- 配置简单
- 自动故障转移
- 适合单主多从架构
- 资源占用少

**适用场景**：
- 单个 Redis 实例可满足性能需求
- 需要高可用但不需要水平扩展
- 数据量 < 100GB

### Redis Cluster (推荐用于大规模)

**优点**：
- 数据自动分片
- 水平扩展能力
- 高吞吐量

**适用场景**：
- 需要水平扩展
- 数据量 > 100GB
- 高并发场景

## Redis Sentinel 配置

### 1. 架构设计

```
┌─────────────┐
│   Master    │ :6379
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌──▼──┐
│Slave│ │Slave│ :6380, :6381
└─────┘ └─────┘
   │       │
┌──▼───────▼──┐
│  Sentinel   │ :26379, :26380, :26381
│   (x3)      │
└─────────────┘
```

### 2. Docker Compose 配置

创建 `docker-compose.redis-sentinel.yml`:

```yaml
version: '3.8'

services:
  redis-master:
    image: redis:7.4.7-alpine
    container_name: redis-master
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis-master-data:/data
    networks:
      - redis-network
    restart: unless-stopped

  redis-slave-1:
    image: redis:7.4.7-alpine
    container_name: redis-slave-1
    command: redis-server --appendonly yes --slaveof redis-master 6379 --masterauth ${REDIS_PASSWORD} --requirepass ${REDIS_PASSWORD}
    ports:
      - "6380:6379"
    volumes:
      - redis-slave-1-data:/data
    networks:
      - redis-network
    depends_on:
      - redis-master
    restart: unless-stopped

  redis-slave-2:
    image: redis:7.4.7-alpine
    container_name: redis-slave-2
    command: redis-server --appendonly yes --slaveof redis-master 6379 --masterauth ${REDIS_PASSWORD} --requirepass ${REDIS_PASSWORD}
    ports:
      - "6381:6379"
    volumes:
      - redis-slave-2-data:/data
    networks:
      - redis-network
    depends_on:
      - redis-master
    restart: unless-stopped

  redis-sentinel-1:
    image: redis:7.4.7-alpine
    container_name: redis-sentinel-1
    command: redis-sentinel /etc/redis/sentinel.conf
    ports:
      - "26379:26379"
    volumes:
      - ./redis-sentinel-1.conf:/etc/redis/sentinel.conf
    networks:
      - redis-network
    depends_on:
      - redis-master
      - redis-slave-1
      - redis-slave-2
    restart: unless-stopped

  redis-sentinel-2:
    image: redis:7.4.7-alpine
    container_name: redis-sentinel-2
    command: redis-sentinel /etc/redis/sentinel.conf
    ports:
      - "26380:26379"
    volumes:
      - ./redis-sentinel-2.conf:/etc/redis/sentinel.conf
    networks:
      - redis-network
    depends_on:
      - redis-master
      - redis-slave-1
      - redis-slave-2
    restart: unless-stopped

  redis-sentinel-3:
    image: redis:7.4.7-alpine
    container_name: redis-sentinel-3
    command: redis-sentinel /etc/redis/sentinel.conf
    ports:
      - "26381:26379"
    volumes:
      - ./redis-sentinel-3.conf:/etc/redis/sentinel.conf
    networks:
      - redis-network
    depends_on:
      - redis-master
      - redis-slave-1
      - redis-slave-2
    restart: unless-stopped

volumes:
  redis-master-data:
  redis-slave-1-data:
  redis-slave-2-data:

networks:
  redis-network:
    driver: bridge
```

### 3. Sentinel 配置文件

创建 `redis-sentinel-1.conf` (其他 sentinel 配置类似):

```conf
port 26379
dir /tmp
sentinel monitor mymaster redis-master 6379 2
sentinel auth-pass mymaster ${REDIS_PASSWORD}
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
```

### 4. 应用代码集成

更新 `backend/utils/cache.py`:

```python
# Global cache instance - use Redis Sentinel if available
try:
    import redis
    from redis.sentinel import Sentinel
    import os
    from dotenv import load_dotenv
    load_dotenv()

    # Check if Sentinel is configured
    sentinel_hosts = os.getenv('REDIS_SENTINEL_HOSTS', '')

    if sentinel_hosts:
        # Parse sentinel hosts: "host1:port1,host2:port2,host3:port3"
        sentinel_list = [
            (host.split(':')[0], int(host.split(':')[1]))
            for host in sentinel_hosts.split(',')
        ]

        sentinel = Sentinel(
            sentinel_list,
            socket_timeout=2,
            password=os.getenv('REDIS_PASSWORD')
        )

        # Get master connection
        master_name = os.getenv('REDIS_SENTINEL_MASTER', 'mymaster')
        _redis_client = sentinel.master_for(
            master_name,
            socket_timeout=2,
            decode_responses=True
        )

        _redis_client.ping()
        _use_redis = True
        logger.info(f"Using Redis Sentinel (master: {master_name})")
    else:
        # Fallback to direct connection
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        _redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
        _redis_client.ping()
        _use_redis = True
        logger.info("Using Redis direct connection")

except Exception as e:
    _redis_client = None
    _use_redis = False
    logger.warning(f"Redis unavailable, using in-memory cache: {e}")
```

### 5. 环境变量配置

更新 `.env.production`:

```bash
# Redis Sentinel Configuration
REDIS_SENTINEL_HOSTS=localhost:26379,localhost:26380,localhost:26381
REDIS_SENTINEL_MASTER=mymaster
REDIS_PASSWORD=your_strong_password_here
```

### 6. 启动和测试

```bash
# 启动 Redis Sentinel 集群
docker-compose -f docker-compose.redis-sentinel.yml up -d

# 检查状态
docker exec redis-sentinel-1 redis-cli -p 26379 sentinel master mymaster

# 测试故障转移
docker stop redis-master

# 观察 Sentinel 日志
docker logs -f redis-sentinel-1

# 验证新 master
docker exec redis-sentinel-1 redis-cli -p 26379 sentinel get-master-addr-by-name mymaster
```

## Redis Cluster 配置

### 1. 架构设计

```
┌────────┐  ┌────────┐  ┌────────┐
│Master 1│  │Master 2│  │Master 3│
│  :7000 │  │  :7001 │  │  :7002 │
└───┬────┘  └───┬────┘  └───┬────┘
    │           │           │
┌───▼────┐  ┌───▼────┐  ┌───▼────┐
│Slave 1 │  │Slave 2 │  │Slave 3 │
│  :7003 │  │  :7004 │  │  :7005 │
└────────┘  └────────┘  └────────┘
```

### 2. Docker Compose 配置

创建 `docker-compose.redis-cluster.yml`:

```yaml
version: '3.8'

services:
  redis-node-1:
    image: redis:7.4.7-alpine
    container_name: redis-node-1
    command: redis-server /etc/redis/redis.conf
    ports:
      - "7000:7000"
      - "17000:17000"
    volumes:
      - ./redis-cluster-node-1.conf:/etc/redis/redis.conf
      - redis-node-1-data:/data
    networks:
      - redis-cluster-network
    restart: unless-stopped

  redis-node-2:
    image: redis:7.4.7-alpine
    container_name: redis-node-2
    command: redis-server /etc/redis/redis.conf
    ports:
      - "7001:7001"
      - "17001:17001"
    volumes:
      - ./redis-cluster-node-2.conf:/etc/redis/redis.conf
      - redis-node-2-data:/data
    networks:
      - redis-cluster-network
    restart: unless-stopped

  redis-node-3:
    image: redis:7.4.7-alpine
    container_name: redis-node-3
    command: redis-server /etc/redis/redis.conf
    ports:
      - "7002:7002"
      - "17002:17002"
    volumes:
      - ./redis-cluster-node-3.conf:/etc/redis/redis.conf
      - redis-node-3-data:/data
    networks:
      - redis-cluster-network
    restart: unless-stopped

  redis-node-4:
    image: redis:7.4.7-alpine
    container_name: redis-node-4
    command: redis-server /etc/redis/redis.conf
    ports:
      - "7003:7003"
      - "17003:17003"
    volumes:
      - ./redis-cluster-node-4.conf:/etc/redis/redis.conf
      - redis-node-4-data:/data
    networks:
      - redis-cluster-network
    restart: unless-stopped

  redis-node-5:
    image: redis:7.4.7-alpine
    container_name: redis-node-5
    command: redis-server /etc/redis/redis.conf
    ports:
      - "7004:7004"
      - "17004:17004"
    volumes:
      - ./redis-cluster-node-5.conf:/etc/redis/redis.conf
      - redis-node-5-data:/data
    networks:
      - redis-cluster-network
    restart: unless-stopped

  redis-node-6:
    image: redis:7.4.7-alpine
    container_name: redis-node-6
    command: redis-server /etc/redis/redis.conf
    ports:
      - "7005:7005"
      - "17005:17005"
    volumes:
      - ./redis-cluster-node-6.conf:/etc/redis/redis.conf
      - redis-node-6-data:/data
    networks:
      - redis-cluster-network
    restart: unless-stopped

  redis-cluster-init:
    image: redis:7.4.7-alpine
    container_name: redis-cluster-init
    command: >
      sh -c "sleep 10 && redis-cli --cluster create
      redis-node-1:7000 redis-node-2:7001 redis-node-3:7002
      redis-node-4:7003 redis-node-5:7004 redis-node-6:7005
      --cluster-replicas 1 --cluster-yes"
    networks:
      - redis-cluster-network
    depends_on:
      - redis-node-1
      - redis-node-2
      - redis-node-3
      - redis-node-4
      - redis-node-5
      - redis-node-6

volumes:
  redis-node-1-data:
  redis-node-2-data:
  redis-node-3-data:
  redis-node-4-data:
  redis-node-5-data:
  redis-node-6-data:

networks:
  redis-cluster-network:
    driver: bridge
```

### 3. 节点配置文件

创建 `redis-cluster-node-1.conf` (其他节点配置类似，修改端口):

```conf
port 7000
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
requirepass ${REDIS_PASSWORD}
masterauth ${REDIS_PASSWORD}
```

### 4. 应用代码集成

更新 `backend/utils/cache.py`:

```python
from redis.cluster import RedisCluster

# Check if Cluster is configured
cluster_nodes = os.getenv('REDIS_CLUSTER_NODES', '')

if cluster_nodes:
    # Parse cluster nodes: "host1:port1,host2:port2,host3:port3"
    startup_nodes = [
        {"host": node.split(':')[0], "port": int(node.split(':')[1])}
        for node in cluster_nodes.split(',')
    ]

    _redis_client = RedisCluster(
        startup_nodes=startup_nodes,
        decode_responses=True,
        password=os.getenv('REDIS_PASSWORD'),
        socket_timeout=2
    )

    _redis_client.ping()
    _use_redis = True
    logger.info("Using Redis Cluster")
```

### 5. 环境变量配置

```bash
# Redis Cluster Configuration
REDIS_CLUSTER_NODES=localhost:7000,localhost:7001,localhost:7002
REDIS_PASSWORD=your_strong_password_here
```

## 缓存失效策略

### 1. TTL-based 失效 (已实现)

```python
# 设置 TTL
cache.set(key, value, ttl=300)  # 5分钟后自动失效
```

### 2. Pattern-based 失效

更新 `backend/utils/cache.py`:

```python
def invalidate_cache_pattern(pattern: str):
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "agents_list:*")
    """
    if _use_redis and _redis_client:
        try:
            # Use SCAN to avoid blocking
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = _redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    _redis_client.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted_count} cache entries matching '{pattern}'")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern '{pattern}': {e}")
            return 0
    else:
        # Fallback to memory cache
        keys_to_delete = [
            key for key in _cache._cache.keys()
            if key.startswith(pattern.replace('*', ''))
        ]
        for key in keys_to_delete:
            _cache.delete(key)
        logger.info(f"Invalidated {len(keys_to_delete)} memory cache entries")
        return len(keys_to_delete)
```

### 3. Event-driven 失效

在数据更新时自动失效相关缓存:

```python
# backend/services/agent_service.py

async def update_agent(agent_id: str, data: dict, db: Session):
    """Update agent and invalidate related cache."""
    # Update database
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")

    for key, value in data.items():
        setattr(agent, key, value)

    db.commit()
    db.refresh(agent)

    # Invalidate related cache
    from utils.cache import invalidate_cache_pattern
    invalidate_cache_pattern(f"agents_list:*")
    invalidate_cache_pattern(f"agent:{agent_id}:*")

    logger.info(f"Agent {agent_id} updated, cache invalidated")
    return agent
```

### 4. 缓存预热

在应用启动时预热常用数据:

```python
# backend/main.py

async def warmup_cache():
    """Warm up cache with frequently accessed data."""
    from services.agent_service import get_agents_list_cached
    from services.task_service import get_tasks_cached
    from utils.database import get_db

    logger.info("Starting cache warm-up...")
    db = next(get_db())

    try:
        # Warm up agents list
        await get_agents_list_cached(limit=50, offset=0, db=db)

        # Warm up tasks list
        await get_tasks_cached(status=None, limit=50, db=db)
        await get_tasks_cached(status="open", limit=50, db=db)

        logger.info("✅ Cache warm-up completed")
    except Exception as e:
        logger.warning(f"⚠️ Cache warm-up failed: {e}")
    finally:
        db.close()
```

## 健康检查

### 1. Redis 健康检查端点

更新 `backend/main.py`:

```python
@app.get("/health/redis")
async def redis_health():
    """Check Redis health status."""
    try:
        if _use_redis and _redis_client:
            # Test connection
            _redis_client.ping()

            # Get info
            info = _redis_client.info()

            return {
                "status": "healthy",
                "type": "redis",
                "version": info.get("redis_version"),
                "uptime_seconds": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "role": info.get("role")
            }
        else:
            return {
                "status": "unavailable",
                "type": "memory",
                "message": "Using in-memory cache"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### 2. Kubernetes Liveness/Readiness Probes

```yaml
# kubernetes/deployment.yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/redis
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

## 监控和告警

### 1. Redis 指标收集

```python
# backend/utils/metrics.py

redis_info_gauge = Gauge(
    'redis_info',
    'Redis server information',
    ['metric']
)

def collect_redis_metrics():
    """Collect Redis metrics for Prometheus."""
    if _use_redis and _redis_client:
        try:
            info = _redis_client.info()

            redis_info_gauge.labels(metric='connected_clients').set(
                info.get('connected_clients', 0)
            )
            redis_info_gauge.labels(metric='used_memory').set(
                info.get('used_memory', 0)
            )
            redis_info_gauge.labels(metric='keyspace_hits').set(
                info.get('keyspace_hits', 0)
            )
            redis_info_gauge.labels(metric='keyspace_misses').set(
                info.get('keyspace_misses', 0)
            )
        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
```

### 2. 告警规则

```yaml
# prometheus/alerts.yml
- alert: RedisDown
  expr: up{job="redis"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Redis instance is down"

- alert: RedisHighMemoryUsage
  expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Redis memory usage is above 90%"

- alert: RedisHighConnectionCount
  expr: redis_connected_clients > 1000
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Redis has too many connections"
```

## 最佳实践

1. **使用连接池**
   - 避免频繁创建/销毁连接
   - 设置合理的连接池大小

2. **设置合理的 TTL**
   - 根据数据更新频率设置
   - 避免缓存雪崩

3. **监控缓存命中率**
   - 目标: > 60%
   - 低于阈值时优化缓存策略

4. **定期清理过期数据**
   - 使用 Redis 的 EXPIRE 命令
   - 避免内存泄漏

5. **备份策略**
   - 启用 AOF 持久化
   - 定期备份 RDB 文件

6. **安全配置**
   - 使用强密码
   - 限制网络访问
   - 禁用危险命令

## 故障排查

### 常见问题

1. **连接超时**
   - 检查网络连接
   - 增加 socket_timeout
   - 检查 Redis 负载

2. **内存不足**
   - 增加 Redis 内存限制
   - 优化 TTL 设置
   - 清理过期数据

3. **主从同步延迟**
   - 检查网络带宽
   - 优化 repl-backlog-size
   - 减少写入频率

## 相关文档

- [Redis Sentinel 官方文档](https://redis.io/docs/management/sentinel/)
- [Redis Cluster 官方文档](https://redis.io/docs/management/scaling/)
- [Redis 最佳实践](https://redis.io/docs/management/optimization/)

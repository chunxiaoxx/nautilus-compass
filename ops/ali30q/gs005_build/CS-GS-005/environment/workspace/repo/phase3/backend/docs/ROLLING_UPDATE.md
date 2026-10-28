# 滚动更新部署指南

## 概述

本文档介绍如何为 Nautilus API 实施零停机滚动更新部署策略。

## 部署架构

### 负载均衡器 + 多实例

```
┌─────────────┐
│   Nginx     │ :80
│Load Balancer│
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
┌──▼──┐  ┌──▼──┐
│API 1│  │API 2│ :8000, :8001
└─────┘  └─────┘
   │        │
   └────┬───┘
        │
   ┌────▼────┐
   │Database │
   │  Redis  │
   └─────────┘
```

## Kubernetes 滚动更新

### 1. Deployment 配置

创建 `kubernetes/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nautilus-api
  labels:
    app: nautilus-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 最多额外创建1个Pod
      maxUnavailable: 0  # 保证至少3个Pod可用
  selector:
    matchLabels:
      app: nautilus-api
  template:
    metadata:
      labels:
        app: nautilus-api
        version: "{{ .Values.version }}"
    spec:
      containers:
      - name: api
        image: nautilus-api:{{ .Values.version }}
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: nautilus-secrets
              key: database-url
        - name: REDIS_SENTINEL_HOSTS
          value: "redis-sentinel-0:26379,redis-sentinel-1:26379,redis-sentinel-2:26379"
        - name: REDIS_SENTINEL_MASTER
          value: "mymaster"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: nautilus-secrets
              key: redis-password

        # 健康检查
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
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        # 优雅关闭
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]

        # 资源限制
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

      # 优雅终止时间
      terminationGracePeriodSeconds: 30
```

### 2. Service 配置

创建 `kubernetes/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nautilus-api
  labels:
    app: nautilus-api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: nautilus-api
  sessionAffinity: None
```

### 3. 部署命令

```bash
# 应用配置
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# 查看部署状态
kubectl rollout status deployment/nautilus-api

# 查看 Pod 状态
kubectl get pods -l app=nautilus-api

# 查看滚动更新历史
kubectl rollout history deployment/nautilus-api
```

### 4. 更新应用

```bash
# 更新镜像
kubectl set image deployment/nautilus-api api=nautilus-api:v2.0.0

# 或者编辑 deployment
kubectl edit deployment/nautilus-api

# 监控滚动更新过程
kubectl rollout status deployment/nautilus-api -w

# 如果出现问题，回滚
kubectl rollout undo deployment/nautilus-api

# 回滚到特定版本
kubectl rollout undo deployment/nautilus-api --to-revision=2
```

## Docker Compose 滚动更新

### 1. 配置文件

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api-1:
    image: nautilus-api:${VERSION}
    container_name: nautilus-api-1
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_SENTINEL_HOSTS=${REDIS_SENTINEL_HOSTS}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    restart: unless-stopped
    networks:
      - nautilus-network

  api-2:
    image: nautilus-api:${VERSION}
    container_name: nautilus-api-2
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_SENTINEL_HOSTS=${REDIS_SENTINEL_HOSTS}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    restart: unless-stopped
    networks:
      - nautilus-network

  nginx:
    image: nginx:alpine
    container_name: nautilus-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api-1
      - api-2
    restart: unless-stopped
    networks:
      - nautilus-network

networks:
  nautilus-network:
    driver: bridge
```

### 2. Nginx 配置

创建 `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream nautilus_api {
        least_conn;
        server api-1:8000 max_fails=3 fail_timeout=30s;
        server api-2:8000 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://nautilus_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 健康检查
            proxy_next_upstream error timeout http_500 http_502 http_503;
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /health {
            access_log off;
            proxy_pass http://nautilus_api/health;
        }
    }
}
```

### 3. 滚动更新脚本

创建 `scripts/rolling-update.sh`:

```bash
#!/bin/bash

set -e

# 配置
NEW_VERSION=$1
HEALTH_CHECK_URL="http://localhost:8000/health"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=2

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "🚀 Starting rolling update to version $NEW_VERSION"

# 函数：等待服务健康
wait_for_health() {
    local container=$1
    local port=$2
    local url="http://localhost:$port/health"

    echo "⏳ Waiting for $container to be healthy..."

    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo "✅ $container is healthy"
            return 0
        fi
        echo "   Attempt $i/$HEALTH_CHECK_RETRIES failed, retrying in ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
    done

    echo "❌ $container failed to become healthy"
    return 1
}

# 更新 api-1
echo ""
echo "📦 Updating api-1..."
docker-compose -f docker-compose.prod.yml stop api-1
docker-compose -f docker-compose.prod.yml rm -f api-1
VERSION=$NEW_VERSION docker-compose -f docker-compose.prod.yml up -d api-1

if ! wait_for_health "api-1" "8000"; then
    echo "❌ Rolling update failed at api-1"
    echo "🔄 Rolling back..."
    docker-compose -f docker-compose.prod.yml restart api-1
    exit 1
fi

# 等待一段时间确保稳定
echo "⏳ Waiting 10s for api-1 to stabilize..."
sleep 10

# 更新 api-2
echo ""
echo "📦 Updating api-2..."
docker-compose -f docker-compose.prod.yml stop api-2
docker-compose -f docker-compose.prod.yml rm -f api-2
VERSION=$NEW_VERSION docker-compose -f docker-compose.prod.yml up -d api-2

if ! wait_for_health "api-2" "8001"; then
    echo "❌ Rolling update failed at api-2"
    echo "🔄 Rolling back..."
    docker-compose -f docker-compose.prod.yml restart api-2
    exit 1
fi

echo ""
echo "✅ Rolling update completed successfully!"
echo "📊 Current status:"
docker-compose -f docker-compose.prod.yml ps
```

### 4. 执行滚动更新

```bash
# 赋予执行权限
chmod +x scripts/rolling-update.sh

# 执行更新
./scripts/rolling-update.sh v2.0.0
```

## 应用层优雅关闭

### 1. 更新 main.py

```python
import signal
import asyncio

# Global shutdown event
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Nautilus Phase 3 Backend...")
    init_db()

    # ... existing startup code ...

    yield

    # Shutdown
    logger.info("Shutting down Nautilus Phase 3 Backend...")

    # Wait for in-flight requests to complete (max 15s)
    logger.info("Waiting for in-flight requests to complete...")
    await asyncio.sleep(15)

    # Close database connections
    try:
        from utils.db_pool import close_db_pool
        await close_db_pool()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.warning(f"Error closing database pool: {e}")

    # Close Redis connections
    if _use_redis and _redis_client:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")

    logger.info("Shutdown complete")
```

### 2. Dockerfile 优化

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Graceful shutdown
STOPSIGNAL SIGTERM
```

## 监控和验证

### 1. 部署前检查清单

```bash
# 1. 运行测试
pytest --cov=. --cov-report=html

# 2. 构建镜像
docker build -t nautilus-api:v2.0.0 .

# 3. 本地测试
docker run -p 8000:8000 nautilus-api:v2.0.0

# 4. 健康检查
curl http://localhost:8000/health

# 5. 性能测试
python backend/tests/test_performance.py
```

### 2. 部署后验证

```bash
# 1. 检查所有 Pod 状态
kubectl get pods -l app=nautilus-api

# 2. 检查服务端点
kubectl get endpoints nautilus-api

# 3. 查看日志
kubectl logs -f deployment/nautilus-api

# 4. 测试 API
curl http://your-domain/health
curl http://your-domain/api/agents

# 5. 监控指标
curl http://your-domain/prometheus
```

### 3. 回滚计划

```bash
# Kubernetes 回滚
kubectl rollout undo deployment/nautilus-api

# Docker Compose 回滚
./scripts/rolling-update.sh v1.9.0

# 验证回滚
kubectl rollout status deployment/nautilus-api
```

## 最佳实践

1. **始终使用健康检查**
   - Liveness probe: 检测应用是否存活
   - Readiness probe: 检测应用是否就绪

2. **设置合理的超时时间**
   - terminationGracePeriodSeconds: 30s
   - preStop hook: 15s
   - 确保有足够时间完成请求

3. **使用版本标签**
   - 不要使用 `latest` 标签
   - 使用语义化版本号

4. **监控部署过程**
   - 实时查看日志
   - 监控错误率和响应时间
   - 准备好回滚计划

5. **分阶段部署**
   - 先部署到测试环境
   - 再部署到预生产环境
   - 最后部署到生产环境

6. **保持数据库兼容性**
   - 向后兼容的数据库迁移
   - 先部署代码，再运行迁移
   - 或使用蓝绿部署

## 故障排查

### 常见问题

1. **Pod 无法启动**
   - 检查镜像是否存在
   - 检查环境变量配置
   - 查看 Pod 日志

2. **健康检查失败**
   - 增加 initialDelaySeconds
   - 检查健康检查端点
   - 查看应用日志

3. **滚动更新卡住**
   - 检查 maxUnavailable 设置
   - 检查资源限制
   - 查看事件日志

4. **请求失败**
   - 检查负载均衡器配置
   - 检查服务端点
   - 验证网络连接

## 相关文档

- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Nginx Load Balancing](https://nginx.org/en/docs/http/load_balancing.html)

# Staging环境部署准备清单

**日期**: 2024-03-07
**目标**: Day 1-2完成Staging部署
**状态**: 准备中

---

## 📋 部署前检查清单

### 1. 环境配置文件
- [ ] 创建`.env.staging`配置文件
- [ ] 配置数据库连接（PostgreSQL）
- [ ] 配置Redis连接
- [ ] 配置区块链RPC URL
- [ ] 配置监控端点
- [ ] 配置日志级别

### 2. 基础设施准备
- [ ] Staging服务器准备
- [ ] PostgreSQL数据库安装配置
- [ ] Redis缓存安装配置
- [ ] Docker和Docker Compose安装
- [ ] 网络端口开放（8000, 8001, 5432, 6379, 9090）

### 3. 代码准备
- [ ] 确认当前分支（master）
- [ ] 拉取最新代码
- [ ] 检查依赖项
- [ ] 准备数据库迁移脚本

### 4. 部署脚本准备
- [ ] 检查deploy_production.sh脚本
- [ ] 创建staging专用部署脚本
- [ ] 准备docker-compose.staging.yml
- [ ] 准备回滚脚本

---

## 🔧 需要创建的文件

### 1. .env.staging
```bash
# 应用配置
ENVIRONMENT=staging
DEBUG=False
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://nautilus:password@localhost:5432/nautilus_staging

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 区块链配置
BLOCKCHAIN_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
BLOCKCHAIN_NETWORK=sepolia

# 监控配置
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# API配置
API_HOST=0.0.0.0
API_PORT=8001
```

### 2. docker-compose.staging.yml
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: nautilus-backend-staging
    ports:
      - "8001:8001"
    env_file:
      - .env.staging
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - nautilus-staging

  postgres:
    image: postgres:15-alpine
    container_name: nautilus-postgres-staging
    environment:
      POSTGRES_DB: nautilus_staging
      POSTGRES_USER: nautilus
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - nautilus-staging

  redis:
    image: redis:7-alpine
    container_name: nautilus-redis-staging
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - nautilus-staging

  prometheus:
    image: prom/prometheus:latest
    container_name: nautilus-prometheus-staging
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - nautilus-staging

  grafana:
    image: grafana/grafana:latest
    container_name: nautilus-grafana-staging
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - nautilus-staging

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  nautilus-staging:
    driver: bridge
```

### 3. deploy_staging.sh
```bash
#!/bin/bash

set -euo pipefail

echo "🚀 开始Staging环境部署..."

# 1. 检查环境
echo "📋 检查部署环境..."
if [ ! -f ".env.staging" ]; then
    echo "❌ 错误: .env.staging文件不存在"
    exit 1
fi

# 2. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin master

# 3. 停止旧服务
echo "🛑 停止旧服务..."
docker-compose -f docker-compose.staging.yml down || true

# 4. 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose -f docker-compose.staging.yml build

# 5. 启动数据库和Redis
echo "🗄️ 启动数据库和Redis..."
docker-compose -f docker-compose.staging.yml up -d postgres redis

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 10

# 6. 运行数据库迁移
echo "🔄 运行数据库迁移..."
docker-compose -f docker-compose.staging.yml run --rm backend alembic upgrade head

# 7. 启动所有服务
echo "🚀 启动所有服务..."
docker-compose -f docker-compose.staging.yml up -d

# 8. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 9. 健康检查
echo "🏥 执行健康检查..."
for i in {1..30}; do
    if curl -sf http://localhost:8001/health > /dev/null; then
        echo "✅ 服务健康检查通过！"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 健康检查超时"
        docker-compose -f docker-compose.staging.yml logs backend
        exit 1
    fi
    echo "等待中... ($i/30)"
    sleep 2
done

# 10. 显示服务状态
echo ""
echo "📊 服务状态:"
docker-compose -f docker-compose.staging.yml ps

echo ""
echo "✅ Staging环境部署完成！"
echo ""
echo "🔗 访问地址:"
echo "  - API: http://localhost:8001"
echo "  - Health: http://localhost:8001/health"
echo "  - Docs: http://localhost:8001/docs"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo ""
echo "📝 查看日志:"
echo "  docker-compose -f docker-compose.staging.yml logs -f backend"
```

---

## 🧪 部署后验证清单

### 1. 服务状态检查
```bash
# 检查容器状态
docker-compose -f docker-compose.staging.yml ps

# 检查日志
docker-compose -f docker-compose.staging.yml logs backend

# 检查健康状态
curl http://localhost:8001/health
```

### 2. API端点测试
```bash
# 健康检查
curl http://localhost:8001/health

# API文档
curl http://localhost:8001/docs

# 获取任务列表
curl http://localhost:8001/api/tasks

# 获取Agent列表
curl http://localhost:8001/api/agents
```

### 3. 数据库连接测试
```bash
# 连接数据库
docker exec -it nautilus-postgres-staging psql -U nautilus -d nautilus_staging

# 检查表
\dt

# 检查数据
SELECT COUNT(*) FROM tasks;
SELECT COUNT(*) FROM agents;
```

### 4. Redis连接测试
```bash
# 连接Redis
docker exec -it nautilus-redis-staging redis-cli

# 检查连接
PING

# 检查键
KEYS *
```

### 5. 监控系统测试
```bash
# 访问Prometheus
open http://localhost:9090

# 访问Grafana
open http://localhost:3000
# 默认用户名: admin
# 默认密码: admin
```

---

## 🧪 测试验证清单

### 1. 单元测试
```bash
# 运行所有测试
docker-compose -f docker-compose.staging.yml run --rm backend pytest tests/ -v

# 运行核心测试
docker-compose -f docker-compose.staging.yml run --rm backend pytest tests/test_week5_*.py -v
```

### 2. 集成测试
```bash
# 运行集成测试
docker-compose -f docker-compose.staging.yml run --rm backend pytest tests/test_*_integration.py -v
```

### 3. E2E测试
```bash
# 运行E2E测试
docker-compose -f docker-compose.staging.yml run --rm backend pytest tests/e2e/ -v
```

### 4. 性能测试
```bash
# 运行性能测试
docker-compose -f docker-compose.staging.yml run --rm backend pytest tests/performance/ -v
```

---

## 📊 性能基准验证

### 1. API响应时间
- [ ] /health < 50ms
- [ ] /api/tasks < 200ms
- [ ] /api/agents < 200ms
- [ ] Epiplexity计算 < 10ms

### 2. 并发处理
- [ ] 100 req/s无错误
- [ ] 500 req/s < 5%错误率

### 3. 资源使用
- [ ] CPU < 70%
- [ ] 内存 < 4GB
- [ ] 磁盘I/O正常

---

## 🔍 监控指标验证

### 1. 系统指标
- [ ] CPU使用率
- [ ] 内存使用率
- [ ] 磁盘I/O
- [ ] 网络流量

### 2. 应用指标
- [ ] API响应时间
- [ ] 请求成功率
- [ ] 错误率
- [ ] 并发用户数

### 3. 业务指标
- [ ] Agent数量
- [ ] 任务完成率
- [ ] 知识节点创建数
- [ ] Epiplexity平均值

---

## 🚨 问题排查指南

### 1. 服务无法启动
```bash
# 查看日志
docker-compose -f docker-compose.staging.yml logs backend

# 检查配置
cat .env.staging

# 检查端口占用
netstat -tuln | grep -E "8001|5432|6379"
```

### 2. 数据库连接失败
```bash
# 检查数据库状态
docker-compose -f docker-compose.staging.yml ps postgres

# 测试连接
docker exec -it nautilus-postgres-staging psql -U nautilus -d nautilus_staging
```

### 3. Redis连接失败
```bash
# 检查Redis状态
docker-compose -f docker-compose.staging.yml ps redis

# 测试连接
docker exec -it nautilus-redis-staging redis-cli PING
```

---

## 📝 部署记录

### 部署信息
- **部署时间**: ___________
- **部署版本**: ___________
- **部署人员**: ___________
- **Git Commit**: ___________

### 验证结果
- [ ] 所有服务启动成功
- [ ] 健康检查通过
- [ ] API端点正常
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] 监控系统正常
- [ ] 测试通过

### 问题记录
- 问题1: ___________
- 解决方案: ___________

---

## 🎯 下一步

完成Staging部署后：
1. [ ] 运行完整测试套件（Day 2-3）
2. [ ] 设置监控告警（Day 3-4）
3. [ ] 准备生产环境部署（Day 5-7）

---

**创建时间**: 2024-03-07
**状态**: 准备就绪
**优先级**: P0

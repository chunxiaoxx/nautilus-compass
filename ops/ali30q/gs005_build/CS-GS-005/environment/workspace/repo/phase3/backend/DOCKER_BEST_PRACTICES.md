# Docker最佳实践指南

## 目录

1. [镜像构建最佳实践](#1-镜像构建最佳实践)
2. [安全最佳实践](#2-安全最佳实践)
3. [性能最佳实践](#3-性能最佳实践)
4. [故障排查](#4-故障排查)
5. [生产环境部署](#5-生产环境部署)
6. [监控和日志](#6-监控和日志)
7. [常见问题FAQ](#7-常见问题faq)

---

## 1. 镜像构建最佳实践

### 1.1 使用多阶段构建

**为什么重要**: 减少最终镜像大小，分离构建和运行时依赖

**示例**:
```dockerfile
# 构建阶段
FROM python:3.13-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# 运行阶段
FROM python:3.13-slim
COPY --from=builder /install /usr/local
COPY . /app
WORKDIR /app
CMD ["python", "app.py"]
```

**优势**:
- ✅ 镜像体积减少40-60%
- ✅ 构建工具不包含在最终镜像
- ✅ 更安全的生产镜像

### 1.2 优化层缓存

**原则**: 将变化频率低的指令放在前面

**正确顺序**:
```dockerfile
# 1. 基础镜像和系统包（很少变化）
FROM python:3.13-slim
RUN apt-get update && apt-get install -y libpq5

# 2. 依赖文件（偶尔变化）
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3. 应用代码（经常变化）
COPY . .

# 4. 启动命令
CMD ["python", "app.py"]
```

**效果**:
- ⚡ 代码更新时构建时间从60s降至10s
- ⚡ 依赖更新时构建时间从120s降至40s

### 1.3 合并RUN命令

**❌ 不好的做法**:
```dockerfile
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN rm -rf /var/lib/apt/lists/*
```

**✅ 好的做法**:
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        package1 \
        package2 && \
    rm -rf /var/lib/apt/lists/*
```

**优势**:
- 减少镜像层数
- 减少镜像体积
- 避免缓存问题

### 1.4 使用.dockerignore

**必须排除的内容**:
```
# 版本控制
.git/
.gitignore

# 虚拟环境
venv/
__pycache__/

# 测试文件
tests/
*.test.py

# 文档
*.md
docs/

# 临时文件
*.log
*.tmp
.DS_Store

# 敏感文件
.env
*.key
*.pem
```

**效果**:
- 构建上下文减少70%
- 构建速度提升50%
- 避免敏感信息泄露

### 1.5 固定基础镜像版本

**❌ 不好的做法**:
```dockerfile
FROM python:3
FROM python:latest
```

**✅ 好的做法**:
```dockerfile
FROM python:3.13-slim
FROM python:3.13.1-slim
```

**原因**:
- 确保构建可重现
- 避免意外的破坏性更新
- 便于回滚

### 1.6 使用小型基础镜像

**镜像大小对比**:
```
python:3.13          → 1.0GB
python:3.13-slim     → 180MB  (推荐)
python:3.13-alpine   → 50MB   (需要额外配置)
```

**选择建议**:
- **开发环境**: slim镜像（平衡大小和兼容性）
- **生产环境**: slim或alpine（根据依赖选择）
- **避免**: 完整镜像（除非必需）

### 1.7 清理临时文件

**在同一层清理**:
```dockerfile
RUN apt-get update && \
    apt-get install -y package && \
    # 使用包
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

**Python特定清理**:
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local -type d -name '__pycache__' -exec rm -rf {} + && \
    find /usr/local -type f -name '*.pyc' -delete
```

### 1.8 使用BuildKit

**启用BuildKit**:
```bash
export DOCKER_BUILDKIT=1
docker build .
```

**或在docker-compose.yml**:
```yaml
services:
  app:
    build:
      context: .
      args:
        - BUILDKIT_INLINE_CACHE=1
```

**优势**:
- 并行构建
- 更好的缓存
- 构建时间减少30-50%

---

## 2. 安全最佳实践

### 2.1 使用非root用户

**✅ 正确实现**:
```dockerfile
# 创建用户
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser -m -s /sbin/nologin appuser

# 设置文件权限
RUN chown -R appuser:appuser /app

# 切换用户
USER appuser

# 启动应用
CMD ["python", "app.py"]
```

**安全检查**:
```bash
# 验证用户
docker exec container-name whoami
# 应该输出: appuser

# 验证权限
docker exec container-name id
# 应该输出: uid=1000(appuser) gid=1000(appuser)
```

### 2.2 最小化安装包

**❌ 不安全**:
```dockerfile
RUN apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    # ... 很多不需要的包
```

**✅ 安全**:
```dockerfile
# 构建阶段安装构建工具
FROM python:3.13-slim as builder
RUN apt-get install -y gcc libpq-dev

# 运行阶段只安装运行时依赖
FROM python:3.13-slim
RUN apt-get install -y --no-install-recommends libpq5
```

### 2.3 扫描镜像漏洞

**使用Trivy扫描**:
```bash
# 安装Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# 扫描镜像
trivy image nautilus-backend:latest

# 只显示高危和严重漏洞
trivy image --severity HIGH,CRITICAL nautilus-backend:latest
```

**集成到CI/CD**:
```yaml
# .github/workflows/security.yml
- name: Run Trivy scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'nautilus-backend:${{ github.sha }}'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### 2.4 不在镜像中存储秘密

**❌ 危险做法**:
```dockerfile
ENV DATABASE_PASSWORD=mysecretpassword
COPY .env /app/.env
```

**✅ 安全做法**:
```dockerfile
# 使用ARG（仅构建时）
ARG BUILD_SECRET
RUN --mount=type=secret,id=mysecret \
    cat /run/secrets/mysecret

# 运行时使用环境变量
docker run -e DATABASE_PASSWORD=$DB_PASS app
```

**Docker Compose**:
```yaml
services:
  app:
    environment:
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### 2.5 使用安全选项

**Docker Compose配置**:
```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

### 2.6 网络隔离

**创建隔离网络**:
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # 不能访问外网

services:
  api:
    networks:
      - frontend
      - backend

  database:
    networks:
      - backend  # 只在内部网络
```

### 2.7 定期更新基础镜像

**自动化更新流程**:
```bash
#!/bin/bash
# update_base_images.sh

# 拉取最新基础镜像
docker pull python:3.13-slim

# 重新构建
docker build -t nautilus-backend:latest .

# 扫描漏洞
trivy image nautilus-backend:latest

# 如果通过，推送到仓库
docker push nautilus-backend:latest
```

**建议频率**:
- 每周检查更新
- 每月重新构建
- 发现严重漏洞立即更新

---

## 3. 性能最佳实践

### 3.1 优化Python应用

**预编译Python文件**:
```dockerfile
# 预编译所有.py文件为.pyc
RUN python -m compileall -b /app && \
    find /app -name "*.py" -type f -delete
```

**效果**:
- 启动时间减少30-40%
- 内存占用减少10-15%

### 3.2 使用高性能事件循环

**安装uvloop**:
```dockerfile
RUN pip install uvloop
```

**启动配置**:
```bash
uvicorn main:app --loop uvloop --workers 4
```

**性能提升**:
- 吞吐量提升2-4倍
- 延迟降低30-50%

### 3.3 配置多worker

**CPU密集型应用**:
```python
workers = (cpu_count * 2) + 1
```

**IO密集型应用**:
```python
workers = cpu_count * 4
```

**Docker配置**:
```dockerfile
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]
```

### 3.4 数据库连接池

**配置示例**:
```python
# SQLAlchemy配置
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # 连接池大小
    max_overflow=10,        # 最大溢出连接
    pool_pre_ping=True,     # 连接健康检查
    pool_recycle=3600,      # 连接回收时间
)
```

**Docker Compose环境变量**:
```yaml
environment:
  DATABASE_POOL_SIZE: 20
  DATABASE_MAX_OVERFLOW: 10
```

### 3.5 Redis缓存优化

**Redis配置**:
```yaml
redis:
  command: >
    redis-server
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
    --save 60 1000
    --appendonly yes
```

**应用层缓存**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_function(param):
    # 昂贵的计算
    return result
```

### 3.6 资源限制

**合理的资源配置**:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**监控资源使用**:
```bash
# 查看容器资源使用
docker stats

# 查看特定容器
docker stats nautilus-backend
```

### 3.7 健康检查优化

**轻量级健康检查**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**健康检查端点**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**避免**:
- 复杂的数据库查询
- 外部API调用
- 重量级检查

---

## 4. 故障排查

### 4.1 容器无法启动

**检查日志**:
```bash
# 查看容器日志
docker logs nautilus-backend

# 实时查看日志
docker logs -f nautilus-backend

# 查看最近100行
docker logs --tail 100 nautilus-backend
```

**常见问题**:

1. **端口冲突**
```bash
# 检查端口占用
netstat -tulpn | grep 8000
lsof -i :8000

# 解决方案：更改端口
docker run -p 8001:8000 nautilus-backend
```

2. **权限问题**
```bash
# 检查文件权限
docker exec nautilus-backend ls -la /app

# 解决方案：修复权限
RUN chown -R appuser:appuser /app
```

3. **依赖缺失**
```bash
# 进入容器检查
docker exec -it nautilus-backend bash

# 测试导入
python -c "import module_name"
```

### 4.2 性能问题

**诊断步骤**:

1. **检查资源使用**
```bash
docker stats nautilus-backend
```

2. **检查进程**
```bash
docker exec nautilus-backend ps aux
```

3. **性能分析**
```bash
# 安装性能分析工具
docker exec nautilus-backend pip install py-spy

# 生成火焰图
docker exec nautilus-backend py-spy record -o profile.svg -- python app.py
```

### 4.3 网络问题

**检查网络连接**:
```bash
# 查看网络配置
docker network ls
docker network inspect nautilus_backend

# 测试容器间连接
docker exec nautilus-backend ping postgres
docker exec nautilus-backend nc -zv postgres 5432
```

**DNS问题**:
```bash
# 检查DNS解析
docker exec nautilus-backend nslookup postgres
docker exec nautilus-backend cat /etc/resolv.conf
```

### 4.4 数据库连接问题

**检查连接**:
```bash
# 测试PostgreSQL连接
docker exec nautilus-backend psql -h postgres -U nautilus -d nautilus_dev -c "SELECT 1"

# 检查连接数
docker exec nautilus-postgres psql -U nautilus -c "SELECT count(*) FROM pg_stat_activity"
```

**常见错误**:

1. **连接被拒绝**
   - 检查数据库是否启动
   - 检查网络配置
   - 检查防火墙规则

2. **认证失败**
   - 验证用户名密码
   - 检查pg_hba.conf配置

3. **连接池耗尽**
   - 增加pool_size
   - 检查连接泄漏

### 4.5 内存泄漏

**诊断工具**:
```bash
# 安装memory_profiler
pip install memory_profiler

# 分析内存使用
python -m memory_profiler app.py
```

**监控内存**:
```bash
# 实时监控
docker stats --format "table {{.Container}}\t{{.MemUsage}}"

# 设置内存限制
docker run -m 512m nautilus-backend
```

### 4.6 调试技巧

**进入运行中的容器**:
```bash
# 使用bash
docker exec -it nautilus-backend bash

# 使用sh（Alpine镜像）
docker exec -it nautilus-backend sh

# 以root用户进入
docker exec -it -u root nautilus-backend bash
```

**复制文件**:
```bash
# 从容器复制到主机
docker cp nautilus-backend:/app/logs/error.log ./

# 从主机复制到容器
docker cp ./config.json nautilus-backend:/app/
```

**查看容器详情**:
```bash
# 完整配置
docker inspect nautilus-backend

# 特定字段
docker inspect --format='{{.State.Status}}' nautilus-backend
docker inspect --format='{{.NetworkSettings.IPAddress}}' nautilus-backend
```

---

## 5. 生产环境部署

### 5.1 部署前检查清单

**安全检查**:
- [ ] 使用非root用户
- [ ] 扫描镜像漏洞
- [ ] 移除调试工具
- [ ] 配置安全选项
- [ ] 使用秘密管理
- [ ] 启用网络隔离

**性能检查**:
- [ ] 配置资源限制
- [ ] 优化连接池
- [ ] 启用健康检查
- [ ] 配置日志轮转
- [ ] 测试负载能力

**可靠性检查**:
- [ ] 配置重启策略
- [ ] 设置依赖顺序
- [ ] 配置备份策略
- [ ] 准备回滚方案
- [ ] 测试故障恢复

### 5.2 蓝绿部署

**实施步骤**:

1. **部署新版本（绿）**
```bash
docker-compose -f docker-compose.green.yml up -d
```

2. **健康检查**
```bash
curl http://green-backend:8000/health
```

3. **切换流量**
```bash
# 更新负载均衡器配置
# 或更新DNS记录
```

4. **监控新版本**
```bash
# 监控错误率、响应时间
```

5. **保留旧版本（蓝）**
```bash
# 保留24小时以便快速回滚
```

### 5.3 滚动更新

**Docker Compose**:
```yaml
services:
  backend:
    deploy:
      replicas: 4
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
```

**执行更新**:
```bash
docker-compose up -d --no-deps --build backend
```

### 5.4 备份策略

**数据库备份**:
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

docker exec nautilus-postgres pg_dump -U nautilus nautilus_dev > \
    "${BACKUP_DIR}/nautilus_${DATE}.sql"

# 保留最近7天的备份
find ${BACKUP_DIR} -name "nautilus_*.sql" -mtime +7 -delete
```

**数据卷备份**:
```bash
# 备份数据卷
docker run --rm \
    -v nautilus_postgres_data:/data \
    -v $(pwd)/backups:/backup \
    alpine tar czf /backup/postgres_data.tar.gz /data
```

### 5.5 监控告警

**Prometheus告警规则**:
```yaml
groups:
  - name: nautilus_alerts
    rules:
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name="nautilus-backend"} > 1.5e9
        for: 5m
        annotations:
          summary: "Backend memory usage is high"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate is above 5%"
```

---

## 6. 监控和日志

### 6.1 日志管理

**配置日志驱动**:
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service,environment"
```

**集中式日志**:
```yaml
services:
  backend:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://logserver:514"
        tag: "nautilus-backend"
```

**查看日志**:
```bash
# 查看所有日志
docker-compose logs

# 查看特定服务
docker-compose logs backend

# 实时跟踪
docker-compose logs -f backend

# 最近100行
docker-compose logs --tail=100 backend
```

### 6.2 性能监控

**Prometheus指标**:
```python
from prometheus_client import Counter, Histogram, Gauge

# 请求计数
request_count = Counter('http_requests_total', 'Total HTTP requests')

# 响应时间
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# 活跃连接
active_connections = Gauge('active_connections', 'Active database connections')
```

**Grafana仪表板**:
- CPU使用率
- 内存使用率
- 请求速率
- 错误率
- 响应时间
- 数据库连接数

### 6.3 健康监控

**多层健康检查**:

1. **容器级别**
```dockerfile
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
```

2. **应用级别**
```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }
```

3. **依赖检查**
```python
@app.get("/health/ready")
async def readiness():
    # 检查数据库
    db_ok = await check_database()
    # 检查Redis
    redis_ok = await check_redis()

    if db_ok and redis_ok:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503)
```

---

## 7. 常见问题FAQ

### Q1: 镜像构建很慢怎么办？

**A**:
1. 启用BuildKit: `export DOCKER_BUILDKIT=1`
2. 优化.dockerignore，减少构建上下文
3. 调整Dockerfile顺序，利用层缓存
4. 使用多阶段构建
5. 考虑使用构建缓存服务器

### Q2: 容器内存占用过高？

**A**:
1. 设置内存限制: `docker run -m 512m`
2. 检查内存泄漏
3. 优化应用代码
4. 减少worker数量
5. 使用内存分析工具

### Q3: 如何在容器间共享数据？

**A**:
```yaml
volumes:
  shared_data:

services:
  app1:
    volumes:
      - shared_data:/data
  app2:
    volumes:
      - shared_data:/data:ro  # 只读
```

### Q4: 如何处理时区问题？

**A**:
```dockerfile
# 方法1: 设置环境变量
ENV TZ=Asia/Shanghai

# 方法2: 安装tzdata
RUN apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
```

### Q5: 如何优化镜像大小？

**A**:
1. 使用slim/alpine基础镜像
2. 多阶段构建
3. 清理临时文件
4. 合并RUN命令
5. 使用.dockerignore
6. 移除不必要的依赖

### Q6: 容器启动后立即退出？

**A**:
```bash
# 查看退出原因
docker logs container-name

# 查看退出代码
docker inspect --format='{{.State.ExitCode}}' container-name

# 常见原因：
# - 主进程立即退出
# - 配置错误
# - 权限问题
# - 依赖服务未就绪
```

### Q7: 如何调试生产环境问题？

**A**:
1. 查看日志: `docker logs`
2. 进入容器: `docker exec -it container bash`
3. 检查资源: `docker stats`
4. 查看网络: `docker network inspect`
5. 导出容器: `docker export`
6. 使用调试镜像

### Q8: 如何实现零停机部署？

**A**:
1. 使用蓝绿部署
2. 配置健康检查
3. 使用滚动更新
4. 配置优雅关闭
5. 使用负载均衡器

### Q9: Docker Compose vs Kubernetes？

**A**:

**使用Docker Compose**:
- 单机部署
- 开发/测试环境
- 简单应用
- 快速原型

**使用Kubernetes**:
- 多节点集群
- 生产环境
- 复杂应用
- 需要自动扩缩容

### Q10: 如何保护敏感数据？

**A**:
1. 使用Docker secrets
2. 环境变量注入
3. 外部密钥管理（Vault）
4. 加密数据卷
5. 不在镜像中存储秘密

---

## 总结

### 关键要点

1. **构建优化**
   - 多阶段构建
   - 层缓存利用
   - 最小化镜像

2. **安全加固**
   - 非root用户
   - 漏洞扫描
   - 网络隔离

3. **性能优化**
   - 资源限制
   - 连接池配置
   - 健康检查

4. **运维实践**
   - 日志管理
   - 监控告警
   - 备份恢复

### 持续改进

- 定期审查配置
- 更新基础镜像
- 优化性能瓶颈
- 学习新特性

### 参考资源

- [Docker官方文档](https://docs.docker.com/)
- [Docker最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [Docker安全指南](https://docs.docker.com/engine/security/)
- [Dockerfile参考](https://docs.docker.com/engine/reference/builder/)

---

**文档版本**: 1.0
**最后更新**: 2026-02-26
**维护者**: Docker优化专家

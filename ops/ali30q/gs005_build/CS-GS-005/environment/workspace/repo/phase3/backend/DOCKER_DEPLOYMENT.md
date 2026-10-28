# Nexus Server Docker 部署指南

## 概述

本文档提供Nexus Server的Docker容器化部署完整指南，包括开发环境、生产环境的配置和故障排查。

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少1GB可用内存
- 端口8001未被占用

## 快速开始

### 方式1: 使用部署脚本（推荐）

**Linux/Mac:**
```bash
# 赋予执行权限
chmod +x deploy.sh

# 交互式菜单
./deploy.sh

# 或直接执行命令
./deploy.sh deploy    # 完整部署
./deploy.sh build     # 仅构建
./deploy.sh start     # 仅启动
./deploy.sh health    # 健康检查
```

**Windows:**
```cmd
# 双击运行或命令行执行
deploy.bat
```

### 方式2: 使用Docker Compose

**开发环境:**
```bash
# 使用开发配置
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

**生产环境:**
```bash
# 使用生产配置
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止服务
docker-compose -f docker-compose.prod.yml down
```

**默认配置:**
```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式3: 使用Docker命令

```bash
# 构建镜像
docker build -t nexus-server:latest .

# 运行容器
docker run -d \
  --name nexus-server \
  -p 8001:8001 \
  -e MAX_AGENTS=100 \
  -e MAX_QUEUE_SIZE=1000 \
  -e CORS_ORIGINS=* \
  -e LOG_LEVEL=info \
  nexus-server:latest

# 查看日志
docker logs -f nexus-server

# 停止容器
docker stop nexus-server

# 删除容器
docker rm nexus-server
```

## 配置文件说明

### Docker配置文件

| 文件 | 用途 |
|------|------|
| `Dockerfile` | 镜像构建文件（多阶段构建，优化大小） |
| `docker-compose.yml` | 默认配置（适合测试） |
| `docker-compose.dev.yml` | 开发环境配置（代码热重载） |
| `docker-compose.prod.yml` | 生产环境配置（高可用） |
| `.dockerignore` | 排除不需要的文件 |
| `.env.example` | 环境变量模板 |
| `deploy.sh` | Linux/Mac部署脚本 |
| `deploy.bat` | Windows部署脚本 |

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MAX_AGENTS` | 100 | 最大智能体连接数 |
| `MAX_QUEUE_SIZE` | 1000 | 消息队列最大大小 |
| `CORS_ORIGINS` | * | CORS允许的源 |
| `LOG_LEVEL` | info | 日志级别 (debug/info/warning/error) |
| `ENVIRONMENT` | production | 运行环境 (development/production) |
| `PORT` | 8001 | 服务端口 |

### 配置示例

**开发环境 (.env):**
```env
MAX_AGENTS=50
MAX_QUEUE_SIZE=500
CORS_ORIGINS=*
LOG_LEVEL=debug
ENVIRONMENT=development
```

**生产环境 (.env):**
```env
MAX_AGENTS=200
MAX_QUEUE_SIZE=2000
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=warning
ENVIRONMENT=production
```

## 健康检查

### HTTP健康检查端点

```bash
# 检查服务健康状态
curl http://localhost:8001/health

# 响应示例
{
  "status": "healthy",
  "version": "1.0.0",
  "online_agents": 0
}
```

### 查看统计信息

```bash
# 获取服务器统计
curl http://localhost:8001/stats

# 获取在线智能体
curl http://localhost:8001/agents
```

## 容器管理

### 查看容器状态

```bash
# 查看运行中的容器
docker ps

# 查看容器详细信息
docker inspect nexus-server

# 查看容器资源使用
docker stats nexus-server
```

### 日志管理

```bash
# 实时查看日志
docker-compose logs -f nexus-server

# 查看最近100行日志
docker-compose logs --tail=100 nexus-server

# 查看特定时间的日志
docker-compose logs --since 30m nexus-server
```

### 重启服务

```bash
# 重启容器
docker-compose restart nexus-server

# 重新构建并重启
docker-compose up -d --build
```

## 资源限制

Docker Compose配置中已设置资源限制：

- CPU限制: 2核心（最大）
- 内存限制: 1GB（最大）
- CPU预留: 0.5核心（最小）
- 内存预留: 256MB（最小）

### 自定义资源限制

编辑`docker-compose.yml`：

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 512M
```

## 网络配置

### 端口映射

默认映射：`8001:8001`（主机:容器）

修改主机端口：

```yaml
ports:
  - "9001:8001"  # 使用主机端口9001
```

### 网络模式

默认使用bridge网络。如需连接其他容器：

```yaml
networks:
  - nexus-network
  - other-network
```

## 数据持久化

如需持久化日志或数据：

```yaml
volumes:
  - ./logs:/app/logs
  - ./data:/app/data
```

## 故障排查指南

### 常见问题速查表

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 容器无法启动 | 端口被占用 | 检查端口占用，修改端口映射 |
| 健康检查失败 | 服务未就绪 | 等待更长时间或检查日志 |
| 连接被拒绝 | 防火墙阻止 | 配置防火墙规则 |
| 内存不足 | 资源限制太小 | 增加内存限制 |
| 构建失败 | 依赖问题 | 清理缓存重新构建 |

### 1. 容器无法启动

**症状:** `docker-compose up -d` 后容器立即退出

**排查步骤:**
```bash
# 1. 查看容器日志
docker-compose logs nexus-server

# 2. 检查端口占用
# Windows
netstat -ano | findstr :8001
# Linux/Mac
lsof -i :8001

# 3. 检查镜像是否构建成功
docker images | grep nexus-server

# 4. 查看容器状态
docker-compose ps

# 5. 尝试手动运行查看错误
docker run --rm nexus-server:latest
```

**解决方案:**
- 如果端口被占用，修改 `docker-compose.yml` 中的端口映射
- 如果镜像不存在，运行 `docker-compose build`
- 检查 `requirements.txt` 中的依赖是否正确

### 2. 健康检查失败

**症状:** 容器运行但健康检查一直失败

**排查步骤:**
```bash
# 1. 进入容器检查
docker exec -it nexus-server bash

# 2. 在容器内手动测试健康检查
curl http://localhost:8001/health

# 3. 查看Python进程
ps aux | grep python

# 4. 检查端口监听
netstat -tlnp | grep 8001

# 5. 查看详细日志
docker-compose logs --tail=100 nexus-server
```

**解决方案:**
- 增加 `start_period` 时间（服务启动需要更长时间）
- 检查服务是否正确监听 8001 端口
- 查看日志中是否有启动错误

### 3. 连接被拒绝

**症状:** 从主机无法访问 `http://localhost:8001`

**排查步骤:**
```bash
# 1. 检查容器是否运行
docker ps | grep nexus-server

# 2. 检查端口映射
docker port nexus-server

# 3. 测试容器内部连接
docker exec nexus-server curl http://localhost:8001/health

# 4. 检查防火墙
# Windows
netsh advfirewall show allprofiles
# Linux
sudo ufw status
```

**解决方案:**
```bash
# Windows防火墙
netsh advfirewall firewall add rule name="Nexus Server" dir=in action=allow protocol=TCP localport=8001

# Linux防火墙
sudo ufw allow 8001/tcp

# 如果使用Docker Desktop，检查网络设置
```

### 4. 内存不足

**症状:** 容器频繁重启或OOM killed

**排查步骤:**
```bash
# 1. 查看容器内存使用
docker stats nexus-server

# 2. 查看容器事件
docker events --filter container=nexus-server

# 3. 检查系统内存
free -h  # Linux
```

**解决方案:**
编辑 `docker-compose.yml` 增加内存限制：
```yaml
deploy:
  resources:
    limits:
      memory: 2G  # 增加到2GB
    reservations:
      memory: 512M
```

### 5. 依赖安装失败

**症状:** 构建镜像时失败

**排查步骤:**
```bash
# 1. 查看构建日志
docker-compose build

# 2. 检查requirements.txt
cat requirements.txt

# 3. 测试单个依赖安装
docker run --rm python:3.13-slim pip install fastapi==0.104.1
```

**解决方案:**
```bash
# 清理缓存重新构建
docker-compose build --no-cache

# 如果网络问题，使用国内镜像
# 在Dockerfile中添加：
# RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 6. WebSocket连接失败

**症状:** 客户端无法建立WebSocket连接

**排查步骤:**
```bash
# 1. 检查CORS配置
docker exec nexus-server env | grep CORS

# 2. 测试HTTP连接
curl http://localhost:8001/health

# 3. 查看Socket.IO日志
docker-compose logs -f nexus-server | grep socket
```

**解决方案:**
- 确保 `CORS_ORIGINS` 包含客户端域名
- 如果使用反向代理，确保正确配置WebSocket升级
- 检查客户端连接URL是否正确

### 7. 性能问题

**症状:** 响应慢或消息延迟

**排查步骤:**
```bash
# 1. 查看资源使用
docker stats nexus-server

# 2. 查看统计信息
curl http://localhost:8001/stats

# 3. 检查消息队列
# 查看日志中的queue_size
```

**解决方案:**
- 增加 `MAX_AGENTS` 和 `MAX_QUEUE_SIZE`
- 增加CPU和内存限制
- 考虑水平扩展（多实例）

### 8. 日志问题

**症状:** 日志过多或找不到日志

**排查步骤:**
```bash
# 1. 查看日志配置
docker inspect nexus-server | grep -A 10 LogConfig

# 2. 查看日志文件大小
docker exec nexus-server du -sh /var/lib/docker/containers/*/

# 3. 查看日志驱动
docker info | grep "Logging Driver"
```

**解决方案:**
配置日志轮转（已在 docker-compose.yml 中配置）：
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 生产环境部署建议

### 1. 使用环境变量文件

创建`.env`文件：

```env
MAX_AGENTS=500
MAX_QUEUE_SIZE=5000
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=warning
```

在`docker-compose.yml`中引用：

```yaml
env_file:
  - .env
```

### 2. 启用日志轮转

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 3. 使用反向代理

推荐使用Nginx或Traefik作为反向代理：

```nginx
server {
    listen 80;
    server_name nexus.yourdomain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. 监控和告警

使用Prometheus + Grafana监控：

```yaml
services:
  nexus-server:
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8001"
```

## 更新和维护

### 更新镜像

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务（零停机）
docker-compose up -d
```

### 备份和恢复

```bash
# 导出镜像
docker save nexus-server:latest > nexus-server.tar

# 导入镜像
docker load < nexus-server.tar
```

## 安全建议

1. 不要在生产环境使用`CORS_ORIGINS=*`
2. 使用HTTPS（通过反向代理）
3. 定期更新基础镜像
4. 限制容器权限（非root用户）
5. 使用Docker secrets管理敏感信息

## 性能优化

1. 调整`MAX_AGENTS`和`MAX_QUEUE_SIZE`根据负载
2. 使用多阶段构建减小镜像大小
3. 启用Docker BuildKit加速构建
4. 使用镜像缓存加速部署

## 支持和反馈

如遇到问题，请提供以下信息：

- Docker版本：`docker --version`
- Docker Compose版本：`docker-compose --version`
- 容器日志：`docker-compose logs nexus-server`
- 系统信息：`docker info`

## 附录

### 完整的docker-compose.yml示例

```yaml
version: '3.8'

services:
  nexus-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: nexus-server
    ports:
      - "8001:8001"
    environment:
      - MAX_AGENTS=100
      - MAX_QUEUE_SIZE=1000
      - CORS_ORIGINS=*
      - LOG_LEVEL=info
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    networks:
      - nexus-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  nexus-network:
    driver: bridge
```

### Dockerfile最佳实践

```dockerfile
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY nexus_server.py .
COPY nexus_protocol/ ./nexus_protocol/

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["python", "nexus_server.py"]
```

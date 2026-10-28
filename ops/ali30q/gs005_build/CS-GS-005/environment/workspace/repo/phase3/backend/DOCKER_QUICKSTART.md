# Nexus Server Docker 部署 - 快速参考

## 一键部署

### Linux/Mac
```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
chmod +x deploy.sh
./deploy.sh deploy
```

### Windows
```cmd
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
deploy.bat
```

## 快速命令

### 构建和启动
```bash
# 默认配置
docker-compose up -d

# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 健康检查
```bash
curl http://localhost:8001/health
curl http://localhost:8001/stats
curl http://localhost:8001/agents
```

### 日志和状态
```bash
# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 查看资源
docker stats nexus-server
```

### 停止和清理
```bash
# 停止服务
docker-compose down

# 完全清理
docker-compose down -v
docker system prune -f
```

## 配置文件

| 文件 | 说明 |
|------|------|
| `Dockerfile` | 镜像构建（多阶段、非root用户） |
| `docker-compose.yml` | 默认配置 |
| `docker-compose.dev.yml` | 开发环境（代码热重载） |
| `docker-compose.prod.yml` | 生产环境（高可用） |
| `.dockerignore` | 构建排除规则 |
| `.env.example` | 环境变量模板 |

## 环境变量

```env
MAX_AGENTS=100              # 最大智能体数
MAX_QUEUE_SIZE=1000         # 消息队列大小
CORS_ORIGINS=*              # CORS配置
LOG_LEVEL=info              # 日志级别
ENVIRONMENT=production      # 运行环境
```

## 故障排查

```bash
# 查看日志
docker-compose logs nexus-server

# 检查端口
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # Linux/Mac

# 进入容器
docker exec -it nexus-server bash

# 重新构建
docker-compose build --no-cache
```

## 文档

- **DOCKER_DEPLOYMENT.md** - 完整部署指南
- **DOCKER_TEST_CHECKLIST.md** - 测试清单
- **DOCKER_OPTIMIZATION.md** - 优化说明
- **DOCKER_COMPLETION_REPORT.md** - 完成报告

## 验收标准

- ✅ Docker可以成功构建
- ✅ 容器可以正常运行
- ✅ 服务可以访问
- ✅ 文档完整

## 支持

如有问题，请查看：
1. 详细日志：`docker-compose logs`
2. 故障排查指南：`DOCKER_DEPLOYMENT.md`
3. 测试清单：`DOCKER_TEST_CHECKLIST.md`

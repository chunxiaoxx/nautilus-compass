# Docker部署测试清单

## 测试环境
- 日期: 2026-02-25
- Docker版本: 需要 20.10+
- Docker Compose版本: 需要 2.0+

## 测试步骤

### 1. 构建测试

```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend

# 测试镜像构建
docker-compose build

# 预期结果：
# ✅ 构建成功，无错误
# ✅ 镜像大小合理（< 500MB）
```

### 2. 启动测试

```bash
# 启动服务
docker-compose up -d

# 检查容器状态
docker-compose ps

# 预期结果：
# ✅ 容器状态为 Up
# ✅ 健康检查通过 (healthy)
```

### 3. 健康检查测试

```bash
# 等待服务启动
sleep 10

# 测试健康检查端点
curl http://localhost:8001/health

# 预期响应：
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "online_agents": 0
# }
```

### 4. API端点测试

```bash
# 测试统计端点
curl http://localhost:8001/stats

# 测试智能体列表端点
curl http://localhost:8001/agents

# 预期结果：
# ✅ 所有端点返回200状态码
# ✅ 返回正确的JSON格式
```

### 5. 日志测试

```bash
# 查看日志
docker-compose logs --tail=50 nexus-server

# 预期结果：
# ✅ 无错误日志
# ✅ 显示服务启动信息
# ✅ 显示Socket.IO初始化信息
```

### 6. 资源使用测试

```bash
# 查看资源使用
docker stats nexus-server --no-stream

# 预期结果：
# ✅ 内存使用 < 500MB
# ✅ CPU使用正常
```

### 7. 重启测试

```bash
# 重启服务
docker-compose restart

# 等待重启
sleep 10

# 再次检查健康
curl http://localhost:8001/health

# 预期结果：
# ✅ 服务正常重启
# ✅ 健康检查通过
```

### 8. 停止测试

```bash
# 停止服务
docker-compose down

# 检查容器
docker ps -a | grep nexus-server

# 预期结果：
# ✅ 容器已停止
# ✅ 无残留进程
```

## 验收标准

- [x] Docker镜像可以成功构建
- [x] 容器可以正常启动
- [x] 健康检查通过
- [x] 所有API端点可访问
- [x] 日志输出正常
- [x] 资源使用合理
- [x] 可以正常重启
- [x] 可以正常停止

## 测试命令汇总

```bash
# 完整测试流程
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend

# 1. 构建
docker-compose build

# 2. 启动
docker-compose up -d

# 3. 等待启动
sleep 10

# 4. 健康检查
curl http://localhost:8001/health

# 5. 查看状态
docker-compose ps

# 6. 查看日志
docker-compose logs --tail=50

# 7. 查看资源
docker stats nexus-server --no-stream

# 8. 停止
docker-compose down
```

## Windows测试命令

```cmd
REM 切换目录
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend

REM 构建
docker-compose build

REM 启动
docker-compose up -d

REM 等待10秒
timeout /t 10 /nobreak

REM 健康检查
curl http://localhost:8001/health

REM 查看状态
docker-compose ps

REM 查看日志
docker-compose logs --tail=50

REM 停止
docker-compose down
```

## 故障排查

如果测试失败，请检查：

1. Docker是否正确安装和运行
2. 端口8001是否被占用
3. 查看详细日志：`docker-compose logs nexus-server`
4. 检查防火墙设置
5. 确认requirements.txt中的依赖正确

## 下一步

测试通过后，可以：
1. 使用 `deploy.sh` 或 `deploy.bat` 进行自动化部署
2. 配置生产环境参数
3. 设置监控和告警
4. 配置反向代理（Nginx/Traefik）

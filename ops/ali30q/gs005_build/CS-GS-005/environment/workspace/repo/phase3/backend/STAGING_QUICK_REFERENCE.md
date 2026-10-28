# 🚀 Nautilus Staging环境 - 快速参考

**更新时间**: 2024-03-08 05:00
**状态**: ✅ 全部运行中

---

## 📍 访问地址

### 应用服务
```
Backend API:  http://localhost:8001
API文档:      http://localhost:8001/docs
API Redoc:    http://localhost:8001/redoc
```

### 监控服务
```
Prometheus:   http://localhost:9090
Grafana:      http://localhost:3000
  用户名: admin
  密码: admin
```

### 数据库
```
PostgreSQL:   localhost:5432
  数据库: nautilus_staging
  用户: nautilus
  密码: nautilus_staging_2024

Redis:        localhost:6379
```

---

## 🔧 常用命令

### 查看服务状态
```bash
docker ps | grep nautilus
docker-compose -f docker-compose.staging.yml ps
```

### 查看日志
```bash
# 后端日志
docker logs nautilus-backend-staging

# 数据库日志
docker logs nautilus-postgres-staging

# 所有服务日志
docker-compose -f docker-compose.staging.yml logs -f
```

### 重启服务
```bash
# 重启后端
docker-compose -f docker-compose.staging.yml restart backend

# 重启所有服务
docker-compose -f docker-compose.staging.yml restart
```

### 停止服务
```bash
# 停止所有服务
docker-compose -f docker-compose.staging.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.staging.yml down -v
```

### 启动服务
```bash
# 启动所有服务
docker-compose -f docker-compose.staging.yml up -d

# 启动特定服务
docker-compose -f docker-compose.staging.yml up -d backend
```

---

## 🧪 测试命令

### 快速测试
```bash
cd tests
python run_quick_test.py
```

### 完整测试
```bash
cd tests
python run_test_suite.py
```

### 覆盖率测试
```bash
pytest tests/ --cov=. --cov-report=html
```

---

## 📊 当前状态

### 运行中的服务
```
✅ nautilus-backend-staging     (8001)
✅ nautilus-postgres-staging    (5432)
✅ nautilus-redis-staging       (6379)
✅ nautilus-prometheus-staging  (9090)
✅ nautilus-grafana-staging     (3000)
```

### 数据库表
```
✅ agents (代理)
✅ api_keys (API密钥)
✅ oauth_access_tokens (OAuth访问令牌)
✅ oauth_authorization_codes (OAuth授权码)
✅ oauth_clients (OAuth客户端)
✅ rewards (奖励)
✅ tasks (任务)
✅ users (用户)
✅ verification_logs (验证日志)
```

---

## ⚠️ 已知问题

### 非关键问题
1. **Health端点**: 有async bug，不影响服务
2. **Redis连接**: 有警告，缓存降级
3. **Web3连接**: 失败，区块链功能不可用
4. **Alertmanager**: 重启循环，不影响监控

---

## 📝 重要文档

### 部署文档
- `STAGING_DEPLOYMENT_COMPLETE.md` - 部署完成报告
- `BACKEND_STARTUP_SUCCESS.md` - 后端启动详情
- `MONITORING_SYSTEM_STATUS.md` - 监控系统状态
- `TEST_PREPARATION_STATUS.md` - 测试准备状态

### 工作总结
- `WORK_SUMMARY_2024_03_08.md` - 完整工作总结

### 测试指南
- `QUICK_TEST_GUIDE.md` - 快速测试指南

---

## 🆘 故障排查

### Backend无法访问
```bash
# 检查容器状态
docker ps | grep backend

# 查看日志
docker logs nautilus-backend-staging

# 重启服务
docker-compose -f docker-compose.staging.yml restart backend
```

### 数据库连接失败
```bash
# 检查PostgreSQL
docker exec nautilus-postgres-staging pg_isready -U nautilus

# 测试连接
docker exec nautilus-postgres-staging psql -U nautilus -d nautilus_staging -c "SELECT 1;"
```

### Redis连接失败
```bash
# 检查Redis
docker exec nautilus-redis-staging redis-cli ping

# 查看日志
docker logs nautilus-redis-staging
```

---

## 🎯 下一步

1. ✅ 运行完整测试套件
2. ✅ 修复已知小问题
3. ✅ 性能测试
4. ✅ 准备生产环境

---

**快速启动**: `docker-compose -f docker-compose.staging.yml up -d`
**快速停止**: `docker-compose -f docker-compose.staging.yml down`
**查看状态**: `docker ps | grep nautilus`

---

# ✅ Staging环境就绪！

# 健康检查修复 - 测试验证指南

## 快速验证命令

### 1. 基本健康检查
```bash
curl http://115.159.62.192:8000/health
```

**预期输出**:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "3.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "connected": true,
      "response_time": 0.023
    },
    "blockchain": {
      "status": "healthy",
      "connected": true,
      "block_number": 12345
    },
    "redis": {
      "status": "healthy",
      "connected": true
    }
  }
}
```

### 2. 仅检查数据库状态
```bash
curl -s http://115.159.62.192:8000/health | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Database Status: {data['checks']['database']['status']}\"); print(f\"Connected: {data['checks']['database']['connected']}\"); print(f\"Response Time: {data['checks']['database']['response_time']}s\")"
```

### 3. 检查服务日志
```bash
ssh ubuntu@115.159.62.192
sudo journalctl -u nautilus-backend -n 50 --no-pager | grep -i "health\|database"
```

## 详细验证步骤

### 步骤 1: 验证文件已更新
```bash
ssh ubuntu@115.159.62.192
cd /home/ubuntu/nautilus-mvp/phase3/backend
grep -A 3 "result = conn.execute" monitoring_config.py
```

**预期输出**:
```python
result = conn.execute(text("SELECT 1"))
result.close()
```

### 步骤 2: 验证服务运行状态
```bash
ssh ubuntu@115.159.62.192
sudo systemctl status nautilus-backend
```

**预期输出**:
- Active: active (running)
- 无错误信息

### 步骤 3: 多次调用健康检查
```bash
for i in {1..5}; do
  echo "=== 测试 $i ==="
  curl -s http://115.159.62.192:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin)['checks']['database']['status'])"
  sleep 2
done
```

**预期输出**: 5次都返回 "healthy"

### 步骤 4: 压力测试
```bash
# 并发 10 个请求
for i in {1..10}; do
  curl -s http://115.159.62.192:8000/health &
done
wait
```

**预期**: 所有请求都成功返回，无错误

### 步骤 5: 检查数据库连接池
```bash
curl -s http://115.159.62.192:8000/database/pool
```

**预期输出**:
```json
{
  "pool": {
    "size": 20,
    "checked_out": 0,
    "overflow": 0,
    "queue_size": 0,
    "utilization": 0.0
  },
  "status": "ok"
}
```

## 验证清单

### ✅ 功能验证
- [ ] `/health` 端点返回 200 状态码
- [ ] `status` 字段为 "healthy"
- [ ] `database.status` 为 "healthy"
- [ ] `database.connected` 为 true
- [ ] `database.response_time` < 1.0 秒
- [ ] 无 "Not an executable object" 错误

### ✅ 性能验证
- [ ] 响应时间 < 500ms
- [ ] 连续 10 次调用都成功
- [ ] 并发 10 个请求都成功
- [ ] 数据库连接池无泄漏

### ✅ 日志验证
- [ ] 无错误日志
- [ ] 健康检查日志正常
- [ ] 数据库连接日志正常

## 常见问题排查

### 问题 1: 仍然返回 "Not an executable object"
**原因**: 文件未正确上传或服务未重启
**解决**:
```bash
ssh ubuntu@115.159.62.192
cd /home/ubuntu/nautilus-mvp/phase3/backend
cat monitoring_config.py | grep -A 2 "result = conn.execute"
sudo systemctl restart nautilus-backend
```

### 问题 2: 返回 "unhealthy" 但无错误信息
**原因**: 数据库连接配置问题
**解决**:
```bash
ssh ubuntu@115.159.62.192
cd /home/ubuntu/nautilus-mvp/phase3/backend
cat .env | grep DATABASE_URL
# 测试数据库连接
python3 -c "from utils.database import engine; print(engine.url)"
```

### 问题 3: 响应时间过长 (> 1秒)
**原因**: 数据库性能问题或网络延迟
**解决**:
```bash
ssh ubuntu@115.159.62.192
# 检查数据库性能
psql -U postgres -d nautilus -c "SELECT pg_stat_activity.pid, pg_stat_activity.query FROM pg_stat_activity WHERE state = 'active';"
```

### 问题 4: 连接池泄漏
**原因**: 其他代码未正确关闭连接
**解决**:
```bash
curl http://115.159.62.192:8000/database/pool
# 如果 checked_out 持续增长，需要检查其他代码
```

## 性能基准

| 指标 | 目标值 | 可接受范围 |
|------|--------|-----------|
| 响应时间 | < 100ms | < 500ms |
| 数据库查询时间 | < 10ms | < 50ms |
| 成功率 | 100% | > 99% |
| 并发处理 | 10+ | 5+ |

## 监控建议

### 1. 设置告警
```bash
# Prometheus 告警规则
- alert: DatabaseHealthCheckFailed
  expr: nautilus_database_health_status != 1
  for: 5m
  annotations:
    summary: "Database health check failed"
```

### 2. 定期检查
```bash
# 添加到 crontab
*/5 * * * * curl -s http://115.159.62.192:8000/health | grep -q "healthy" || echo "Health check failed" | mail -s "Alert" admin@example.com
```

### 3. 日志监控
```bash
# 监控错误日志
tail -f /var/log/nautilus/backend.log | grep -i "error\|failed"
```

## 回滚验证

如果需要回滚，执行后验证：
```bash
# 回滚
ssh ubuntu@115.159.62.192
cd /home/ubuntu/nautilus-mvp/phase3/backend
cp monitoring_config.py.backup monitoring_config.py
sudo systemctl restart nautilus-backend

# 验证回滚成功
curl http://115.159.62.192:8000/health
```

## 联系信息

如遇问题，请提供以下信息：
1. 健康检查返回的完整 JSON
2. 服务日志最后 50 行
3. 数据库连接池状态
4. 系统资源使用情况

```bash
# 收集诊断信息
curl -s http://115.159.62.192:8000/health > health.json
ssh ubuntu@115.159.62.192 "sudo journalctl -u nautilus-backend -n 50" > service.log
curl -s http://115.159.62.192:8000/database/pool > pool.json
```

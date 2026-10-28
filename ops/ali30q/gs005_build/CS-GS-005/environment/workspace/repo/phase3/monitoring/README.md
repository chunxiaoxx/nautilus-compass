# Nautilus 监控告警配置

## 配置文件说明

### alerts.yml - Prometheus 告警规则
定义了三个优先级的告警规则：

#### P0 - 关键告警（Critical）
- **ServiceDown**: API 服务宕机超过 1 分钟
- **DatabaseDown**: 数据库连接失败超过 1 分钟
- **HighErrorRate**: 5xx 错误率超过 5%（持续 5 分钟）

#### P1 - 重要告警（Warning）
- **HighResponseTime**: 95% 请求响应时间超过 1 秒（持续 10 分钟）
- **HighMemoryUsage**: 内存使用率超过 85%（持续 5 分钟）
- **HighCPUUsage**: CPU 使用率超过 80%（持续 10 分钟）
- **DiskSpaceLow**: 根分区可用空间低于 15%（持续 5 分钟）

#### P2 - 次要告警（Info）
- **HighDatabaseConnections**: 活跃数据库连接超过 50（持续 10 分钟）
- **SlowDatabaseQuery**: 平均查询时间超过 500ms（持续 10 分钟）

### alertmanager.yml - AlertManager 配置
- 按优先级路由告警到不同的 webhook
- P0 告警发送到 `/api/alerts/critical`
- P1 告警发送到 `/api/alerts/warning`
- 其他告警发送到 `/api/alerts/webhook`
- 告警抑制：critical 级别会抑制同名的 warning 级别告警

### prometheus.yml - Prometheus 主配置
- 抓取间隔：15 秒
- 评估间隔：15 秒
- 监控目标：
  - nautilus-api (localhost:8000)
  - node-exporter (localhost:9100)
  - prometheus (localhost:9090)

## 部署步骤

### 1. 上传配置到服务器
```bash
scp monitoring/*.yml cloud:/home/ubuntu/nautilus-mvp/phase3/monitoring/
```

### 2. 验证配置
```bash
# 验证 Prometheus 配置
docker run --rm -v /home/ubuntu/nautilus-mvp/phase3/monitoring:/config \
  prom/prometheus:latest promtool check config /config/prometheus.yml

# 验证告警规则
docker run --rm -v /home/ubuntu/nautilus-mvp/phase3/monitoring:/config \
  prom/prometheus:latest promtool check rules /config/alerts.yml

# 验证 AlertManager 配置
docker run --rm -v /home/ubuntu/nautilus-mvp/phase3/monitoring:/config \
  prom/alertmanager:latest amtool check-config /config/alertmanager.yml
```

### 3. 启动服务
```bash
cd /home/ubuntu/nautilus-mvp/phase3
docker-compose up -d prometheus alertmanager
```

### 4. 验证运行状态
```bash
# 检查 Prometheus
curl http://localhost:9090/-/healthy

# 检查 AlertManager
curl http://localhost:9093/-/healthy

# 查看告警规则
curl http://localhost:9090/api/v1/rules
```

## 告警 Webhook 端点

需要在后端实现以下端点来接收告警：

- `POST /api/alerts/webhook` - 接收所有告警
- `POST /api/alerts/critical` - 接收 P0 关键告警
- `POST /api/alerts/warning` - 接收 P1 重要告警

### Webhook 请求格式
```json
{
  "version": "4",
  "groupKey": "{}:{alertname=\"ServiceDown\"}",
  "status": "firing",
  "receiver": "critical",
  "groupLabels": {
    "alertname": "ServiceDown"
  },
  "commonLabels": {
    "alertname": "ServiceDown",
    "priority": "P0",
    "severity": "critical"
  },
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "ServiceDown",
        "priority": "P0",
        "severity": "critical"
      },
      "annotations": {
        "description": "API 服务已宕机超过 1 分钟",
        "summary": "Nautilus API 服务宕机"
      },
      "startsAt": "2026-03-03T10:00:00Z",
      "endsAt": "0001-01-01T00:00:00Z"
    }
  ]
}
```

## 访问界面

- Prometheus: http://localhost:9090
- AlertManager: http://localhost:9093
- Grafana: http://localhost:3001

## 告警测试

### 触发 ServiceDown 告警
```bash
# 停止 API 服务
docker-compose stop api

# 等待 1 分钟后检查告警
curl http://localhost:9090/api/v1/alerts
```

### 触发 HighErrorRate 告警
```bash
# 发送大量请求触发错误
for i in {1..100}; do
  curl http://localhost:8000/api/nonexistent
done
```

## 维护

### 查看活跃告警
```bash
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
```

### 静默告警
```bash
# 通过 AlertManager UI 或 API 静默特定告警
amtool silence add alertname=HighMemoryUsage --duration=1h
```

### 更新配置
```bash
# 重新加载 Prometheus 配置（无需重启）
curl -X POST http://localhost:9090/-/reload

# 重新加载 AlertManager 配置
curl -X POST http://localhost:9093/-/reload
```

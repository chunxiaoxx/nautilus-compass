# Nautilus 监控系统快速参考

## 一键命令

### 部署监控系统
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend/monitoring && chmod +x deploy_monitoring.sh && ./deploy_monitoring.sh
```

### 验证监控系统
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend/monitoring && chmod +x verify_monitoring.sh && ./verify_monitoring.sh
```

### 使用 Docker Compose 部署
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend && docker-compose -f docker-compose.monitoring.yml up -d
```

## 快速访问

| 服务 | 本地地址 | 外网地址 | 凭证 |
|------|---------|---------|------|
| Prometheus | http://localhost:9090 | http://115.159.62.192:9090 | 无需认证 |
| Grafana | http://localhost:3001 | http://115.159.62.192:3001 | admin / nautilus2024 |
| AlertManager | http://localhost:9093 | http://115.159.62.192:9093 | 无需认证 |
| Node Exporter | http://localhost:9100/metrics | http://115.159.62.192:9100/metrics | 无需认证 |
| Nautilus Metrics | http://localhost:8000/metrics | http://115.159.62.192:8000/metrics | 无需认证 |

## 常用命令

### 服务管理
```bash
# 查看所有监控容器状态
docker ps | grep nautilus-

# 启动所有监控服务
docker start nautilus-prometheus nautilus-grafana nautilus-alertmanager nautilus-node-exporter

# 停止所有监控服务
docker stop nautilus-prometheus nautilus-grafana nautilus-alertmanager nautilus-node-exporter

# 重启所有监控服务
docker restart nautilus-prometheus nautilus-grafana nautilus-alertmanager nautilus-node-exporter

# 查看服务日志
docker logs -f nautilus-prometheus
docker logs -f nautilus-grafana
docker logs -f nautilus-alertmanager
```

### 健康检查
```bash
# 检查 Prometheus
curl http://localhost:9090/-/healthy

# 检查 Grafana
curl http://localhost:3001/api/health

# 检查 AlertManager
curl http://localhost:9093/-/healthy

# 检查 Nautilus Metrics
curl http://localhost:8000/metrics | head -20

# 一键检查所有服务
curl -s http://localhost:9090/-/healthy && echo "Prometheus: OK" || echo "Prometheus: FAIL"
curl -s http://localhost:3001/api/health && echo "Grafana: OK" || echo "Grafana: FAIL"
curl -s http://localhost:9093/-/healthy && echo "AlertManager: OK" || echo "AlertManager: FAIL"
curl -s http://localhost:8000/metrics > /dev/null && echo "Nautilus: OK" || echo "Nautilus: FAIL"
```

### 配置管理
```bash
# 重新加载 Prometheus 配置（无需重启）
curl -X POST http://localhost:9090/-/reload

# 重新加载 AlertManager 配置（无需重启）
curl -X POST http://localhost:9093/-/reload

# 编辑 Prometheus 配置
sudo nano /home/ubuntu/monitoring/prometheus/prometheus.yml

# 编辑告警规则
sudo nano /home/ubuntu/monitoring/prometheus/alerting_rules.yml

# 编辑 AlertManager 配置
sudo nano /home/ubuntu/monitoring/alertmanager/alertmanager.yml
```

### 数据查询
```bash
# 查询 Prometheus Targets 状态
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# 查询当前告警
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {name: .labels.alertname, state: .state}'

# 查询指标数据
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq .

# 查询请求速率
curl -s 'http://localhost:9090/api/v1/query?query=rate(nautilus_http_requests_total[5m])' | jq .
```

## 关键 PromQL 查询

### 系统监控
```promql
# CPU 使用率
rate(process_cpu_seconds_total[5m]) * 100

# 内存使用（MB）
process_resident_memory_bytes / 1024 / 1024

# 文件描述符使用率
process_open_fds / process_max_fds * 100
```

### API 监控
```promql
# 请求速率（QPS）
rate(nautilus_http_requests_total[5m])

# 错误率
rate(nautilus_http_requests_total{status=~"5.."}[5m]) / rate(nautilus_http_requests_total[5m])

# P95 响应时间
histogram_quantile(0.95, rate(nautilus_http_request_duration_seconds_bucket[5m]))
```

### 业务监控
```promql
# 活跃任务数
nautilus_tasks_active

# 活跃 Agent 数
nautilus_agents_active

# 数据库连接数
nautilus_database_connections
```

## 故障排查

### Prometheus 无法启动
```bash
# 检查配置文件语法
docker run --rm -v /home/ubuntu/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus promtool check config /etc/prometheus/prometheus.yml

# 查看日志
docker logs nautilus-prometheus

# 检查端口占用
netstat -tuln | grep 9090
```

### Grafana 无法访问
```bash
# 检查容器状态
docker ps | grep grafana

# 查看日志
docker logs nautilus-grafana

# 重置管理员密码
docker exec -it nautilus-grafana grafana-cli admin reset-admin-password nautilus2024
```

### Targets 显示 DOWN
```bash
# 检查目标服务是否运行
curl http://localhost:8000/metrics

# 检查网络连接
telnet localhost 8000

# 查看 Prometheus 日志
docker logs nautilus-prometheus | grep -i error
```

## 告警测试

### 触发测试告警
```bash
# 发送测试告警到 AlertManager
curl -X POST http://localhost:9093/api/v1/alerts -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert"
    }
  }
]'

# 查看告警状态
curl http://localhost:9093/api/v2/alerts | jq .
```

## 备份与恢复

### 备份
```bash
# 备份所有监控数据
sudo tar -czf monitoring-backup-$(date +%Y%m%d).tar.gz /home/ubuntu/monitoring/

# 仅备份配置文件
sudo tar -czf monitoring-config-$(date +%Y%m%d).tar.gz \
  /home/ubuntu/monitoring/prometheus/prometheus.yml \
  /home/ubuntu/monitoring/prometheus/alerting_rules.yml \
  /home/ubuntu/monitoring/alertmanager/alertmanager.yml
```

### 恢复
```bash
# 恢复数据
sudo tar -xzf monitoring-backup-20260302.tar.gz -C /

# 重启服务
docker restart nautilus-prometheus nautilus-grafana nautilus-alertmanager
```

## 性能优化

### 减少 Prometheus 内存使用
```bash
# 调整抓取间隔（在 prometheus.yml 中）
global:
  scrape_interval: 30s  # 从 15s 增加到 30s

# 减少数据保留时间
docker update --restart=always nautilus-prometheus
docker exec nautilus-prometheus kill -HUP 1
```

### 清理旧数据
```bash
# 删除 Prometheus 旧数据
docker exec nautilus-prometheus rm -rf /prometheus/wal

# 压缩数据
docker exec nautilus-prometheus promtool tsdb compact /prometheus
```

## 安全配置

### 限制外网访问
```bash
# 使用防火墙限制访问
sudo ufw allow from YOUR_IP to any port 9090
sudo ufw allow from YOUR_IP to any port 3001
sudo ufw allow from YOUR_IP to any port 9093
```

### 启用 Grafana HTTPS
```bash
# 使用 Nginx 反向代理
sudo apt install nginx certbot python3-certbot-nginx

# 配置 SSL
sudo certbot --nginx -d grafana.nautilus.social
```

## 监控指标说明

### 应用指标
- `nautilus_app_info`: 应用信息（版本、环境）
- `nautilus_http_requests_total`: HTTP 请求总数
- `nautilus_http_request_duration_seconds`: 请求响应时间
- `nautilus_tasks_total`: 任务总数
- `nautilus_agents_active`: 活跃 Agent 数

### 系统指标
- `process_resident_memory_bytes`: 常驻内存
- `process_cpu_seconds_total`: CPU 使用时间
- `process_open_fds`: 打开的文件描述符
- `node_cpu_seconds_total`: 系统 CPU 使用
- `node_memory_MemAvailable_bytes`: 可用内存

### 数据库指标
- `nautilus_database_connections`: 数据库连接数
- `nautilus_database_query_duration_seconds`: 查询时长
- `nautilus_database_errors_total`: 数据库错误数

## 告警规则说明

### P0 关键告警
- `ServiceDown`: 服务不可用
- `HighErrorRate`: 错误率 > 5%
- `DatabaseConnectionFailed`: 数据库连接失败
- `BlockchainDisconnected`: 区块链连接断开

### P1 重要告警
- `HighAPILatency`: P95 响应时间 > 2s
- `SlowDatabaseQueries`: 数据库查询 > 1s
- `HighMemoryUsage`: 内存使用 > 1.8GB

### P2 一般告警
- `LowAPIRequestRate`: 请求量异常下降
- `TaskQueueBacklog`: 任务队列积压 > 100
- `HighCPUUsage`: CPU 使用率 > 80%

## 联系方式

- **技术支持**: devops@nautilus.social
- **文档**: https://docs.nautilus.social/monitoring
- **问题反馈**: https://github.com/nautilus/issues

---

**版本**: 1.0
**更新**: 2026-03-02

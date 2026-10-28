# Prometheus 监控设置指南

## 概述

Nautilus API 集成了 Prometheus 指标收集，提供全面的性能监控和告警能力。

## 可用指标

### HTTP 请求指标

- **http_requests_total**: 总HTTP请求数
  - Labels: `method`, `endpoint`, `status`
  - Type: Counter

- **http_request_duration_seconds**: HTTP请求持续时间
  - Labels: `method`, `endpoint`
  - Type: Histogram
  - Buckets: 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0

- **http_requests_in_progress**: 当前进行中的HTTP请求
  - Labels: `method`, `endpoint`
  - Type: Gauge

### 缓存指标

- **cache_hits_total**: 缓存命中总数
  - Labels: `cache_key`
  - Type: Counter

- **cache_misses_total**: 缓存未命中总数
  - Labels: `cache_key`
  - Type: Counter

- **cache_hit_rate**: 缓存命中率 (0-1)
  - Labels: `cache_key`
  - Type: Gauge

### 数据库指标

- **db_query_duration_seconds**: 数据库查询持续时间
  - Labels: `query_type`
  - Type: Histogram
  - Buckets: 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0

- **db_connections_active**: 活跃数据库连接数
  - Type: Gauge

### Redis 指标

- **redis_operations_total**: Redis操作总数
  - Labels: `operation`, `status`
  - Type: Counter

- **redis_operation_duration_seconds**: Redis操作持续时间
  - Labels: `operation`
  - Type: Histogram
  - Buckets: 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5

## Prometheus 配置

### 1. 安装 Prometheus

```bash
# Docker 方式
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 2. 配置 prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nautilus-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/prometheus'
    scrape_interval: 15s
```

### 3. 验证配置

访问 Prometheus UI: http://localhost:9090

查询示例：
```promql
# 查看所有HTTP请求
http_requests_total

# 查看特定端点的请求率
rate(http_requests_total{endpoint="/api/agents"}[5m])

# 查看P95响应时间
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 查看缓存命中率
cache_hit_rate{cache_key="agents_list"}
```

## Grafana 仪表板

### 1. 安装 Grafana

```bash
# Docker 方式
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

### 2. 添加 Prometheus 数据源

1. 访问 Grafana: http://localhost:3000 (默认: admin/admin)
2. Configuration → Data Sources → Add data source
3. 选择 Prometheus
4. URL: http://prometheus:9090
5. Save & Test

### 3. 导入仪表板

创建新仪表板，添加以下面板：

#### API 性能面板

```json
{
  "title": "API Request Rate",
  "targets": [
    {
      "expr": "rate(http_requests_total[5m])",
      "legendFormat": "{{method}} {{endpoint}}"
    }
  ]
}
```

#### 响应时间面板

```json
{
  "title": "API Response Time (P95)",
  "targets": [
    {
      "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
      "legendFormat": "{{endpoint}}"
    }
  ]
}
```

#### 缓存命中率面板

```json
{
  "title": "Cache Hit Rate",
  "targets": [
    {
      "expr": "cache_hit_rate",
      "legendFormat": "{{cache_key}}"
    }
  ]
}
```

#### 错误率面板

```json
{
  "title": "Error Rate",
  "targets": [
    {
      "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
      "legendFormat": "{{endpoint}}"
    }
  ]
}
```

## 告警规则

### 1. 创建 alerts.yml

```yaml
groups:
  - name: nautilus_alerts
    interval: 30s
    rules:
      # 高响应时间告警
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
          description: "P95 response time is {{ $value }}s (threshold: 0.5s)"

      # 高错误率告警
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 1%)"

      # 低缓存命中率告警
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 0.6
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate for {{ $labels.cache_key }} is {{ $value | humanizePercentage }} (threshold: 60%)"

      # 数据库连接池耗尽告警
      - alert: DatabaseConnectionPoolExhausted
        expr: db_connections_active > 45
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool near exhaustion"
          description: "Active connections: {{ $value }} (max: 50)"

      # Redis 操作失败告警
      - alert: RedisOperationFailures
        expr: rate(redis_operations_total{status="failure"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Redis operation failure rate"
          description: "Redis failures: {{ $value }}/s"
```

### 2. 配置 Alertmanager

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://your-webhook-url'
```

## 性能基准

### 目标指标

- **P95 响应时间**: < 500ms
- **错误率**: < 1%
- **缓存命中率**: > 60%
- **吞吐量**: > 10 req/s

### 监控查询

```promql
# P95 响应时间
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 错误率
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# 缓存命中率
sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))

# 吞吐量
rate(http_requests_total[5m])
```

## 故障排查

### 高响应时间

1. 检查数据库查询性能
   ```promql
   histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))
   ```

2. 检查缓存命中率
   ```promql
   cache_hit_rate
   ```

3. 检查并发请求数
   ```promql
   http_requests_in_progress
   ```

### 高错误率

1. 按端点查看错误
   ```promql
   rate(http_requests_total{status=~"5.."}[5m])
   ```

2. 检查数据库连接
   ```promql
   db_connections_active
   ```

3. 检查 Redis 状态
   ```promql
   rate(redis_operations_total{status="failure"}[5m])
   ```

## 最佳实践

1. **设置合理的告警阈值**
   - 基于历史数据调整阈值
   - 避免告警疲劳

2. **定期审查指标**
   - 每周查看性能趋势
   - 识别性能退化

3. **优化查询**
   - 使用 rate() 而非 irate()
   - 合理设置时间窗口

4. **保留历史数据**
   - 配置 Prometheus 数据保留期
   - 考虑使用远程存储

5. **监控监控系统**
   - 确保 Prometheus 正常运行
   - 监控抓取失败率

## 相关文档

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [PromQL 查询语言](https://prometheus.io/docs/prometheus/latest/querying/basics/)

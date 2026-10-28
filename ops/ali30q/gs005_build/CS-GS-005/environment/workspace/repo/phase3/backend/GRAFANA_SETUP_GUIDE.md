# Grafana 配置指南

## 目录
- [访问Grafana](#访问grafana)
- [配置数据源](#配置数据源)
- [导入仪表板](#导入仪表板)
- [配置告警](#配置告警)
- [常用查询示例](#常用查询示例)
- [故障排查](#故障排查)

---

## 访问Grafana

### 1. 启动监控服务

```bash
# 进入项目目录
cd /c/Users/chunx/Projects/nautilus-core/phase3/backend

# 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 验证服务状态
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. 访问Grafana界面

- **URL**: http://localhost:3001
- **用户名**: admin
- **密码**: admin（首次登录后会要求修改）

### 3. 验证服务健康状态

```bash
# 检查Grafana健康状态
curl http://localhost:3001/api/health

# 检查Prometheus连接
curl http://localhost:9090/-/healthy
```

---

## 配置数据源

### 自动配置（推荐）

Grafana已通过provisioning自动配置Prometheus数据源：

- 配置文件: `monitoring/grafana/provisioning/datasources/prometheus.yml`
- 数据源名称: Prometheus
- URL: http://prometheus:9090

### 手动验证数据源

1. 登录Grafana
2. 导航到: Configuration → Data Sources
3. 点击 "Prometheus" 数据源
4. 点击 "Save & Test" 验证连接

### 手动添加数据源（如需要）

```bash
# 使用API添加数据源
curl -X POST http://admin:admin@localhost:3001/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

---

## 导入仪表板

### 方法1: 自动加载（推荐）

仪表板已配置为自动加载：

- 仪表板文件: `monitoring/grafana/dashboards/nautilus-overview.json`
- 配置文件: `monitoring/grafana/provisioning/dashboards/dashboards.yml`

重启Grafana后自动加载：

```bash
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### 方法2: 手动导入

1. 登录Grafana
2. 点击左侧菜单 "+" → "Import"
3. 选择 "Upload JSON file"
4. 选择文件: `monitoring/grafana/dashboards/nautilus-overview.json`
5. 选择数据源: Prometheus
6. 点击 "Import"

### 方法3: 使用API导入

```bash
# 导入仪表板
curl -X POST http://admin:admin@localhost:3001/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/nautilus-overview.json
```

### 验证仪表板

1. 导航到: Dashboards → Browse
2. 查找 "Nautilus 系统监控总览"
3. 点击打开仪表板

---

## 配置告警

### 告警规则文件

告警规则已定义在: `monitoring/grafana/alerts/nautilus-alerts.yml`

### 告警类别

#### 1. API性能告警
- **API响应时间过长**: P95响应时间 > 1秒
- **API错误率过高**: 5xx错误率 > 5%
- **数据库查询缓慢**: 平均查询时间 > 500ms
- **缓存命中率过低**: 命中率 < 70%

#### 2. 系统资源告警
- **CPU使用率过高**: > 80%
- **内存使用率过高**: > 85%
- **磁盘使用率过高**: > 85%
- **服务不可用**: 服务宕机

#### 3. 业务告警
- **请求量异常**: 与1小时前相比变化 > 50%
- **数据库连接池耗尽**: 使用率 > 90%

### 配置告警通知

#### 1. 配置邮件通知

1. 导航到: Alerting → Contact points
2. 点击 "New contact point"
3. 配置邮件设置：
   - Name: Email Notifications
   - Integration: Email
   - Addresses: your-email@example.com

#### 2. 配置Slack通知

1. 创建Slack Webhook URL
2. 在Grafana中添加Contact point：
   - Name: Slack Notifications
   - Integration: Slack
   - Webhook URL: your-slack-webhook-url

#### 3. 配置通知策略

1. 导航到: Alerting → Notification policies
2. 配置路由规则：
   - Critical告警 → 立即通知
   - Warning告警 → 5分钟后通知
   - Info告警 → 仅记录日志

### 导入告警规则

```bash
# 方法1: 通过Grafana UI
# 1. 导航到: Alerting → Alert rules
# 2. 点击 "Import"
# 3. 上传 nautilus-alerts.yml

# 方法2: 通过API（需要转换为JSON格式）
# Grafana的告警规则API需要JSON格式，YAML文件需要手动导入
```

---

## 常用查询示例

### API监控查询

#### 1. 请求速率（QPS）

```promql
# 总请求速率
rate(http_requests_total{job="nautilus-api"}[5m])

# 按端点分组
sum by (endpoint) (rate(http_requests_total{job="nautilus-api"}[5m]))

# 按HTTP方法分组
sum by (method) (rate(http_requests_total{job="nautilus-api"}[5m]))
```

#### 2. 响应时间

```promql
# P50响应时间
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job="nautilus-api"}[5m])) * 1000

# P95响应时间
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="nautilus-api"}[5m])) * 1000

# P99响应时间
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job="nautilus-api"}[5m])) * 1000
```

#### 3. 错误率

```promql
# 4xx错误率
rate(http_requests_total{job="nautilus-api",status=~"4.."}[5m]) / rate(http_requests_total{job="nautilus-api"}[5m]) * 100

# 5xx错误率
rate(http_requests_total{job="nautilus-api",status=~"5.."}[5m]) / rate(http_requests_total{job="nautilus-api"}[5m]) * 100

# 总错误率
rate(http_requests_total{job="nautilus-api",status=~"[45].."}[5m]) / rate(http_requests_total{job="nautilus-api"}[5m]) * 100
```

### 数据库监控查询

#### 1. 查询性能

```promql
# 平均查询时间
rate(db_query_duration_seconds_sum{job="nautilus-api"}[5m]) / rate(db_query_duration_seconds_count{job="nautilus-api"}[5m]) * 1000

# 按查询类型分组
rate(db_query_duration_seconds_sum{job="nautilus-api"}[5m]) by (query_type) / rate(db_query_duration_seconds_count{job="nautilus-api"}[5m]) by (query_type) * 1000
```

#### 2. 连接池状态

```promql
# 活跃连接数
db_connection_pool_active{job="nautilus-api"}

# 连接池使用率
db_connection_pool_active{job="nautilus-api"} / db_connection_pool_max{job="nautilus-api"} * 100

# 等待连接数
db_connection_pool_waiting{job="nautilus-api"}
```

### 缓存监控查询

#### 1. 缓存命中率

```promql
# 总体命中率
(rate(cache_hits_total{job="nautilus-api"}[5m]) / (rate(cache_hits_total{job="nautilus-api"}[5m]) + rate(cache_misses_total{job="nautilus-api"}[5m]))) * 100

# 按缓存类型分组
(rate(cache_hits_total{job="nautilus-api"}[5m]) by (cache_type) / (rate(cache_hits_total{job="nautilus-api"}[5m]) by (cache_type) + rate(cache_misses_total{job="nautilus-api"}[5m]) by (cache_type))) * 100
```

#### 2. 缓存操作

```promql
# 缓存命中次数
rate(cache_hits_total{job="nautilus-api"}[5m])

# 缓存未命中次数
rate(cache_misses_total{job="nautilus-api"}[5m])

# 缓存写入次数
rate(cache_writes_total{job="nautilus-api"}[5m])
```

### 系统资源查询

#### 1. CPU使用率

```promql
# 总体CPU使用率
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 按CPU核心分组
100 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100)
```

#### 2. 内存使用

```promql
# 内存使用率
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# 已用内存（GB）
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024 / 1024

# 可用内存（GB）
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024
```

#### 3. 磁盘使用

```promql
# 磁盘使用率
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100

# 已用磁盘空间（GB）
(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"}) / 1024 / 1024 / 1024

# 可用磁盘空间（GB）
node_filesystem_avail_bytes{mountpoint="/"} / 1024 / 1024 / 1024
```

#### 4. 网络流量

```promql
# 网络接收速率（MB/s）
rate(node_network_receive_bytes_total[5m]) / 1024 / 1024

# 网络发送速率（MB/s）
rate(node_network_transmit_bytes_total[5m]) / 1024 / 1024
```

---

## 故障排查

### 问题1: Grafana无法访问

**症状**: 无法打开 http://localhost:3001

**解决方案**:

```bash
# 1. 检查容器状态
docker ps | grep grafana

# 2. 查看容器日志
docker logs nautilus-grafana

# 3. 检查端口占用
netstat -ano | grep :3001

# 4. 重启Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana

# 5. 如果仍然失败，重新创建容器
docker-compose -f docker-compose.monitoring.yml down
docker-compose -f docker-compose.monitoring.yml up -d
```

### 问题2: 数据源连接失败

**症状**: Grafana显示 "Data source is not working"

**解决方案**:

```bash
# 1. 检查Prometheus状态
curl http://localhost:9090/-/healthy

# 2. 检查容器网络
docker network inspect nautilus_monitoring

# 3. 从Grafana容器内测试连接
docker exec nautilus-grafana wget -O- http://prometheus:9090/api/v1/status/config

# 4. 检查数据源配置
cat monitoring/grafana/provisioning/datasources/prometheus.yml

# 5. 重启Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

### 问题3: 仪表板无数据

**症状**: 仪表板显示 "No data"

**解决方案**:

```bash
# 1. 验证Prometheus有数据
curl http://localhost:9090/api/v1/query?query=up

# 2. 检查应用是否暴露指标
curl http://localhost:8000/metrics

# 3. 检查Prometheus配置
cat monitoring/prometheus.yml

# 4. 验证Prometheus targets
curl http://localhost:9090/api/v1/targets

# 5. 检查时间范围设置
# 在Grafana仪表板右上角调整时间范围
```

### 问题4: 告警不触发

**症状**: 告警规则配置了但不触发

**解决方案**:

```bash
# 1. 检查告警规则状态
# 在Grafana UI: Alerting → Alert rules

# 2. 验证查询返回数据
# 在Grafana UI: Explore → 输入告警查询

# 3. 检查告警评估间隔
# 确保 interval 和 for 参数设置合理

# 4. 查看告警历史
# 在Grafana UI: Alerting → Alert rules → 点击规则 → State history

# 5. 检查通知渠道配置
# 在Grafana UI: Alerting → Contact points
```

### 问题5: 仪表板加载缓慢

**症状**: 仪表板打开很慢或超时

**解决方案**:

```bash
# 1. 优化查询时间范围
# 减少查询的时间范围（如从24h改为6h）

# 2. 调整刷新间隔
# 在仪表板设置中增加刷新间隔（如从10s改为30s）

# 3. 优化PromQL查询
# 使用更短的rate/increase时间窗口
# 减少不必要的label分组

# 4. 增加Prometheus查询超时
# 编辑 monitoring/grafana/provisioning/datasources/prometheus.yml
# 增加 queryTimeout 值

# 5. 检查Prometheus性能
docker stats nautilus-prometheus
```

### 问题6: 告警通知未收到

**症状**: 告警触发了但没有收到通知

**解决方案**:

```bash
# 1. 测试通知渠道
# 在Grafana UI: Alerting → Contact points → Test

# 2. 检查通知策略
# 在Grafana UI: Alerting → Notification policies

# 3. 查看通知历史
# 在Grafana UI: Alerting → Contact points → 查看发送历史

# 4. 检查邮件配置（如使用邮件通知）
# 编辑 docker-compose.monitoring.yml
# 添加SMTP配置环境变量

# 5. 查看Grafana日志
docker logs nautilus-grafana | grep -i notification
```

### 常用调试命令

```bash
# 查看所有监控容器状态
docker-compose -f docker-compose.monitoring.yml ps

# 查看所有容器日志
docker-compose -f docker-compose.monitoring.yml logs

# 查看特定容器日志
docker logs nautilus-grafana -f
docker logs nautilus-prometheus -f

# 进入容器调试
docker exec -it nautilus-grafana /bin/bash
docker exec -it nautilus-prometheus /bin/sh

# 重启所有监控服务
docker-compose -f docker-compose.monitoring.yml restart

# 完全重建监控服务
docker-compose -f docker-compose.monitoring.yml down -v
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 最佳实践

### 1. 仪表板使用

- 使用变量（Variables）使仪表板更灵活
- 设置合理的刷新间隔（推荐30s-1m）
- 使用文件夹组织多个仪表板
- 定期导出仪表板备份

### 2. 告警配置

- 设置合理的阈值，避免告警疲劳
- 使用 `for` 参数避免瞬时波动触发告警
- 配置告警分级（Critical/Warning/Info）
- 定期审查和优化告警规则

### 3. 性能优化

- 限制查询时间范围
- 使用合适的rate/increase时间窗口
- 避免过多的label分组
- 定期清理旧数据

### 4. 安全建议

- 修改默认管理员密码
- 启用HTTPS（生产环境）
- 配置用户权限和角色
- 定期更新Grafana版本

---

## 相关资源

- Grafana官方文档: https://grafana.com/docs/
- Prometheus查询语法: https://prometheus.io/docs/prometheus/latest/querying/basics/
- 仪表板示例: https://grafana.com/grafana/dashboards/
- 告警配置指南: https://grafana.com/docs/grafana/latest/alerting/

---

## 支持

如有问题，请联系：
- 技术支持: support@nautilus.com
- 文档反馈: docs@nautilus.com

# Nautilus 日志聚合系统配置文档

## 系统架构

```
应用日志 → Promtail → Loki → Grafana
  ↓
/var/log/nautilus-backend.log
/var/log/nautilus-backend-error.log
/var/log/nginx/access.log
/var/log/nginx/error.log
```

## 已安装组件

### 1. Loki (日志聚合服务)
- **版本**: 2.9.3
- **端口**: 3100
- **配置文件**: `/home/ubuntu/loki-config/loki-config.yaml`
- **数据目录**: `/home/ubuntu/loki-data`
- **容器名**: `loki`

### 2. Promtail (日志采集器)
- **版本**: 2.9.3
- **端口**: 9080
- **配置文件**: `/home/ubuntu/promtail-config/promtail-config.yaml`
- **容器名**: `promtail`

## 配置详情

### Loki 配置

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20

table_manager:
  retention_deletes_enabled: true
  retention_period: 168h  # 7 days
```

### Promtail 配置

采集以下日志文件：

| 日志文件 | Job 名称 | 标签 |
|---------|---------|------|
| `/var/log/nautilus-backend.log` | nautilus-backend | host=nautilus-server |
| `/var/log/nautilus-backend-error.log` | nautilus-backend-error | host=nautilus-server, level=error |
| `/var/log/nginx/access.log` | nginx | type=access |
| `/var/log/nginx/error.log` | nginx | type=error |

## 使用方法

### 1. 检查服务状态

```bash
# 检查 Loki 状态
docker ps | grep loki
curl http://localhost:3100/ready

# 检查 Promtail 状态
docker ps | grep promtail
docker logs promtail --tail 20
```

### 2. 查询日志

#### 使用 curl 查询

```bash
# 查询所有 nautilus-backend 日志
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend"}' \
  --data-urlencode 'limit=10'

# 查询错误日志
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend-error"}' \
  --data-urlencode 'limit=10'

# 查询包含特定关键词的日志
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend"} |= "error"' \
  --data-urlencode 'limit=10'

# 查询最近 1 小时的日志
START=$(date -d '1 hour ago' +%s)000000000
END=$(date +%s)000000000
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend"}' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode 'limit=10'
```

#### 使用脚本查询

```bash
# 运行查询示例脚本
bash scripts/loki-queries.sh

# 运行日志分析脚本
bash scripts/analyze-logs.sh
```

### 3. LogQL 查询语法

#### 基础查询

```logql
# 查询特定 job 的日志
{job="nautilus-backend"}

# 查询特定 job 和 level 的日志
{job="nautilus-backend-error", level="error"}

# 查询多个 job
{job=~"nautilus-backend|nginx"}
```

#### 过滤器

```logql
# 包含特定文本
{job="nautilus-backend"} |= "error"

# 不包含特定文本
{job="nautilus-backend"} != "debug"

# 正则匹配
{job="nautilus-backend"} |~ "error|warning"

# 正则不匹配
{job="nautilus-backend"} !~ "debug|trace"
```

#### 聚合查询

```logql
# 统计日志行数
count_over_time({job="nautilus-backend"}[5m])

# 统计错误率
sum(rate({job="nautilus-backend-error"}[5m]))

# 按标签分组统计
sum by (job) (count_over_time({job=~"nautilus.*"}[1h]))
```

### 4. 在 Grafana 中配置

1. 登录 Grafana (http://your-server:3000)
2. 进入 Configuration → Data Sources
3. 点击 "Add data source"
4. 选择 "Loki"
5. 配置：
   - Name: `Loki`
   - URL: `http://localhost:3100`
   - Access: `Server (default)`
6. 点击 "Save & Test"

### 5. 创建 Grafana Dashboard

#### 常用面板查询

**错误日志面板**:
```logql
{job="nautilus-backend-error"}
```

**错误率面板**:
```logql
sum(rate({job="nautilus-backend-error"}[5m]))
```

**日志量趋势**:
```logql
sum by (job) (count_over_time({job=~"nautilus.*"}[1m]))
```

**Nginx 状态码分布**:
```logql
{job="nginx", type="access"} | pattern `<_> <_> <_> <_> "<_>" <status> <_>` | status >= 400
```

## 告警配置

### 1. 创建告警规则文件

```bash
ssh cloud "cat > /home/ubuntu/loki-config/rules.yaml << 'EOF'
groups:
  - name: nautilus_logs
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({job=\"nautilus-backend-error\"}[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: \"High error rate in Nautilus backend\"
          description: \"Error rate is {{ \$value }} errors/sec\"

      - alert: DatabaseError
        expr: |
          count_over_time({job=\"nautilus-backend\"} |= \"database error\"[5m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: \"Database errors detected\"
          description: \"{{ \$value }} database errors in last 5 minutes\"

      - alert: NginxHighErrorRate
        expr: |
          sum(rate({job=\"nginx\", type=\"error\"}[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: \"High Nginx error rate\"
          description: \"Nginx error rate is {{ \$value }} errors/sec\"
EOF"
```

### 2. 常见告警场景

| 告警名称 | 条件 | 严重级别 |
|---------|------|---------|
| HighErrorRate | 错误率 > 10/sec | Warning |
| DatabaseError | 数据库错误 > 5次/5分钟 | Critical |
| NginxHighErrorRate | Nginx 错误率 > 5/sec | Warning |
| SlowQuery | 慢查询 > 3次/5分钟 | Warning |

## 日志保留策略

- **保留时间**: 7 天 (168 小时)
- **自动清理**: 启用
- **存储位置**: `/home/ubuntu/loki-data`

## 性能优化

### 1. 日志采集优化

- Promtail 使用只读挂载 (`ro`)
- 限制日志文件大小和轮转
- 使用标签过滤减少数据量

### 2. 查询优化

- 使用时间范围限制查询
- 使用标签过滤而非文本搜索
- 避免查询过长时间范围

### 3. 存储优化

- 定期清理旧日志
- 监控磁盘使用情况
- 考虑使用对象存储（S3/OSS）

## 故障排查

### Loki 无法启动

```bash
# 检查日志
docker logs loki

# 检查配置文件
cat /home/ubuntu/loki-config/loki-config.yaml

# 检查权限
ls -la /home/ubuntu/loki-data

# 重启服务
docker restart loki
```

### Promtail 无法采集日志

```bash
# 检查日志
docker logs promtail

# 检查配置文件
cat /home/ubuntu/promtail-config/promtail-config.yaml

# 检查日志文件权限
ls -la /var/log/nautilus*

# 重启服务
docker restart promtail
```

### 查询无数据

```bash
# 检查 Loki 是否就绪
curl http://localhost:3100/ready

# 检查可用的标签
curl -s http://localhost:3100/loki/api/v1/labels

# 检查特定 job 的值
curl -s http://localhost:3100/loki/api/v1/label/job/values

# 检查 Promtail 是否正在采集
docker logs promtail | grep "Adding target"
```

## 维护任务

### 每日检查

```bash
# 检查服务状态
docker ps | grep -E "(loki|promtail)"

# 检查磁盘使用
du -sh /home/ubuntu/loki-data

# 运行日志分析
bash scripts/analyze-logs.sh
```

### 每周检查

```bash
# 检查日志保留情况
ls -lh /home/ubuntu/loki-data/chunks

# 检查错误趋势
bash scripts/loki-queries.sh

# 备份配置文件
tar -czf loki-config-backup-$(date +%Y%m%d).tar.gz \
  /home/ubuntu/loki-config \
  /home/ubuntu/promtail-config
```

## 扩展功能

### 1. 集成 Alertmanager

```bash
# 安装 Alertmanager
docker run -d --name alertmanager \
  --restart=always \
  -p 9093:9093 \
  -v /home/ubuntu/alertmanager-config:/etc/alertmanager \
  prom/alertmanager:latest
```

### 2. 添加更多日志源

编辑 `/home/ubuntu/promtail-config/promtail-config.yaml`，添加新的 `scrape_configs`。

### 3. 使用对象存储

修改 Loki 配置，使用 S3 或 OSS 作为后端存储。

## 参考资源

- [Loki 官方文档](https://grafana.com/docs/loki/latest/)
- [Promtail 配置](https://grafana.com/docs/loki/latest/clients/promtail/)
- [LogQL 查询语法](https://grafana.com/docs/loki/latest/logql/)
- [Grafana Dashboard](https://grafana.com/grafana/dashboards/)

# Nautilus 日志聚合系统 - 快速参考

## 服务管理

### 检查服务状态
```bash
ssh cloud "docker ps | grep -E '(loki|promtail)'"
```

### 重启服务
```bash
# 重启 Loki
ssh cloud "docker restart loki"

# 重启 Promtail
ssh cloud "docker restart promtail"

# 重启所有日志服务
ssh cloud "docker restart loki promtail"
```

### 查看日志
```bash
# Loki 日志
ssh cloud "docker logs loki --tail 50"

# Promtail 日志
ssh cloud "docker logs promtail --tail 50"

# 实时跟踪
ssh cloud "docker logs -f loki"
```

## 日志查询

### 基础查询
```bash
# 查询后端日志
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend"}' \
  --data-urlencode 'limit=10'

# 查询错误日志
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend-error"}' \
  --data-urlencode 'limit=10'
```

### LogQL 查询语法

| 查询 | 说明 |
|------|------|
| `{job="nautilus-backend"}` | 查询特定 job |
| `{job="nautilus-backend"} \|= "error"` | 包含 "error" |
| `{job="nautilus-backend"} !\= "debug"` | 不包含 "debug" |
| `{job="nautilus-backend"} \|~ "error\|warning"` | 正则匹配 |
| `sum(rate({job="nautilus-backend-error"}[5m]))` | 错误率 |
| `count_over_time({job="nautilus-backend"}[1h])` | 日志计数 |

## 工具脚本

### 上传脚本到服务器
```bash
bash scripts/upload-log-scripts.sh
```

### 运行测试
```bash
ssh cloud "bash /home/ubuntu/test-log-system.sh"
```

### 运行日志分析
```bash
ssh cloud "bash /home/ubuntu/analyze-logs.sh"
```

### 运行查询示例
```bash
ssh cloud "bash /home/ubuntu/loki-queries.sh"
```

## Grafana 配置

### 添加 Loki 数据源
1. 访问 Grafana: `http://your-server:3000`
2. Configuration → Data Sources → Add data source
3. 选择 "Loki"
4. URL: `http://localhost:3100`
5. Save & Test

### 导入 Dashboard
1. Dashboards → Import
2. 上传文件: `config/grafana-dashboard-logs.json`
3. 选择 Loki 数据源
4. Import

## 常见问题

### Loki 无法启动
```bash
# 检查日志
ssh cloud "docker logs loki"

# 检查配置
ssh cloud "cat /home/ubuntu/loki-config/loki-config.yaml"

# 检查权限
ssh cloud "ls -la /home/ubuntu/loki-data"

# 修复权限
ssh cloud "sudo chown -R 10001:10001 /home/ubuntu/loki-data"
```

### Promtail 无法采集
```bash
# 检查日志
ssh cloud "docker logs promtail"

# 检查配置
ssh cloud "cat /home/ubuntu/promtail-config/promtail-config.yaml"

# 检查日志文件
ssh cloud "ls -la /var/log/nautilus*"
```

### 查询无数据
```bash
# 检查 Loki 状态
ssh cloud "curl http://localhost:3100/ready"

# 检查可用标签
ssh cloud "curl -s http://localhost:3100/loki/api/v1/label/job/values"

# 检查 Promtail 采集状态
ssh cloud "docker logs promtail | grep 'Adding target'"
```

## 告警规则

已配置的告警：

| 告警名称 | 条件 | 持续时间 | 严重级别 |
|---------|------|---------|---------|
| HighErrorRate | 错误率 > 10/sec | 5m | Warning |
| DatabaseError | 数据库错误 > 5次 | 2m | Critical |
| NginxHighErrorRate | Nginx 错误率 > 5/sec | 5m | Warning |
| SlowQuery | 慢查询 > 3次 | 5m | Warning |
| ServiceDown | 无日志输出 | 2m | Critical |

## 维护任务

### 每日
```bash
# 检查服务状态
ssh cloud "docker ps | grep -E '(loki|promtail)'"

# 检查磁盘使用
ssh cloud "du -sh /home/ubuntu/loki-data"

# 运行日志分析
ssh cloud "bash /home/ubuntu/analyze-logs.sh"
```

### 每周
```bash
# 备份配置
ssh cloud "tar -czf loki-config-backup-\$(date +%Y%m%d).tar.gz \
  /home/ubuntu/loki-config \
  /home/ubuntu/promtail-config"

# 下载备份
scp cloud:/home/ubuntu/loki-config-backup-*.tar.gz ./backups/
```

## 文件位置

### 服务器端
- Loki 配置: `/home/ubuntu/loki-config/loki-config.yaml`
- Promtail 配置: `/home/ubuntu/promtail-config/promtail-config.yaml`
- Loki 数据: `/home/ubuntu/loki-data`
- 告警规则: `/home/ubuntu/loki-config/rules.yaml`
- 脚本: `/home/ubuntu/*.sh`

### 本地
- 脚本: `scripts/`
- 配置: `config/`
- 文档: `docs/`

## 有用的链接

- [Loki 文档](https://grafana.com/docs/loki/latest/)
- [LogQL 语法](https://grafana.com/docs/loki/latest/logql/)
- [Promtail 配置](https://grafana.com/docs/loki/latest/clients/promtail/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

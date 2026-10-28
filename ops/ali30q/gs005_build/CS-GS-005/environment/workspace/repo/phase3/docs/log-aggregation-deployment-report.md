# Nautilus 日志聚合系统部署报告

## 执行摘要

已成功为 Nautilus 配置集中式日志管理系统，使用 Loki + Promtail 方案实现日志收集、存储、查询和分析。

## 已完成的工作

### 1. 核心组件部署

#### Loki (日志聚合服务)
- **状态**: ✅ 已部署并运行
- **版本**: 2.9.3
- **端口**: 3100
- **容器名**: loki
- **配置文件**: `/home/ubuntu/loki-config/loki-config.yaml`
- **数据目录**: `/home/ubuntu/loki-data`
- **日志保留**: 7 天 (168 小时)

#### Promtail (日志采集器)
- **状态**: ✅ 已部署并运行
- **版本**: 2.9.3
- **端口**: 9080
- **容器名**: promtail
- **配置文件**: `/home/ubuntu/promtail-config/promtail-config.yaml`

### 2. 日志采集配置

已配置采集以下日志源：

| 日志文件 | Job 名称 | 标签 | 状态 |
|---------|---------|------|------|
| `/var/log/nautilus-backend.log` | nautilus-backend | host=nautilus-server | ✅ 采集中 |
| `/var/log/nautilus-backend-error.log` | nautilus-backend-error | host=nautilus-server, level=error | ✅ 采集中 |
| `/var/log/nginx/access.log` | nginx | type=access | ✅ 采集中 |
| `/var/log/nginx/error.log` | nginx | type=error | ✅ 采集中 |

### 3. 创建的文件和脚本

#### 配置文件
1. **Loki 配置**: `/home/ubuntu/loki-config/loki-config.yaml`
   - 文件系统存储
   - 7 天日志保留
   - 速率限制: 10MB/s

2. **Promtail 配置**: `/home/ubuntu/promtail-config/promtail-config.yaml`
   - 4 个日志源配置
   - 自动标签分类

3. **告警规则**: `/c/Users/chunx/Projects/nautilus-core/phase3/config/loki-alert-rules.yaml`
   - 高错误率告警
   - 数据库错误告警
   - Nginx 错误告警
   - 慢查询告警
   - 服务宕机告警

#### 工具脚本
1. **日志查询脚本**: `/c/Users/chunx/Projects/nautilus-core/phase3/scripts/loki-queries.sh`
   - 7 种常用查询示例
   - 自动执行查询并显示结果

2. **日志分析脚本**: `/c/Users/chunx/Projects/nautilus-core/phase3/scripts/analyze-logs.sh`
   - 日志文件状态检查
   - Top 10 错误消息统计
   - Nginx 访问统计
   - 服务状态检查

#### 文档
1. **完整配置文档**: `/c/Users/chunx/Projects/nautilus-core/phase3/docs/log-aggregation-setup.md`
   - 系统架构说明
   - 详细配置说明
   - 使用方法和查询示例
   - 故障排查指南
   - 维护任务清单

2. **Grafana Dashboard**: `/c/Users/chunx/Projects/nautilus-core/phase3/config/grafana-dashboard-logs.json`
   - 日志量趋势图
   - 错误率仪表盘
   - 实时日志流
   - Nginx 日志分析

## 验证结果

### 服务状态
```
✅ Loki: 运行中 (Up About a minute)
✅ Promtail: 运行中 (Up 21 seconds)
✅ Loki API: 就绪 (ready)
✅ 日志采集: 4 个目标已添加
```

### 功能验证
- ✅ Loki 服务正常启动
- ✅ Promtail 成功连接到 Loki
- ✅ 日志文件正在被采集
- ✅ API 查询接口可用
- ✅ 标签系统工作正常

## 使用指南

### 快速开始

#### 1. 检查服务状态
```bash
ssh cloud "docker ps | grep -E '(loki|promtail)'"
```

#### 2. 查询日志
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

#### 3. 运行分析脚本
```bash
# 上传脚本到服务器
scp scripts/analyze-logs.sh cloud:/home/ubuntu/
scp scripts/loki-queries.sh cloud:/home/ubuntu/

# 运行分析
ssh cloud "bash /home/ubuntu/analyze-logs.sh"
```

### 在 Grafana 中配置

1. 登录 Grafana: `http://your-server:3000`
2. 添加 Loki 数据源:
   - Configuration → Data Sources → Add data source
   - 选择 "Loki"
   - URL: `http://localhost:3100`
   - 点击 "Save & Test"

3. 导入 Dashboard:
   - Dashboards → Import
   - 上传 `config/grafana-dashboard-logs.json`

### 常用 LogQL 查询

```logql
# 查询所有后端日志
{job="nautilus-backend"}

# 查询包含错误的日志
{job="nautilus-backend"} |= "error"

# 查询错误率
sum(rate({job="nautilus-backend-error"}[5m]))

# 按 job 统计日志量
sum by (job) (count_over_time({job=~"nautilus.*"}[1h]))

# 查询 Nginx 4xx/5xx 错误
{job="nginx", type="access"} | pattern `<_> <_> <_> <_> "<_>" <status> <_>` | status >= 400
```

## 告警配置

已创建 5 个告警规则：

1. **HighErrorRate**: 错误率 > 10/sec，持续 5 分钟
2. **DatabaseError**: 数据库错误 > 5 次/5 分钟
3. **NginxHighErrorRate**: Nginx 错误率 > 5/sec
4. **SlowQuery**: 慢查询 > 3 次/5 分钟
5. **ServiceDown**: 服务无日志输出超过 5 分钟

要启用告警，需要配置 Alertmanager 或在 Grafana 中设置告警通知。

## 性能和存储

### 当前配置
- **日志保留期**: 7 天
- **摄入速率限制**: 10 MB/s
- **突发限制**: 20 MB/s
- **存储类型**: 本地文件系统

### 预估存储需求
假设日志量为 1 MB/小时：
- 每天: ~24 MB
- 7 天: ~168 MB

实际存储需求取决于应用日志量。

## 维护建议

### 每日检查
```bash
# 检查服务状态
ssh cloud "docker ps | grep -E '(loki|promtail)'"

# 检查磁盘使用
ssh cloud "du -sh /home/ubuntu/loki-data"

# 运行日志分析
ssh cloud "bash /home/ubuntu/analyze-logs.sh"
```

### 每周检查
```bash
# 检查日志保留情况
ssh cloud "ls -lh /home/ubuntu/loki-data/chunks"

# 备份配置文件
ssh cloud "tar -czf loki-config-backup-\$(date +%Y%m%d).tar.gz \
  /home/ubuntu/loki-config \
  /home/ubuntu/promtail-config"
```

### 故障排查

#### Loki 无法启动
```bash
docker logs loki
docker restart loki
```

#### Promtail 无法采集
```bash
docker logs promtail
docker restart promtail
```

#### 查询无数据
```bash
# 检查可用标签
curl -s http://localhost:3100/loki/api/v1/label/job/values

# 检查 Promtail 采集状态
docker logs promtail | grep "Adding target"
```

## 下一步优化

### 短期优化
1. 配置 Alertmanager 实现告警通知
2. 在 Grafana 中创建更多可视化面板
3. 添加更多应用日志源
4. 配置日志轮转策略

### 长期优化
1. 考虑使用对象存储（S3/OSS）降低成本
2. 实施日志采样减少存储
3. 配置多副本提高可用性
4. 集成 Tempo 实现分布式追踪

## 相关文件

### 配置文件
- `/home/ubuntu/loki-config/loki-config.yaml` - Loki 主配置
- `/home/ubuntu/promtail-config/promtail-config.yaml` - Promtail 配置
- `/c/Users/chunx/Projects/nautilus-core/phase3/config/loki-alert-rules.yaml` - 告警规则

### 脚本
- `/c/Users/chunx/Projects/nautilus-core/phase3/scripts/loki-queries.sh` - 查询示例
- `/c/Users/chunx/Projects/nautilus-core/phase3/scripts/analyze-logs.sh` - 日志分析

### 文档
- `/c/Users/chunx/Projects/nautilus-core/phase3/docs/log-aggregation-setup.md` - 完整文档
- `/c/Users/chunx/Projects/nautilus-core/phase3/config/grafana-dashboard-logs.json` - Grafana Dashboard

## 总结

日志聚合系统已成功部署并运行。系统能够：
- ✅ 自动采集 4 个日志源
- ✅ 提供强大的查询和过滤能力
- ✅ 支持实时日志流和历史查询
- ✅ 配置了 5 个告警规则
- ✅ 提供完整的文档和工具脚本

系统已准备好用于生产环境的日志监控和问题排查。

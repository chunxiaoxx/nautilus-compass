# Grafana 监控配置

本目录包含Nautilus项目的Grafana监控配置文件。

## 目录结构

```
grafana/
├── provisioning/          # Grafana自动配置
│   ├── datasources/      # 数据源配置
│   │   └── prometheus.yml
│   └── dashboards/       # 仪表板provider配置
│       └── dashboards.yml
├── dashboards/           # 仪表板JSON文件
│   └── nautilus-overview.json
├── alerts/              # 告警规则配置
│   └── nautilus-alerts.yml
└── README.md           # 本文件
```

## 快速开始

### 1. 启动Grafana

```bash
# 启动所有监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 仅启动Grafana
docker-compose -f docker-compose.monitoring.yml up -d grafana
```

### 2. 访问Grafana

- URL: http://localhost:3001
- 用户名: admin
- 密码: admin

### 3. 验证配置

仪表板会自动加载，访问 Dashboards → Browse 查看 "Nautilus 系统监控总览"。

## 配置文件说明

### 仪表板配置

**nautilus-overview.json** - 主监控仪表板

包含8个监控面板：
1. API请求速率 - 监控API请求量
2. API响应时间 - P95/P99响应时间
3. 数据库查询性能 - 数据库查询时间
4. 缓存命中率 - 缓存效率
5. CPU使用率 - 系统CPU监控
6. 内存使用率 - 系统内存监控
7. 磁盘使用率 - 系统磁盘监控
8. 告警状态 - 当前告警显示

### 告警规则配置

**nautilus-alerts.yml** - 告警规则定义

包含10条告警规则：

**API性能告警**
- API响应时间过长 (P95 > 1秒)
- API错误率过高 (5xx > 5%)
- 数据库查询缓慢 (平均 > 500ms)
- 缓存命中率过低 (< 70%)

**系统资源告警**
- CPU使用率过高 (> 80%)
- 内存使用率过高 (> 85%)
- 磁盘使用率过高 (> 85%)
- 服务不可用

**业务告警**
- 请求量异常 (变化 > 50%)
- 数据库连接池耗尽 (> 90%)

## 导入告警规则

告警规则需要手动导入：

1. 登录Grafana
2. 导航到 Alerting → Alert rules
3. 点击 Import
4. 上传 `alerts/nautilus-alerts.yml`

## 自定义配置

### 修改仪表板

1. 在Grafana UI中打开仪表板
2. 进行修改
3. 点击 Save dashboard
4. 导出JSON文件替换 `dashboards/nautilus-overview.json`

### 修改告警规则

直接编辑 `alerts/nautilus-alerts.yml` 文件，然后重新导入。

### 添加新仪表板

1. 在Grafana UI中创建新仪表板
2. 导出为JSON
3. 保存到 `dashboards/` 目录
4. 重启Grafana自动加载

## 故障排查

### 仪表板无数据

```bash
# 检查Prometheus连接
curl http://localhost:9090/-/healthy

# 检查数据源配置
docker exec nautilus-grafana cat /etc/grafana/provisioning/datasources/prometheus.yml

# 重启Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### 告警不触发

1. 检查告警规则状态: Alerting → Alert rules
2. 验证查询返回数据: Explore → 输入告警查询
3. 检查通知渠道配置: Alerting → Contact points

## 相关文档

- [GRAFANA_SETUP_GUIDE.md](../../GRAFANA_SETUP_GUIDE.md) - 完整配置指南
- [GRAFANA_CONFIGURATION_REPORT.md](../../GRAFANA_CONFIGURATION_REPORT.md) - 配置报告
- [Grafana官方文档](https://grafana.com/docs/)

## 维护建议

1. 定期备份仪表板配置
2. 根据实际情况调整告警阈值
3. 定期审查和优化查询性能
4. 保持Grafana版本更新

---

配置日期: 2026-02-26

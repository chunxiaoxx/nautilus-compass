# 日志系统指南

## 概述

Nautilus Backend 使用结构化日志系统，支持 JSON 格式输出，便于日志聚合、查询和分析。

## 日志架构

### 日志组件

1. **结构化日志配置** (`utils/logging_config.py`)
   - JSON 格式日志输出
   - 多种日志处理器（控制台、文件、错误）
   - 上下文信息注入

2. **日志中间件** (`middleware/logging_middleware.py`)
   - 自动记录所有 HTTP 请求/响应
   - 性能监控
   - 错误追踪

3. **日志聚合配置**
   - Promtail 配置 (`config/logging/promtail.yml`)
   - Filebeat 配置 (`config/logging/filebeat.yml`)

4. **日志分析工具** (`scripts/analyze_logs.py`)
   - 错误统计
   - 性能分析
   - 异常检测

## 日志格式

### JSON 日志结构

```json
{
  "timestamp": "2026-02-27T10:30:45.123456Z",
  "level": "INFO",
  "logger": "api.tasks",
  "message": "Task created successfully",
  "service": "nautilus-backend",
  "environment": "production",
  "hostname": "app-server-01",
  "process": {
    "pid": 12345,
    "name": "MainProcess"
  },
  "thread": {
    "id": 67890,
    "name": "ThreadPoolExecutor-0"
  },
  "source": {
    "file": "/app/api/tasks.py",
    "line": 145,
    "function": "create_task"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user_123",
  "ip_address": "192.168.1.100",
  "http": {
    "method": "POST",
    "path": "/api/tasks",
    "status_code": 201,
    "duration_ms": 125.5
  },
  "extra": {
    "task_id": "task_456",
    "reward": 1000000000000000000
  }
}
```

### 日志级别

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（默认级别）
- **WARNING**: 警告信息（不影响功能）
- **ERROR**: 错误信息（功能受影响）
- **CRITICAL**: 严重错误（系统不可用）

## 使用方法

### 基础日志记录

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

# 基础日志
logger.info("User logged in")
logger.warning("High memory usage detected")
logger.error("Database connection failed")

# 带异常信息
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Operation failed")
```

### 结构化日志记录

```python
from utils.logging_config import StructuredLogger, get_logger

logger = get_logger(__name__)
structured_logger = StructuredLogger(logger)

# 添加自定义字段
structured_logger.info(
    "Task created",
    task_id="task_123",
    user_id="user_456",
    reward=1000000000000000000,
    status="pending"
)

# 性能日志
structured_logger.warning(
    "Slow query detected",
    query_time_ms=1500,
    query="SELECT * FROM tasks",
    threshold_ms=1000
)
```

### 区块链日志

```python
from utils.logging_config import get_blockchain_logger

blockchain_logger = get_blockchain_logger()

# 记录交易
blockchain_logger.info(
    "Transaction submitted",
    extra={
        "extra_fields": {
            "tx_hash": "0x1234567890abcdef",
            "operation": "publish_task",
            "gas_used": 21000,
            "gas_price": 20000000000
        }
    }
)
```

### 访问日志

访问日志由中间件自动记录，包含：
- 请求方法和路径
- 查询参数
- 客户端 IP
- 用户 ID（如果已认证）
- 响应状态码
- 响应时间

## 日志文件

### 文件位置

所有日志文件存储在 `logs/` 目录：

```
logs/
├── nautilus.json.log          # 主应用日志（JSON格式）
├── nautilus.log               # 主应用日志（文本格式）
├── nautilus.error.json.log    # 错误日志（JSON格式）
├── access.json.log            # 访问日志（JSON格式）
└── blockchain.json.log        # 区块链日志（JSON格式）
```

### 日志轮转

- **最大文件大小**: 50MB
- **保留文件数**: 10 个
- **命名格式**: `filename.log.1`, `filename.log.2`, ...

## 日志聚合

### 使用 Promtail + Loki

1. **配置 Promtail**:
   ```bash
   # 编辑配置文件
   vim config/logging/promtail.yml

   # 设置 Loki 地址
   clients:
     - url: http://loki:3100/loki/api/v1/push
   ```

2. **启动 Promtail**:
   ```bash
   promtail -config.file=config/logging/promtail.yml
   ```

3. **在 Grafana 中查询**:
   ```logql
   # 查询所有错误日志
   {job="nautilus-backend", log_type="error"}

   # 查询特定端点的访问日志
   {job="nautilus-backend", log_type="access"} |= "/api/tasks"

   # 查询慢请求
   {job="nautilus-backend", log_type="access"} | json | duration_ms > 1000
   ```

### 使用 Filebeat + Elasticsearch

1. **配置 Filebeat**:
   ```bash
   # 编辑配置文件
   vim config/logging/filebeat.yml

   # 设置 Elasticsearch 地址
   output.elasticsearch:
     hosts: ["elasticsearch:9200"]
   ```

2. **启动 Filebeat**:
   ```bash
   filebeat -c config/logging/filebeat.yml
   ```

3. **在 Kibana 中查询**:
   ```
   # 查询错误日志
   log_type: "error" AND level: "ERROR"

   # 查询慢请求
   log_type: "access" AND http.duration_ms: >1000

   # 查询特定用户的操作
   user_id: "user_123"
   ```

## 日志分析

### 使用分析脚本

```bash
# 分析所有类型
python scripts/analyze_logs.py

# 只分析错误
python scripts/analyze_logs.py --analysis-type errors

# 只分析性能
python scripts/analyze_logs.py --analysis-type performance

# 只检测异常
python scripts/analyze_logs.py --analysis-type anomalies

# 指定时间范围（小时）
python scripts/analyze_logs.py --time-range 48

# 输出 JSON 报告
python scripts/analyze_logs.py --output report.json
```

### 分析报告内容

1. **错误分析**:
   - 错误总数
   - 错误类型分布
   - 错误来源（文件和行号）
   - 错误时间线

2. **性能分析**:
   - 请求总数
   - 端点性能统计（平均、P95、P99）
   - HTTP 状态码分布
   - 慢请求列表

3. **异常检测**:
   - 高错误率时段
   - 重复错误
   - 异常日志量

## 日志查询示例

### 使用 jq 查询 JSON 日志

```bash
# 查询所有错误
cat logs/nautilus.json.log | jq 'select(.level == "ERROR")'

# 查询特定时间范围
cat logs/nautilus.json.log | jq 'select(.timestamp >= "2026-02-27T10:00:00Z")'

# 查询慢请求
cat logs/access.json.log | jq 'select(.http.duration_ms > 1000)'

# 统计状态码分布
cat logs/access.json.log | jq -r '.http.status_code' | sort | uniq -c

# 查询特定用户的操作
cat logs/nautilus.json.log | jq 'select(.user_id == "user_123")'

# 查询区块链交易
cat logs/blockchain.json.log | jq 'select(.blockchain.tx_hash != null)'
```

### 使用 grep 查询文本日志

```bash
# 查询错误
grep "ERROR" logs/nautilus.log

# 查询特定端点
grep "/api/tasks" logs/nautilus.log

# 查询特定请求ID
grep "a1b2c3d4-e5f6-7890" logs/nautilus.log

# 统计错误数量
grep -c "ERROR" logs/nautilus.log
```

## 故障排查

### 常见问题

#### 1. 找不到特定请求的日志

**解决方案**:
```bash
# 使用请求ID查询
grep "request_id_here" logs/*.log

# 或使用 jq
cat logs/nautilus.json.log | jq 'select(.request_id == "request_id_here")'
```

#### 2. 查找导致错误的原因

**步骤**:
1. 在错误日志中找到错误信息
2. 使用 request_id 查找完整的请求链路
3. 检查相关的访问日志和应用日志
4. 查看异常堆栈信息

```bash
# 1. 找到错误
cat logs/nautilus.error.json.log | jq 'select(.message | contains("Database"))'

# 2. 提取 request_id
REQUEST_ID=$(cat logs/nautilus.error.json.log | jq -r 'select(.message | contains("Database")) | .request_id' | head -1)

# 3. 查找完整链路
cat logs/*.json.log | jq "select(.request_id == \"$REQUEST_ID\")"
```

#### 3. 分析性能问题

**步骤**:
1. 运行性能分析脚本
2. 识别慢端点
3. 查看慢请求的详细日志
4. 检查数据库查询和外部调用

```bash
# 运行性能分析
python scripts/analyze_logs.py --analysis-type performance

# 查找特定端点的慢请求
cat logs/access.json.log | jq 'select(.http.path == "/api/tasks" and .http.duration_ms > 1000)'
```

#### 4. 检测异常行为

**步骤**:
1. 运行异常检测脚本
2. 查看高错误率时段
3. 分析重复错误
4. 检查日志量异常

```bash
# 运行异常检测
python scripts/analyze_logs.py --analysis-type anomalies

# 查看特定时段的日志
cat logs/nautilus.json.log | jq 'select(.timestamp >= "2026-02-27T10:00:00Z" and .timestamp <= "2026-02-27T11:00:00Z")'
```

### 调试技巧

1. **启用 DEBUG 级别日志**:
   ```bash
   export LOG_LEVEL=debug
   python main.py
   ```

2. **实时监控日志**:
   ```bash
   # 监控所有日志
   tail -f logs/nautilus.log

   # 只监控错误
   tail -f logs/nautilus.log | grep ERROR

   # 监控 JSON 日志并格式化
   tail -f logs/nautilus.json.log | jq '.'
   ```

3. **日志关联分析**:
   - 使用 request_id 关联同一请求的所有日志
   - 使用 user_id 追踪用户行为
   - 使用 tx_hash 追踪区块链交易

## 最佳实践

### 日志记录原则

1. **记录关键操作**:
   - 用户认证和授权
   - 数据创建、更新、删除
   - 区块链交易
   - 外部 API 调用

2. **记录错误和异常**:
   - 使用 `logger.exception()` 记录完整堆栈
   - 包含足够的上下文信息
   - 避免记录敏感信息

3. **记录性能指标**:
   - 慢查询
   - 长时间运行的操作
   - 资源使用情况

4. **避免过度日志**:
   - 不要在循环中记录日志
   - 使用适当的日志级别
   - 避免记录大量数据

### 安全考虑

1. **不要记录敏感信息**:
   - 密码
   - API 密钥
   - 私钥
   - 个人身份信息（PII）

2. **日志访问控制**:
   - 限制日志文件访问权限
   - 使用安全的日志传输（TLS）
   - 定期审计日志访问

3. **日志保留策略**:
   - 定义日志保留期限
   - 定期清理旧日志
   - 遵守数据保护法规

## 监控和告警

### 推荐的告警规则

1. **错误率告警**:
   - 错误率 > 5%
   - 持续时间 > 5 分钟

2. **性能告警**:
   - P95 响应时间 > 1 秒
   - P99 响应时间 > 2 秒

3. **可用性告警**:
   - 5xx 错误率 > 1%
   - 健康检查失败

4. **异常告警**:
   - 日志量突增（> 3x 平均值）
   - 重复错误（> 10 次/分钟）

### Grafana 仪表板

推荐的监控面板：
- 请求速率和响应时间
- 错误率趋势
- 端点性能分布
- 状态码分布
- 慢请求列表
- 区块链交易监控

## 参考资源

- [Structured Logging Best Practices](https://www.structlog.org/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Elasticsearch Logging](https://www.elastic.co/guide/en/elasticsearch/reference/current/logging.html)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)

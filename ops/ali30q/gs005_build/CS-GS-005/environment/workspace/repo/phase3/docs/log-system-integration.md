# Nautilus 日志系统集成说明

## 概述

Nautilus 项目现在拥有两套互补的日志系统：

1. **应用层日志系统** (Python logging) - 已存在
2. **日志聚合系统** (Loki + Promtail) - 新部署

## 系统架构

```
应用程序 (FastAPI)
    ↓
Python logging_config.py
    ↓
日志文件输出
    ├── /var/log/nautilus-backend.log
    ├── /var/log/nautilus-backend-error.log
    ├── logs/nautilus_app.log
    ├── logs/nautilus_error.log
    └── logs/blockchain.log
    ↓
Promtail (日志采集)
    ↓
Loki (日志聚合)
    ↓
Grafana (可视化)
```

## 两套系统的关系

### 应用层日志系统 (logging_config.py)
**功能**:
- 生成结构化日志
- 日志轮转和归档
- 彩色控制台输出
- 区块链专用日志
- 按日期归档

**日志文件**:
- `logs/nautilus_app.log` - 主应用日志
- `logs/nautilus_error.log` - 错误日志
- `logs/blockchain.log` - 区块链操作日志
- `logs/nautilus_YYYYMMDD.log` - 按日期归档

### 日志聚合系统 (Loki + Promtail)
**功能**:
- 集中式日志收集
- 强大的查询和过滤
- 实时日志流
- 告警和监控
- 长期存储和分析

**采集源**:
- `/var/log/nautilus-backend.log`
- `/var/log/nautilus-backend-error.log`
- `/var/log/nginx/access.log`
- `/var/log/nginx/error.log`

## 集成建议

### 1. 统一日志输出路径

修改 `backend/logging_config.py` 使其输出到 `/var/log/` 目录，以便 Promtail 采集：

```python
# 在 logging_config.py 中添加
import os

# 根据环境选择日志目录
if os.getenv("ENVIRONMENT") == "production":
    LOG_DIR = Path("/var/log")
else:
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)
```

### 2. 更新 Promtail 配置

添加更多日志源到 Promtail 配置：

```yaml
scrape_configs:
  # 现有配置...

  - job_name: nautilus-app
    static_configs:
      - targets:
          - localhost
        labels:
          job: nautilus-app
          type: application
          __path__: /var/log/nautilus_app.log

  - job_name: nautilus-blockchain
    static_configs:
      - targets:
          - localhost
        labels:
          job: nautilus-blockchain
          type: blockchain
          __path__: /var/log/blockchain.log
```

### 3. 日志格式标准化

确保日志格式便于解析和查询：

```python
# 推荐的日志格式
detailed_format = (
    '%(asctime)s - %(name)s - %(levelname)s - '
    '[%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
)

# 对于结构化日志，考虑使用 JSON 格式
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if hasattr(record, 'tx_hash'):
            log_data['tx_hash'] = record.tx_hash
        return json.dumps(log_data)
```

### 4. 环境变量配置

在 `.env` 文件中添加日志配置：

```bash
# 日志配置
LOG_LEVEL=info
LOG_DIR=/var/log
ENABLE_CONSOLE_LOG=true
ENABLE_FILE_LOG=true
ENABLE_BLOCKCHAIN_LOG=true

# Loki 配置
LOKI_URL=http://localhost:3100
LOKI_ENABLED=true
```

## 使用场景

### 场景 1: 开发调试
**使用**: 应用层日志系统
- 彩色控制台输出
- 详细的堆栈跟踪
- 本地日志文件

```bash
# 启动应用并查看日志
python main.py

# 查看特定日志文件
tail -f logs/nautilus_app.log
```

### 场景 2: 生产监控
**使用**: 日志聚合系统
- Grafana 仪表盘实时监控
- 告警通知
- 历史日志查询

```bash
# 查询最近的错误
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend-error"}' \
  --data-urlencode 'limit=10'
```

### 场景 3: 问题排查
**使用**: 两者结合
- Loki 快速定位问题时间点
- 本地日志文件查看详细上下文

```bash
# 1. 在 Grafana 中找到错误发生时间
# 2. 查看本地详细日志
grep "2026-03-02 14:30" logs/nautilus_app.log
```

### 场景 4: 区块链交易追踪
**使用**: 区块链专用日志 + Loki 查询

```bash
# 查询特定交易
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-blockchain"} |= "0x1234567890abcdef"'
```

## 最佳实践

### 1. 日志级别使用
```python
logger.debug("详细的调试信息")           # 开发环境
logger.info("正常的业务流程")            # 生产环境
logger.warning("潜在问题，但不影响运行")  # 需要关注
logger.error("错误，但程序可以继续")      # 需要处理
logger.critical("严重错误，程序可能崩溃") # 立即处理
```

### 2. 结构化日志
```python
# 使用 extra 参数添加上下文
logger.info(
    "Task published successfully",
    extra={
        'task_id': task_id,
        'tx_hash': tx_hash,
        'reward': reward
    }
)
```

### 3. 区块链操作日志
```python
from logging_config import log_blockchain_transaction, get_blockchain_logger

blockchain_logger = get_blockchain_logger()

# 记录交易
log_blockchain_transaction(
    blockchain_logger,
    operation="publish_task",
    tx_hash=tx_hash,
    status="success",
    details={'task_id': task_id}
)
```

### 4. 性能监控
```python
import time

start_time = time.time()
# 执行操作
duration = time.time() - start_time

logger.info(
    f"Operation completed in {duration:.2f}s",
    extra={'operation': 'publish_task', 'duration': duration}
)
```

## 监控指标

### 应用层指标
- 日志文件大小和轮转
- 日志写入性能
- 磁盘空间使用

### 聚合层指标
- 日志摄入速率
- 查询响应时间
- 存储使用情况
- 告警触发次数

## 维护任务

### 每日
```bash
# 检查日志文件大小
du -sh logs/ /var/log/nautilus*

# 检查 Loki 服务
docker ps | grep loki

# 查看最新错误
tail -50 logs/nautilus_error.log
```

### 每周
```bash
# 清理旧日志（超过30天）
find logs/ -name "nautilus_*.log" -mtime +30 -delete

# 备份重要日志
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# 检查 Loki 存储
du -sh /home/ubuntu/loki-data
```

## 故障排查

### 问题 1: 日志文件过大
```bash
# 检查日志文件大小
ls -lh logs/

# 手动轮转
mv logs/nautilus_app.log logs/nautilus_app.log.1
touch logs/nautilus_app.log

# 重启应用
systemctl restart nautilus-backend
```

### 问题 2: Promtail 无法读取日志
```bash
# 检查文件权限
ls -la /var/log/nautilus*

# 修复权限
chmod 644 /var/log/nautilus*.log

# 重启 Promtail
docker restart promtail
```

### 问题 3: 日志丢失
```bash
# 检查日志配置
python -c "from logging_config import setup_logging; setup_logging()"

# 检查 Promtail 采集状态
docker logs promtail | grep "Adding target"

# 检查 Loki 摄入
curl -s http://localhost:3100/loki/api/v1/label/job/values
```

## 下一步优化

### 短期 (1-2 周)
1. ✅ 统一日志输出路径到 `/var/log/`
2. ✅ 更新 Promtail 配置采集所有日志
3. ⏳ 实施 JSON 格式日志
4. ⏳ 添加请求 ID 追踪

### 中期 (1-2 月)
1. ⏳ 实施分布式追踪 (OpenTelemetry)
2. ⏳ 添加性能指标日志
3. ⏳ 实施日志采样策略
4. ⏳ 集成 APM 工具

### 长期 (3-6 月)
1. ⏳ 机器学习异常检测
2. ⏳ 自动化日志分析
3. ⏳ 日志数据湖建设
4. ⏳ 实时日志流处理

## 总结

Nautilus 现在拥有完整的日志解决方案：
- ✅ 应用层日志系统提供详细的本地日志
- ✅ 日志聚合系统提供集中式监控和分析
- ✅ 两套系统互补，覆盖开发和生产场景
- ✅ 完整的文档和工具支持

建议根据实际需求逐步集成和优化两套系统。

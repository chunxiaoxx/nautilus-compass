# 日志系统完善 - 快速参考

## 📁 创建的文件

### 核心组件
- ✅ `utils/logging_config.py` - 结构化日志配置（JSON格式）
- ✅ `middleware/logging_middleware.py` - 日志中间件（请求/响应/错误）
- ✅ `middleware/__init__.py` - 中间件模块初始化

### 日志聚合配置
- ✅ `config/logging/promtail.yml` - Promtail配置（Loki）
- ✅ `config/logging/filebeat.yml` - Filebeat配置（Elasticsearch）
- ✅ `config/logging/grafana-datasources.yml` - Grafana数据源
- ✅ `config/logging/docker-compose.logging.yml` - Docker Compose栈
- ✅ `config/logging/.env.logging.example` - 环境变量示例
- ✅ `config/logging/README.md` - 配置文档

### 分析和工具
- ✅ `scripts/analyze_logs.py` - 日志分析脚本（错误/性能/异常）
- ✅ `scripts/logging_examples.py` - 使用示例（10个场景）
- ✅ `scripts/start_logging_stack.py` - 启动日志聚合栈
- ✅ `scripts/test_logging_system.sh` - 测试脚本
- ✅ `scripts/verify_logging_system.py` - 验证脚本

### 测试和文档
- ✅ `tests/test_logging_system.py` - 单元测试
- ✅ `LOGGING_GUIDE.md` - 完整日志指南（400+行）
- ✅ `LOGGING_SYSTEM_SUMMARY.md` - 系统总结
- ✅ `LOGGING_QUICK_REFERENCE.md` - 快速参考（本文件）

### 集成修改
- ✅ `main.py` - 已集成日志中间件

## 🚀 快速开始

### 1. 验证安装
```bash
python scripts/verify_logging_system.py
```

### 2. 查看示例
```bash
python scripts/logging_examples.py
```

### 3. 启动日志聚合（可选）
```bash
python scripts/start_logging_stack.py start
```

### 4. 分析日志
```bash
python scripts/analyze_logs.py --time-range 24
```

## 💡 使用示例

### 基础日志
```python
from utils.logging_config import get_logger

logger = get_logger(__name__)
logger.info("操作成功")
logger.error("操作失败")
```

### 结构化日志
```python
from utils.logging_config import StructuredLogger, get_logger

structured_logger = StructuredLogger(get_logger(__name__))
structured_logger.info(
    "用户登录",
    user_id="user123",
    ip_address="192.168.1.100"
)
```

### 区块链日志
```python
from utils.logging_config import get_blockchain_logger

blockchain_logger = get_blockchain_logger()
blockchain_logger.info(
    "交易提交",
    extra={
        "extra_fields": {
            "tx_hash": "0x123...",
            "gas_used": 21000
        }
    }
)
```

## 📊 日志文件

```
logs/
├── nautilus.json.log          # 主日志（JSON）
├── nautilus.log               # 主日志（文本）
├── nautilus.error.json.log    # 错误日志
├── access.json.log            # 访问日志
└── blockchain.json.log        # 区块链日志
```

## 🔍 日志查询

### 使用 jq
```bash
# 查询错误
cat logs/nautilus.json.log | jq 'select(.level == "ERROR")'

# 查询慢请求
cat logs/access.json.log | jq 'select(.http.duration_ms > 1000)'
```

### 使用 Grafana (LogQL)
```logql
# 错误日志
{job="nautilus-backend", log_type="error"}

# 慢请求
{job="nautilus-backend", log_type="access"} | json | duration_ms > 1000
```

## 🎯 关键特性

- ✅ **JSON格式**: 结构化日志，便于解析
- ✅ **自动上下文**: request_id、user_id自动注入
- ✅ **性能监控**: 慢请求自动检测
- ✅ **错误追踪**: 完整异常堆栈
- ✅ **日志轮转**: 自动管理文件大小
- ✅ **多种输出**: 控制台、文件、聚合系统
- ✅ **易于查询**: 支持多种查询工具
- ✅ **完整文档**: 详细使用指南

## 📝 环境变量

```bash
LOG_LEVEL=info                    # 日志级别
SERVICE_NAME=nautilus-backend     # 服务名称
ENVIRONMENT=production            # 环境
LOG_CONSOLE=false                 # 控制台输出
SLOW_REQUEST_THRESHOLD=1.0        # 慢请求阈值（秒）
```

## 🔧 故障排查

### 日志文件未创建
```bash
mkdir -p logs
chmod 755 logs
```

### 查看最新日志
```bash
tail -f logs/nautilus.log
```

### 验证JSON格式
```bash
cat logs/nautilus.json.log | python -m json.tool
```

## 📚 文档

- **完整指南**: `LOGGING_GUIDE.md`
- **系统总结**: `LOGGING_SYSTEM_SUMMARY.md`
- **配置文档**: `config/logging/README.md`

## ✅ 验证清单

- [x] 结构化日志配置
- [x] 日志中间件
- [x] 日志聚合配置（Promtail + Filebeat）
- [x] 日志分析脚本
- [x] 使用示例
- [x] 单元测试
- [x] 完整文档
- [x] 主应用集成

## 🎉 完成状态

所有任务已完成！日志系统已成功完善，可以投入使用。

运行 `python scripts/verify_logging_system.py` 进行最终验证。

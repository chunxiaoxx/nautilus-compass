"""
压力测试配置文件

用于配置压力测试的各项参数

版本: 1.0.0
创建时间: 2026-02-25
"""

# 服务器配置
SERVER_URL = "http://localhost:8001"
SERVER_HEALTH_ENDPOINT = "/health"

# 测试超时配置（秒）
TEST_TIMEOUT = 60
CONNECTION_TIMEOUT = 30
REGISTRATION_TIMEOUT = 30

# 并发连接测试配置
CONCURRENT_TEST = {
    "num_agents": 100,              # 并发智能体数量
    "connection_timeout": 30,       # 连接超时
    "stability_wait": 5,            # 稳定性验证等待时间
    "success_rate_threshold": 0.95, # 成功率阈值
    "avg_time_threshold": 2.0,      # 平均连接时间阈值（秒）
    "max_time_threshold": 5.0,      # 最大连接时间阈值（秒）
}

# 消息吞吐量测试配置
THROUGHPUT_TEST = {
    "num_senders": 10,              # 发送者数量
    "num_receivers": 10,            # 接收者数量
    "messages_per_sender": 100,     # 每个发送者的消息数
    "send_interval": 0.01,          # 发送间隔（秒）
    "receive_wait": 5,              # 接收等待时间（秒）
    "success_rate_threshold": 0.95, # 消息接收率阈值
    "throughput_threshold": 100,    # 吞吐量阈值（条/秒）
    "avg_latency_threshold": 1.0,   # 平均延迟阈值（秒）
    "p95_latency_threshold": 2.0,   # P95延迟阈值（秒）
}

# 长时间运行测试配置
LONG_RUNNING_TEST = {
    "duration": 300,                # 测试时长（秒），300=5分钟，3600=1小时
    "num_agents": 20,               # 智能体数量
    "message_interval": 5,          # 消息发送间隔（秒）
    "status_interval": 30,          # 状态输出间隔（秒）
    "connection_threshold": 0.9,    # 连接稳定率阈值
    "message_threshold": 0.9,       # 消息接收率阈值
}

# 内存泄漏检测配置
MEMORY_TEST = {
    "num_iterations": 50,           # 迭代次数
    "agents_per_iteration": 10,     # 每次迭代的智能体数
    "messages_per_iteration": 10,   # 每次迭代的消息数
    "cleanup_wait": 0.1,            # 清理等待时间（秒）
    "memory_growth_threshold": 50,  # 内存增长阈值（%）
}

# 测试级别配置
TEST_LEVELS = {
    "quick": {
        "concurrent_agents": 50,
        "throughput_messages": 500,
        "longrun_duration": 300,     # 5分钟
        "memory_iterations": 30,
    },
    "standard": {
        "concurrent_agents": 100,
        "throughput_messages": 1000,
        "longrun_duration": 1800,    # 30分钟
        "memory_iterations": 50,
    },
    "full": {
        "concurrent_agents": 200,
        "throughput_messages": 2000,
        "longrun_duration": 3600,    # 1小时
        "memory_iterations": 100,
    }
}

# 性能基准
PERFORMANCE_BENCHMARKS = {
    "connection": {
        "avg_time": 2.0,            # 平均连接时间（秒）
        "max_time": 5.0,            # 最大连接时间（秒）
        "success_rate": 0.95,       # 成功率
    },
    "throughput": {
        "target": 1000,             # 目标吞吐量（条/秒）
        "minimum": 100,             # 最低吞吐量（条/秒）
    },
    "latency": {
        "avg": 1.0,                 # 平均延迟（秒）
        "p95": 2.0,                 # P95延迟（秒）
        "p99": 3.0,                 # P99延迟（秒）
    },
    "stability": {
        "connection_rate": 0.9,     # 连接保持率
        "message_rate": 0.9,        # 消息接收率
    },
    "memory": {
        "growth_limit": 50,         # 内存增长限制（%）
    }
}

# 日志配置
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "stress_test.log",
}

# 报告配置
REPORT = {
    "output_file": "PERFORMANCE_REPORT.md",
    "include_charts": False,        # 是否包含图表（需要matplotlib）
    "save_raw_data": True,          # 是否保存原始数据
    "raw_data_file": "stress_test_data.json",
}

# 重试配置
RETRY = {
    "max_attempts": 3,              # 最大重试次数
    "delay": 1.0,                   # 重试延迟（秒）
    "backoff": 2.0,                 # 退避系数
}

# 资源限制
RESOURCE_LIMITS = {
    "max_memory_mb": 4096,          # 最大内存使用（MB）
    "max_cpu_percent": 90,          # 最大CPU使用率（%）
    "max_connections": 1000,        # 最大连接数
}

# 告警阈值
ALERT_THRESHOLDS = {
    "error_rate": 0.05,             # 错误率阈值（5%）
    "timeout_rate": 0.05,           # 超时率阈值（5%）
    "memory_growth": 0.5,           # 内存增长阈值（50%）
    "cpu_usage": 0.9,               # CPU使用率阈值（90%）
}

# 环境变量覆盖
import os

# 允许通过环境变量覆盖配置
if os.getenv("NEXUS_SERVER_URL"):
    SERVER_URL = os.getenv("NEXUS_SERVER_URL")

if os.getenv("TEST_TIMEOUT"):
    TEST_TIMEOUT = int(os.getenv("TEST_TIMEOUT"))

if os.getenv("CONCURRENT_AGENTS"):
    CONCURRENT_TEST["num_agents"] = int(os.getenv("CONCURRENT_AGENTS"))

if os.getenv("MESSAGE_COUNT"):
    THROUGHPUT_TEST["messages_per_sender"] = int(os.getenv("MESSAGE_COUNT")) // THROUGHPUT_TEST["num_senders"]

if os.getenv("LONGRUN_DURATION"):
    LONG_RUNNING_TEST["duration"] = int(os.getenv("LONGRUN_DURATION"))

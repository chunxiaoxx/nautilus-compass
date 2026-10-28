from datetime import timezone
"""
结构化日志配置模块
提供JSON格式的结构化日志，便于日志聚合和分析
"""
import logging
import logging.handlers
import json
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import socket


# 日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志级别映射
LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}


class StructuredFormatter(logging.Formatter):
    """结构化JSON日志格式化器"""

    def __init__(self, service_name: str = "nautilus-backend", environment: str = "development"):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.hostname = socket.gethostname()

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        # 基础日志结构
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            "hostname": self.hostname,
            "process": {
                "pid": record.process,
                "name": record.processName
            },
            "thread": {
                "id": record.thread,
                "name": record.threadName
            },
            "source": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": traceback.format_exception(*record.exc_info)
            }

        # 添加自定义字段
        if hasattr(record, "extra_fields"):
            log_data["extra"] = record.extra_fields

        # 添加请求相关信息
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, "method"):
            log_data["http"] = {
                "method": record.method,
                "path": getattr(record, "path", None),
                "status_code": getattr(record, "status_code", None),
                "duration_ms": getattr(record, "duration_ms", None)
            }

        # 添加区块链相关信息
        if hasattr(record, "tx_hash"):
            log_data["blockchain"] = {
                "tx_hash": record.tx_hash,
                "operation": getattr(record, "operation", None),
                "gas_used": getattr(record, "gas_used", None),
                "gas_price": getattr(record, "gas_price", None)
            }

        # 添加性能指标
        if hasattr(record, "metrics"):
            log_data["metrics"] = record.metrics

        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台日志格式化器（人类可读）"""

    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        result = super().format(record)
        record.levelname = levelname

        return result


class ContextFilter(logging.Filter):
    """上下文过滤器，添加请求上下文信息"""

    def filter(self, record: logging.LogRecord) -> bool:
        """添加上下文信息到日志记录"""
        # 从上下文变量获取请求信息（如果存在）
        from contextvars import ContextVar

        # 这些变量应该在中间件中设置
        request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
        user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

        request_id = request_id_var.get()
        user_id = user_id_var.get()

        if request_id:
            record.request_id = request_id
        if user_id:
            record.user_id = user_id

        return True


def setup_structured_logging(
    log_level: str = "info",
    service_name: str = "nautilus-backend",
    environment: str = "development",
    enable_console: bool = True,
    enable_json_file: bool = True,
    enable_text_file: bool = True,
    max_bytes: int = 50 * 1024 * 1024,  # 50MB
    backup_count: int = 10
) -> None:
    """
    配置结构化日志系统

    Args:
        log_level: 日志级别
        service_name: 服务名称
        environment: 环境名称
        enable_console: 启用控制台输出（彩色，人类可读）
        enable_json_file: 启用JSON格式文件输出（用于日志聚合）
        enable_text_file: 启用文本格式文件输出（人类可读）
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
    """
    level = LOG_LEVEL_MAP.get(log_level.lower(), logging.INFO)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    # 添加上下文过滤器
    context_filter = ContextFilter()
    root_logger.addFilter(context_filter)

    # 1. 控制台处理器（彩色，人类可读）
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ColoredConsoleFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 2. JSON格式日志文件（用于日志聚合系统）
    if enable_json_file:
        json_log_file = LOG_DIR / "nautilus.json.log"
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(level)
        json_formatter = StructuredFormatter(service_name, environment)
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)

    # 3. 文本格式日志文件（人类可读）
    if enable_text_file:
        text_log_file = LOG_DIR / "nautilus.log"
        text_handler = logging.handlers.RotatingFileHandler(
            text_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        text_handler.setLevel(level)
        text_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        text_handler.setFormatter(text_formatter)
        root_logger.addHandler(text_handler)

    # 4. 错误日志文件（JSON格式）
    if enable_json_file:
        error_json_file = LOG_DIR / "nautilus.error.json.log"
        error_json_handler = logging.handlers.RotatingFileHandler(
            error_json_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_json_handler.setLevel(logging.ERROR)
        error_json_handler.setFormatter(StructuredFormatter(service_name, environment))
        root_logger.addHandler(error_json_handler)

    # 5. 访问日志（单独的JSON文件）
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False

    if enable_json_file:
        access_log_file = LOG_DIR / "access.json.log"
        access_handler = logging.handlers.RotatingFileHandler(
            access_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(StructuredFormatter(service_name, environment))
        access_logger.addHandler(access_handler)

    # 6. 区块链日志（单独的JSON文件）
    blockchain_logger = logging.getLogger('blockchain')
    blockchain_logger.setLevel(logging.DEBUG)
    blockchain_logger.propagate = True

    if enable_json_file:
        blockchain_log_file = LOG_DIR / "blockchain.json.log"
        blockchain_handler = logging.handlers.RotatingFileHandler(
            blockchain_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        blockchain_handler.setLevel(logging.DEBUG)
        blockchain_handler.setFormatter(StructuredFormatter(service_name, environment))
        blockchain_logger.addHandler(blockchain_handler)

    # 配置第三方库的日志级别
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('web3').setLevel(logging.INFO)

    # 记录日志系统启动信息
    root_logger.info(
        "Structured logging system initialized",
        extra={
            "extra_fields": {
                "log_level": log_level.upper(),
                "log_directory": str(LOG_DIR.absolute()),
                "console_output": enable_console,
                "json_file_output": enable_json_file,
                "text_file_output": enable_text_file
            }
        }
    )


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


def get_access_logger() -> logging.Logger:
    """获取访问日志记录器"""
    return logging.getLogger('access')


def get_blockchain_logger() -> logging.Logger:
    """获取区块链日志记录器"""
    return logging.getLogger('blockchain')


class StructuredLogger:
    """结构化日志记录器包装类"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """内部日志记录方法"""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)


def init_logging_from_env() -> None:
    """从环境变量初始化日志系统"""
    log_level = os.getenv("LOG_LEVEL", "info")
    environment = os.getenv("ENVIRONMENT", "development")
    service_name = os.getenv("SERVICE_NAME", "nautilus-backend")

    # 生产环境配置
    if environment == "production":
        enable_console = os.getenv("LOG_CONSOLE", "false").lower() == "true"
        enable_json_file = True
        enable_text_file = False
    else:
        enable_console = True
        enable_json_file = True
        enable_text_file = True

    setup_structured_logging(
        log_level=log_level,
        service_name=service_name,
        environment=environment,
        enable_console=enable_console,
        enable_json_file=enable_json_file,
        enable_text_file=enable_text_file
    )


# 测试代码
if __name__ == "__main__":
    setup_structured_logging(
        log_level="debug",
        service_name="nautilus-backend",
        environment="development"
    )

    logger = get_logger(__name__)
    structured_logger = StructuredLogger(logger)

    # 测试基础日志
    structured_logger.info("Application started")
    structured_logger.debug("Debug information", user_id="user123", action="login")
    structured_logger.warning("High memory usage", memory_percent=85.5)
    structured_logger.error("Database connection failed", error_code="DB001", retry_count=3)

    # 测试异常日志
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.exception("An error occurred")

    print(f"\nLog files created in: {LOG_DIR.absolute()}")

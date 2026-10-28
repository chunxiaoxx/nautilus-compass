"""
日志配置模块
提供完整的日志配置，包括文件轮转、格式化和区块链操作专用日志
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


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


class BlockchainLogFilter(logging.Filter):
    """区块链操作日志过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        """只允许区块链相关的日志通过"""
        return hasattr(record, 'blockchain') or 'blockchain' in record.name.lower()


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（用于控制台输出）"""

    # ANSI颜色代码
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
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # 格式化消息
        result = super().format(record)

        # 重置levelname（避免影响其他handler）
        record.levelname = levelname

        return result


def setup_logging(
    log_level: str = "info",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_blockchain_log: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    配置应用程序日志系统

    Args:
        log_level: 日志级别 (debug, info, warning, error, critical)
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        enable_blockchain_log: 是否启用区块链专用日志
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
    """
    # 获取日志级别
    level = LOG_LEVEL_MAP.get(log_level.lower(), logging.INFO)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 日志格式
    detailed_format = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
    )
    simple_format = '%(asctime)s - %(levelname)s - %(message)s'

    # 1. 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 2. 主应用日志文件（轮转）
    if enable_file:
        app_log_file = LOG_DIR / "nautilus_app.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(level)
        app_formatter = logging.Formatter(detailed_format, datefmt='%Y-%m-%d %H:%M:%S')
        app_handler.setFormatter(app_formatter)
        root_logger.addHandler(app_handler)

    # 3. 错误日志文件（只记录ERROR及以上级别）
    if enable_file:
        error_log_file = LOG_DIR / "nautilus_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(detailed_format, datefmt='%Y-%m-%d %H:%M:%S')
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

    # 4. 区块链操作专用日志
    if enable_blockchain_log and enable_file:
        blockchain_logger = logging.getLogger('blockchain')
        blockchain_logger.setLevel(logging.DEBUG)
        blockchain_logger.propagate = True  # 同时传播到根日志记录器

        blockchain_log_file = LOG_DIR / "blockchain.log"
        blockchain_handler = logging.handlers.RotatingFileHandler(
            blockchain_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        blockchain_handler.setLevel(logging.DEBUG)
        blockchain_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        blockchain_handler.setFormatter(blockchain_formatter)
        blockchain_logger.addHandler(blockchain_handler)

    # 5. 按日期归档的日志（每天一个文件）
    if enable_file:
        daily_log_file = LOG_DIR / f"nautilus_{datetime.now().strftime('%Y%m%d')}.log"
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 保留30天
            encoding='utf-8'
        )
        daily_handler.setLevel(level)
        daily_formatter = logging.Formatter(simple_format, datefmt='%Y-%m-%d %H:%M:%S')
        daily_handler.setFormatter(daily_formatter)
        daily_handler.suffix = "%Y%m%d"
        root_logger.addHandler(daily_handler)

    # 配置第三方库的日志级别
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('web3').setLevel(logging.INFO)

    # 记录日志系统启动信息
    root_logger.info("=" * 60)
    root_logger.info("Nautilus Phase 3 Backend - Logging System Initialized")
    root_logger.info(f"Log Level: {log_level.upper()}")
    root_logger.info(f"Log Directory: {LOG_DIR.absolute()}")
    root_logger.info(f"Console Output: {enable_console}")
    root_logger.info(f"File Output: {enable_file}")
    root_logger.info(f"Blockchain Log: {enable_blockchain_log}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称（通常使用 __name__）

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


def get_blockchain_logger() -> logging.Logger:
    """
    获取区块链专用日志记录器

    Returns:
        区块链日志记录器实例
    """
    return logging.getLogger('blockchain')


def log_blockchain_transaction(
    logger: logging.Logger,
    operation: str,
    tx_hash: Optional[str] = None,
    status: str = "pending",
    details: Optional[dict] = None
) -> None:
    """
    记录区块链交易日志

    Args:
        logger: 日志记录器
        operation: 操作类型（如 publish_task, accept_task 等）
        tx_hash: 交易哈希
        status: 交易状态（pending, success, failed）
        details: 额外的详细信息
    """
    log_message = f"[BLOCKCHAIN] Operation: {operation} | Status: {status}"

    if tx_hash:
        log_message += f" | TxHash: {tx_hash}"

    if details:
        log_message += f" | Details: {details}"

    if status == "failed":
        logger.error(log_message)
    elif status == "success":
        logger.info(log_message)
    else:
        logger.debug(log_message)


def log_gas_usage(
    logger: logging.Logger,
    operation: str,
    gas_used: int,
    gas_price: int,
    gas_cost: int
) -> None:
    """
    记录Gas使用情况

    Args:
        logger: 日志记录器
        operation: 操作类型
        gas_used: 使用的Gas数量
        gas_price: Gas价格（Wei）
        gas_cost: 总Gas费用（Wei）
    """
    gas_cost_eth = gas_cost / 1e18
    log_message = (
        f"[GAS] Operation: {operation} | "
        f"Gas Used: {gas_used} | "
        f"Gas Price: {gas_price} Wei | "
        f"Total Cost: {gas_cost} Wei ({gas_cost_eth:.6f} ETH)"
    )
    logger.info(log_message)


# 从环境变量读取配置并初始化日志系统
def init_logging_from_env() -> None:
    """从环境变量初始化日志系统"""
    log_level = os.getenv("LOG_LEVEL", "info")
    environment = os.getenv("ENVIRONMENT", "development")

    # 生产环境默认不输出到控制台
    enable_console = environment != "production"

    setup_logging(
        log_level=log_level,
        enable_console=enable_console,
        enable_file=True,
        enable_blockchain_log=True
    )


# 如果直接运行此模块，进行测试
if __name__ == "__main__":
    # 测试日志配置
    setup_logging(log_level="debug", enable_console=True, enable_file=True)

    logger = get_logger(__name__)
    blockchain_logger = get_blockchain_logger()

    # 测试不同级别的日志
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # 测试区块链日志
    log_blockchain_transaction(
        blockchain_logger,
        operation="publish_task",
        tx_hash="0x1234567890abcdef",
        status="success",
        details={"task_id": "task_001", "reward": 1000000000000000000}
    )

    log_gas_usage(
        blockchain_logger,
        operation="accept_task",
        gas_used=21000,
        gas_price=20000000000,
        gas_cost=420000000000000
    )

    print(f"\nLog files created in: {LOG_DIR.absolute()}")

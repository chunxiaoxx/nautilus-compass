"""
Utils Module - 工具函数
"""
import logging
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """配置日志"""
    log_format = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers
    )


def format_node_id(node_id: str, length: int = 8) -> str:
    """格式化节点 ID"""
    return node_id[:length]


def calculate_penalty(delay_minutes: float) -> float:
    """计算延迟惩罚"""
    if delay_minutes <= 5:
        return 0.0
    return min(0.2 * (delay_minutes // 5), 0.8)


__all__ = ["setup_logging", "format_node_id", "calculate_penalty"]

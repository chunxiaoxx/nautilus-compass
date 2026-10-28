"""
Nautilus Core - AI Agent Mining Pool System
============================================
基于 V7.1 的模块化重构版本

核心模块:
- pool: 矿池管理器
- body: 执行工作器
- mind: 决策引擎
- pow: POW 系统
- economy: MEME 币经济
"""

__version__ = "1.0.0"
__author__ = "Nautilus Team"

from nautilus.pool import Pool
from nautilus.body import Body
from nautilus.mind import Mind
from nautilus.models import Task, Node, POW, Difficulty

__all__ = [
    "Pool",
    "Body",
    "Mind",
    "Task",
    "Node",
    "POW",
    "Difficulty"
]
